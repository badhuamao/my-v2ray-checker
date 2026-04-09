import requests, re, time, html

# 核心源保持不变
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    最原始的提取逻辑：不进行任何身份判定，只要链接完整就抓
    """
    text = html.unescape(raw_str)
    # 扩大匹配口径，确保包含所有参数（解决 gRPC 消失问题）
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link')
    return None

def process():
    print(f"🐻 狗熊工厂 · 满血版回滚 | 正在恢复原始抓取规模...")
    all_nodes = []
    
    # 1. 抓取所有源
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
                    if link: all_nodes.append(link)
        except: continue

    # 2. 仅进行基础行去重，不进行地址身份判定
    unique_nodes = list(dict.fromkeys(all_nodes))
    
    # 3. 协议简单分类（确保 gRPC 不排在最后）
    grpc_part = [n for n in unique_nodes if 'grpc' in n.lower()]
    other_part = [n for n in unique_nodes if n not in grpc_part]
    
    # 组合结果，放宽数量到 200 个，给你本地留足筛选空间
    final_list = grpc_part + other_part
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·回归巅峰版 | 数量: {len(final_list[:200])} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_list[:200]):
            # 移除旧备注，统一打标
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 回滚完成！200 个原始节点已准备就绪。")

if __name__ == "__main__":
    process()
