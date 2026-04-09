import requests, re, time, html

# 高手精品源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    # 捕获所有符合协议特征的链接
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        link = match.group('link')
        low = link.lower()
        # 严格筛选你要的这几类协议
        if any(p in low for p in ['hy2', 'hysteria2', 'tuic', 'http://', 'grpc']):
            return link
    return None

def process():
    print(f"🐻 狗熊工厂 · 巅峰版 | 正在为你精选 4K 级别节点...")
    final_nodes = []
    
    # 1. 组合源 (私人优先 + 储备补充)
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
                    if link: final_nodes.append(link)
        except: continue

    # 2. 深度去重
    unique_nodes = list(dict.fromkeys(final_nodes))
    
    # 3. 协议分层（确保 gRPC/HTTP 哪怕只有一个也能排在最前面让你看到）
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    http_nodes = [n for n in unique_nodes if 'http://' in n.lower()]
    modern_nodes = [n for n in unique_nodes if n not in grpc_nodes and n not in http_nodes]

    # 4. 重新组合：gRPC + HTTP + 其它精华
    # 总数维持在 150 个左右，这是你本地 11 个绿灯的基数保障
    priority_list = grpc_nodes + http_nodes + modern_nodes
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·4K优选版 | 基数: {len(priority_list[:150])} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(priority_list[:150]):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            # 协议类型精准标注
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务圆满完成！今日 150 个海选节点已就位，请享用 4K！")

if __name__ == "__main__":
    process()
