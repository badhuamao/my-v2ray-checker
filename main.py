import base64
import requests
import socket
import time
import os
import json
import re
from urllib.parse import urlparse, unquote

# 地区映射表：用于规范化显示名称
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC', '台北'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡', '獅城'],
    '美国': ['US', 'USA', '美国', 'UNITED STATES', 'LA', 'NY'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL'],
    '英国': ['UK', 'UNITED KINGDOM', '英国', 'LONDON'],
    '德国': ['DE', 'GERMANY', '德国', 'FRANKFURT'],
    '法国': ['FR', 'FRANCE', '法国', 'PARIS'],
    '加拿大': ['CA', 'CANADA', '加拿大'],
}

def get_region_name(raw_name):
    """根据原始名称识别地区并规范化"""
    upper_name = raw_name.upper()
    for region, keywords in REGION_MAP.items():
        if any(k.upper() in upper_name for k in keywords):
            return region
    return "地区未知"

def safe_base64_decode(data):
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def get_sub_links():
    file_path = 'urls.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

def test_tcp_connectivity(host, port, timeout=3):
    try:
        target_ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        result = sock.connect_ex((target_ip, int(port)))
        delay = int((time.time() - start) * 1000)
        sock.close()
        return delay if result == 0 else None
    except:
        return None

def process():
    nodes_pool = []
    sub_links = get_sub_links()
    seen_ips = set()

    for link in sub_links:
        try:
            print(f"📡 正在拉取: {link[:50]}...")
            headers = {'User-Agent': 'v2rayN/6.23'}
            response = requests.get(link, headers=headers, timeout=15).text
            content = safe_base64_decode(response) if "://" not in response[:20] else response
            lines = content.splitlines()

            for line in lines:
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, raw_name = "", 0, ""
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, raw_name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    try:
                        p = urlparse(line)
                        addr, port, raw_name = p.hostname, p.port, unquote(p.fragment)
                    except: continue
                
                if addr and port:
                    if addr in seen_ips: continue
                    
                    delay = test_tcp_connectivity(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        # 规范化名称：例如 "[香港] 01"
                        region = get_region_name(raw_name)
                        nodes_pool.append({
                            "raw": line, 
                            "delay": delay, 
                            "region": region,
                            "raw_name": raw_name
                        })
                        print(f"✅ 可用: [{delay}ms] {region} <- {raw_name[:20]}")
                        
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

    # 按延迟排序
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 写入结果，修改节点显示的备注名
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 自动筛选 | 总数: {len(nodes_pool)} | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 记录每个地区出现的次数，用于编号
        region_counter = {}
        
        for n in nodes_pool[:50]:
            reg = n['region']
            region_counter[reg] = region_counter.get(reg, 0) + 1
            new_name = f"[{reg}] {region_counter[reg]:02d}"
            
            # 这里的逻辑是：如果是 vmess，需要修改 JSON 里的 ps 字段再编码
            # 如果是其他协议，直接替换 # 后面的部分
            final_link = n['raw']
            if final_link.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(final_link[8:]))
                    cfg['ps'] = new_name
                    new_json = json.dumps(cfg).encode('utf-8')
                    final_link = "vmess://" + base64.b64encode(new_json).decode('utf-8')
                except: pass
            else:
                # 处理 ss/ssr/vless/trojan 的 # 备注部分
                if "#" in final_link:
                    base_url = final_link.split('#')[0]
                    final_link = f"{base_url}#{new_name}"
                else:
                    final_link = f"{final_link}#{new_name}"
            
            f.write(f"{final_link}\n")
    
    print(f"\n🎉 整理完成！节点已统一命名并保存。")

if __name__ == "__main__":
    process()
