import base64, requests, socket, time, os, json, re, subprocess
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def test_real_connectivity(node):
    """
    核心：使用真实 TCP 握手 + 美东 IP 权重
    (由于 Actions 环境限制，我们先用强化版 TCP 验证，并加入美东优先逻辑)
    """
    try:
        host, port = node['addr'], node['port']
        target_ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.5) # 超过2.5秒直接视为垃圾节点
        
        start = time.time()
        result = sock.connect_ex((target_ip, int(port)))
        delay = int((time.time() - start) * 1000)
        sock.close()

        if result == 0:
            # 💡 咱们的秘密武器：美东 IP 权重 (ClawCloud)
            if "47.253" in node['addr'] or "47.90" in node['addr']:
                delay = max(delay - 60, 10) # 给美东 IP 60ms 的“心理提速”，让它们排在前面
            
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

    # 1. 抓取解析
    for link in sub_links:
        try:
            r = requests.get(link, headers={'User-Agent': 'v2rayN/6.23'}, timeout=12)
            if r.status_code != 200: continue
            content = safe_base64_decode(r.text) if "://" not in r.text[:20] else r.text
            
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
                        is_hy2 = line.startswith(('hy', 'hysteria2', 'tuic'))
                    except: continue
                
                if addr and port and addr not in seen_ips:
                    seen_ips.add(addr)
                    all_raw_nodes.append({'raw': line, 'addr': addr, 'port': port, 'name': raw_name, 'is_hy2': is_hy2})
        except: continue

    # 2. 多线程精筛 (20线程)
    print(f"🚀 狗熊工厂正在精选节点（并发: 20）...")
    valid_nodes = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(test_real_connectivity, n) for n in all_raw_nodes]
        for future in as_completed(futures):
            res = future.result()
            if res: valid_nodes.append(res)

    # 3. 排序并只取前 35 个精华
    valid_nodes.sort(key=lambda x: x['delay'])
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊精选 | 有效: {len(valid_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        region_counter = {}
        for n in valid_nodes[:35]:
            reg = get_region_name(n['name'])
            # 标上咱们的专属记号
            display_reg = f"🚀{reg}" if n['is_hy2'] else reg
            region_counter[display_reg] = region_counter.get(display_reg, 0) + 1
            new_name = f"[{display_reg}狗熊] {region_counter[display_reg]:02d}_{n['delay']}ms"
            
            raw = n['raw']
            if raw.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(raw[8:])); cfg['ps'] = new_name
                    raw = "vmess://" + base64.b64encode(json.dumps(cfg).encode('utf-8')).decode('utf-8')
                except: pass
            else:
                raw = f"{raw.split('#')[0]}#{new_name}"
            f.write(f"{raw}\n")
    print(f"🎉 完成！已精选 {len(valid_nodes[:35])} 个最速节点。")

if __name__ == "__main__":
    process()
