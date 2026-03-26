import base64, requests, socket, time, os, json, re
from urllib.parse import urlparse, unquote

# 地区识别字典
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG', '廣港', '深港'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA', '東京', '大阪'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC', '台北', '新北'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡', '獅城'],
    '美国': ['US', 'USA', '美国', 'UNITED STATES', 'LA', 'NY', '圣何塞'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL', '首尔'],
}

def safe_base64_decode(data):
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def get_region(name):
    for reg, keys in REGION_MAP.items():
        if any(k.upper() in name.upper() for k in keys): return reg
    return "其他"

def test_conn(host, port):
    """双轮测试提高准确度"""
    try:
        ip = socket.gethostbyname(host)
        for _ in range(2):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            start = time.time()
            if s.connect_ex((ip, int(port))) != 0: return None
            s.close()
        return int((time.time() - start) * 1000)
    except: return None

def process():
    nodes_pool = []
    seen_ips = set()
    if not os.path.exists('urls.txt'): return
    with open('urls.txt', 'r') as f:
        links = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    for link in links:
        try:
            print(f"📡 抓取: {link[:40]}...")
            res = requests.get(link, headers={'User-Agent':'v2rayN/6.23'}, timeout=10).text
            content = safe_base64_decode(res) if "://" not in res[:20] else res
            
            for line in content.splitlines():
                line = line.strip()
                if "://" not in line: continue
                addr, port, name, is_hy2 = "", 0, "", False
                
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    try:
                        p = urlparse(line)
                        addr, port, name = p.hostname, p.port, unquote(p.fragment)
                        if line.startswith(('hysteria2://', 'hy2://')): is_hy2 = True
                    except: continue
                
                if addr and port and addr not in seen_ips:
                    delay = test_conn(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        reg = get_region(name)
                        nodes_pool.append({"raw":line, "delay":delay, "reg":f"⚡{reg}" if is_hy2 else reg})
                        print(f"✅ {reg} [{delay}ms]")
        except: continue

    nodes_pool.sort(key=lambda x: x['delay'])
    reg_cnt = {}
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 聚合订阅 | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for n in nodes_pool[:50]:
            reg = n['reg']
            reg_cnt[reg] = reg_cnt.get(reg, 0) + 1
            new_ps = f"{reg} {reg_cnt[reg]:02d}"
            raw = n['raw']
            if raw.startswith('vmess://'):
                c = json.loads(safe_base64_decode(raw[8:]))
                c['ps'] = new_ps
                raw = "vmess://" + base64.b64encode(json.dumps(c).encode()).decode()
            else:
                raw = f"{raw.split('#')[0]}#{new_ps}"
            f.write(f"{raw}\n")

if __name__ == "__main__":
    process()
