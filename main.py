import base64, requests, socket, time, os, json, re
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def test_tcp_connectivity(node):
    """单节点测速函数，供多线程调用"""
    try:
        host, port = node['addr'], node['port']
        target_ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.5)
        start = time.time()
        result = sock.connect_ex((target_ip, int(port)))
        delay = int((time.time() - start) * 1000)
        sock.close()
        if result == 0:
            node['delay'] = delay
            return node
    except: pass
    return None

def process():
    all_raw_nodes = []
    if not os.path.exists('urls.txt'): return
    with open('urls.txt', 'r', encoding='utf-8') as f:
        sub_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    
    seen_ips = set()

    # 1. 抓取与初步解析
    for link in sub_links:
        try:
            targets = [link]
            if "raw.githubusercontent.com" in link:
                targets.append(link.replace("raw.githubusercontent.com", "raw.kkgithub.com"))
                targets.append(f"https://ghproxy.net/{link}")

            response_text = ""
            for t in targets:
                try:
                    r = requests.get(t, headers={'User-Agent': 'v2rayN/6.23'}, timeout=12)
                    if r.status_code == 200:
                        response_text = r.text; break
                except: continue
            
            if not response_text: continue

            content = safe_base64_decode(response_text) if "://" not in response_text[:20] else response_text
            for line in content.splitlines():
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
                        is_hy2 = line.startswith(('hy', 'hysteria2'))
                    except: continue
                
                if addr and port and addr not in seen_ips:
                    seen_ips.add(addr)
                    all_raw_nodes.append({'raw': line, 'addr': addr, 'port': port, 'name': raw_name, 'is_hy2': is_hy2})
        except: continue

    # 2. 多线程测速 (10线程)
    print(f"🚀 开始并发测速，共 {len(all_raw_nodes)} 个待测节点...")
    valid_nodes = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(test_tcp_connectivity, n) for n in all_raw_nodes]
        for future in as_completed(futures):
            res = future.result()
            if res:
                valid_nodes.append(res)
                print(f" ✅ {res['name'][:15]}... 通了!")

    # 3. 排序与重命名写入
    valid_nodes.sort(key=lambda x: x['delay'])
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 聚合 | 有效: {len(valid_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        region_counter = {}
        for n in valid_nodes[:50]:
            reg = get_region_name(n['name'])
            display_reg = f"⚡{reg}" if n['is_hy2'] else reg
            region_counter[display_reg] = region_counter.get(display_reg, 0) + 1
            new_name = f"[{display_reg}狗熊] {region_counter[display_reg]:02d}"
            
            raw = n['raw']
            if raw.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(raw[8:])); cfg['ps'] = new_name
                    raw = "vmess://" + base64.b64encode(json.dumps(cfg).encode('utf-8')).decode('utf-8')
                except: pass
            else:
                raw = f"{raw.split('#')[0]}#{new_name}"
            f.write(f"{raw}\n")
    print(f"🎉 任务完成，筛选出 {len(valid_nodes)} 个狗熊节点！")

if __name__ == "__main__":
    process()
