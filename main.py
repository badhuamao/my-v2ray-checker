import base64
import requests
import socket
import time
import os
import json
import re
from urllib.parse import urlparse, unquote

# 地区识别映射表
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG', '廣港', '深港'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA', '東京', '大阪'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC', '台北', '新北'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡', '獅城'],
    '美国': ['US', 'USA', '美国', 'UNITED STATES', 'LA', 'NY', '圣何塞', '西雅图'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL', '首尔'],
    '德国': ['DE', 'GERMANY', '德国', 'FRANKFURT'],
    '英国': ['UK', 'UNITED KINGDOM', '英国', 'LONDON'],
}

def safe_base64_decode(data):
    """鲁棒性强的 Base64 解码，兼容多种订阅格式"""
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        # 移除所有换行符和空格
        data = "".join(data.split())
        # 自动补全填充符
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return ""

def get_region_name(raw_name):
    """根据节点备注识别地区"""
    upper_name = raw_name.upper()
    for region, keywords in REGION_MAP.items():
        if any(k.upper() in upper_name for k in keywords):
            return region
    return "其他"

def test_connectivity(host, port, timeout=2.5):
    """双轮 TCP 握手测试，确保节点真实在线"""
    try:
        target_ip = socket.gethostbyname(host)
        for _ in range(2):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.time()
            result = sock.connect_ex((target_ip, int(port)))
            sock.close()
            if result != 0:
                return None
            time.sleep(0.05)
        return int((time.time() - start) * 1000)
    except:
        return None

def process():
    nodes_pool = []
    seen_ips = set()
    file_path = 'urls.txt'
    
    if not os.path.exists(file_path):
        print("❌ 错误: 找不到 urls.txt 文件")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        sub_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    for link in sub_links:
        try:
            print(f"📡 正在拉取源: {link[:50]}...")
            headers = {'User-Agent': 'v2rayN/6.23'}
            response = requests.get(link, headers=headers, timeout=15).text
            
            # 自动判断是否需要 Base64 解码
            if "://" not in response[:20]:
                content = safe_base64_decode(response)
            else:
                content = response

            lines = content.splitlines()
            print(f"📄 解析到 {len(lines)} 行原始数据")

            for line in lines:
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, raw_name, is_hy2 = "", 0, "", False
                
                # 协议解析
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, raw_name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                elif line.startswith(('hysteria2://', 'hy2://')):
                    try:
                        p = urlparse(line)
                        addr, port, raw_name = p.hostname, p.port, unquote(p.fragment)
                        is_hy2 = True
                    except: continue
                else:
                    try:
                        p = urlparse(line)
                        addr, port, raw_name = p.hostname, p.port, unquote(p.fragment)
                    except: continue
                
                # 过滤并测试
                if addr and port and addr not in seen_ips:
                    delay = test_connectivity(addr, port)
                    if delay and delay < 2500:
                        seen_ips.add(addr)
                        region = get_region_name(raw_name)
                        # 为 Hy2 节点增加特殊标识
                        display_region = f"⚡{region}" if is_hy2 else region
                        nodes_pool.append({
                            "raw": line, 
                            "delay": delay, 
                            "region": display_region,
                            "is_hy2": is_hy2
                        })
                        print(f"✅ 有效: [{delay}ms] {display_region}")
                        
        except Exception as e:
            print(f"⚠️ 跳过源 {link[:30]}: {e}")

    # 按延迟排序
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 写入结果并重命名
    region_counter = {}
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 聚合订阅 | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')} | 总数: {len(nodes_pool)}\n")
        
        for n in nodes_pool[:50]:
            reg = n['region']
            region_counter[reg] = region_counter.get(reg, 0) + 1
            new_name = f"{reg} {region_counter[reg]:02d}"
            
            final_link = n['raw']
            if final_link.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(final_link[8:]))
                    cfg['ps'] = new_name
                    final_link = "vmess://" + base64.b64encode(json.dumps(cfg).encode('utf-8')).decode('utf-8')
                except: pass
            else:
                # 处理带 # 的备注部分
                base_part = final_link.split('#')[0]
                final_link = f"{base_part}#{new_name}"
            
            f.write(f"{final_link}\n")
    
    print(f"\n🎉 处理完成！已保存 {len(nodes_pool[:50])} 个最速节点。")

if __name__ == "__main__":
    process()
