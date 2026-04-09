import requests, re, time, html

GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    最强提取命令：
    1. 修复 HTML 转义
    2. 允许端口号包含 '-' (针对 HY2 端口范围)
    3. 允许参数包含任何字符 (针对 gRPC)
    """
    text = html.unescape(raw_str)
    # 这里的正则不再限制端口必须是数字，允许 41000-42000 这种格式
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def process():
    print(f"🐻 狗熊工厂 · 暴力修复版 | 正在全力抢救 HY2/GRPC...")
    raw_nodes = []
    
    # 抓取源
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

    # 1. 基础去重（仅针对完全相同的行）
    unique_nodes = list(dict.fromkeys(raw_nodes))
    
    # 2. 协议优先级排序 (让 GRPC/HTTP 露脸)
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    http_nodes = [n for n in unique_nodes if 'http://' in n.lower()]
    other_nodes = [n for n in unique_nodes if n not in grpc_nodes and n not in http_nodes]
    
    final_list = grpc_nodes + http_nodes + other_nodes

    # 3. 写入结果 (给足 200 个，不准再少了！)
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·暴力修复版 | 数量: {len(final_list[:200])} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_list[:200]):
            # 这里的 split('#')[0] 也要小心，确保不破坏前面的参数
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 修复完成！200 个原始样本已就位。")

if __name__ == "__main__":
    process()
