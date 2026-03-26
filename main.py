import base64
import requests
import socket
import time
import os
import json
import re
from urllib.parse import urlparse, unquote

# 地区映射表
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡'],
    '美国': ['US', 'USA', '美国', 'STATES'],
    '韩国': ['KR', 'KOREA', '韩国'],
}

def get_region_name(raw_name):
    upper_name = raw_name.upper()
    for region, keywords in REGION_MAP.items():
        if any(k.upper() in upper_name for k in keywords):
            return region
    return "其他"

def safe_base64_decode(data):
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

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
    except: return None

def process():
    nodes_pool = []
    if not os.path.exists('urls.txt'): 
        print("❌ 未找到 urls.txt")
        return
        
    with open('urls.txt', 'r', encoding='utf-8') as f:
        sub_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    
    seen_ips = set()

    for link in sub_links:
        try:
            # --- 自动救活 404 逻辑 ---
            targets = [link]
            if "raw.githubusercontent.com" in link:
                # 尝试两个不同的 GitHub 镜像源
                targets.append(link.replace("raw.githubusercontent.com", "raw.kkgithub.com"))
                targets.append(f"https://ghproxy.net/{link}")

            response_text = ""
            for t in targets:
                print(f"📡 尝试抓取: {t[:60]}...")
                try:
                    r = requests.get(t, headers={'User-Agent': 'v2rayN/6.23'}, timeout=12)
                    if r.status_code == 200:
                        response_text = r.text
                        print(f"✅ 成功! (源: {t[:25]}...)")
                        break
                    else:
                        print(f"⚠️ 返回状态码: {r.status_code}")
                except: continue
            
            if not response_text:
                print(f"❌ 该订阅源所有镜像均失效，跳过。")
                continue

            content = safe_base64_decode(response_text) if "://" not in response_text[:20] else response_text
            lines = content.splitlines()

            for line in lines:
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, raw_name, is_hy2 = "", 0, "", False
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, raw_name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    try:
                        p = urlparse(line)
                        addr, port = p.hostname, p.port
                        raw_name = unquote(p.fragment) if p.fragment else "Node"
                        if line.startswith(('hy', 'hysteria2')): is_hy2 = True
                    except: continue
                
                if addr and port and addr not in seen_ips:
                    delay = test_tcp_connectivity(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        region = get_region_name(raw_name)
                        # 加上 Hy2 标识
                        display_reg = f"⚡{region}" if is_hy2 else region
                        nodes_pool.append({"raw": line, "delay": delay, "region": display_reg})
                        print(f"   [+] {display_reg} ({delay}ms)")
        except Exception as e:
            print(f"❌ 运行异常: {e}")

    # 按延迟排序并重命名
    nodes_pool.sort(key=lambda x: x['delay'])
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 聚合列表 | 有效数: {len(nodes_pool)} | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        region_counter = {}
        for n in nodes_pool[:50]:
            reg = n['region']
            region_counter[reg] = region_counter.get(reg, 0) + 1
            # 核心修改：地区名 + 狗熊 + 编号
            new_name = f"[{reg}狗熊] {region_counter[reg]:02d}"
            
            final_link = n['raw']
            if final_link.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(final_link[8:]))
                    cfg['ps'] = new_name
                    final_link = "vmess://" + base64.b64encode(json.dumps(cfg).encode('utf-8')).decode('utf-8')
                except: pass
            else:
                base_url = final_link.split('#')[0]
                final_link = f"{base_url}#{new_name}"
            f.write(f"{final_link}\n")
    
    print(f"\n🎉 整理完成！抓到 {len(nodes_pool)} 个有效节点，已保存至 top_asia_nodes.txt")

if __name__ == "__main__":
    process()
