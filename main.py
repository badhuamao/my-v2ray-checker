import requests, re, time, html

GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        link = match.group('link')
        low = link.lower()
        if any(p in low for p in ['hy2', 'hysteria2', 'tuic', 'http://', 'grpc']):
            return link
    return None

def get_node_identity(link):
    """
    提取节点的唯一身份：协议 + 域名/IP + 端口
    目的是过滤掉那些仅仅是备注不同的重复节点
    """
    # 移除链接末尾的备注部分 (#之后的内容)
    base_link = link.split('#')[0]
    # 提取协议和核心地址部分 (去掉参数，只看核心)
    # 例如: vless://uuid@host:port?query -> vless://uuid@host:port
    identity = base_link.split('?')[0] if '?' in base_link else base_link
    return identity

def process():
    print(f"🐻 狗熊工厂 · 深度去重版 | 正在清理重复节点...")
    raw_nodes = []
    
    urls = [GOLDEN_SOURCE]
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')] + urls
    except: pass

    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                for line in r.text.split('\n'):
                    link = clean_node_link(line)
                    if link: raw_nodes.append(link)
        except: continue

    # --- 核心去重逻辑升级 ---
    seen_identities = set()
    unique_nodes = []
    
    for node in raw_nodes:
        identity = get_node_identity(node)
        if identity not in seen_identities:
            seen_identities.add(identity)
            unique_nodes.append(node)
    
    print(f"📊 原始节点: {len(raw_nodes)} | 去重后: {len(unique_nodes)}")

    # 协议分层（gRPC/HTTP 优先）
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    http_nodes = [n for n in unique_nodes if 'http://' in n.lower()]
    other_nodes = [n for n in unique_nodes if n not in grpc_nodes and n not in http_nodes]

    priority_list = grpc_nodes + http_nodes + other_nodes
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        # 维持 150 个基数，保证 4K 优选节点的出现概率
        output_limit = 150
        f.write(f"# 狗熊·无重复版 | 有效总数: {len(priority_list[:output_limit])} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(priority_list[:output_limit]):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 深度去重完成！现在每个节点都是独一无二的。")

if __name__ == "__main__":
    process()
