import base64, requests, socket, time, os, json, re, zlib
from urllib.parse import urlparse, unquote

REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG', '廣港'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡'],
    '美国': ['US', 'USA', '美国', 'STATES', 'LA', 'NY'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL'],
}

def safe_decode(data):
    """多级解码尝试，兼容 Gzip 和 Base64"""
    if not data: return ""
    # 尝试处理可能的压缩数据
    try: data = zlib.decompress(data, 16+zlib.MAX_WBITS).decode('utf-8')
    except: pass
    
    # 尝试 Base64 解码
    try:
        clean_data = "".join(data.split())
        missing_padding = len(clean_data) % 4
        if missing_padding: clean_data += '=' * (4 - missing_padding)
        decoded = base64.b64decode(clean_data).decode('utf-8', errors='ignore')
        if "://" in decoded: return decoded
    except: pass
    return data

def test_conn(host, port):
    try:
        ip = socket.gethostbyname(host)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        start = time.time()
        res = s.connect_ex((ip, int(port)))
        s.close()
        return int((time.time() - start) * 1000) if res == 0 else None
    except: return None

def process():
    nodes_pool = []
    seen_ips = set()
    if not os.path.exists('urls.txt'): return
    
    with open('urls.txt', 'r', encoding='utf-8') as f:
        urls = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    for url in urls:
        try:
            print(f"📡 抓取: {url[:40]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Encoding': 'gzip, deflate'
            }
            resp = requests.get(url, headers=headers, timeout=15)
            raw_text = safe_decode(resp.content if isinstance(resp.content, bytes) else resp.text)
            
            # 使用正则抓取所有协议链接，防止行解析失败
            found = re.findall(r'(vmess|vless|ss|ssr|trojan|hysteria2|hy2)://[^\s\'"]+', raw_text)
            print(f"📊 发现 {len(found)} 个潜在节点")

            for link in found:
                # 补全协议头进行解析
                full_link = link if "://" in link else "" # 正则已带协议头
                addr, port, name, is_hy2 = "", 0, "未知", False
                
                if link.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_decode(link[8:]))
                        addr, port, name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    try:
                        p = urlparse(link)
                        addr, port, name = p.hostname, p.port, unquote(p.fragment) if p.fragment else "Node"
                        if link.startswith(('hy', 'hysteria2')): is_hy2 = True
                    except: continue
                
                if addr and port and addr not in seen_ips:
                    delay = test_conn(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        reg = "其他"
                        for r, keys in REGION_MAP.items():
                            if any(k in name.upper() for k in keys): reg = r; break
                        
                        tag = f"⚡{reg}" if is_hy2 else reg
                        nodes_pool.append({"raw": link, "delay": delay, "tag": tag})
                        print(f"✅ [{delay}ms] {tag}")
        except Exception as e:
            print(f"⚠️ 失败: {e}")

    nodes_pool.sort(key=lambda x: x['delay'])
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 纯净聚合 | 更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        cnt = {}
        for n in nodes_pool[:50]:
            tag = n['tag']
            cnt[tag] = cnt.get(tag, 0) + 1
            new_ps = f"{tag} {cnt[tag]:02d}"
            # 备注重写
            raw = n['raw']
            if raw.startswith('vmess://'):
                try:
                    c = json.loads(safe_decode(raw[8:]))
                    c['ps'] = new_ps
                    raw = "vmess://" + base64.b64encode(json.dumps(c).encode()).decode()
                except: pass
            else:
                raw = f"{raw.split('#')[0]}#{new_ps}"
            f.write(f"{raw}\n")
    print(f"🎉 完成！共筛选出 {len(nodes_pool[:50])} 个节点")

if __name__ == "__main__":
    process()
