import requests, re, time, html

# 高手精品源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    深度清洗逻辑：修复转义并识别包含 gRPC 传输参数的链接
    """
    text = html.unescape(raw_str)
    # 捕获主流协议链接
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        link = match.group('link')
        low_link = link.lower()
        # 只要包含我们要的协议关键字或传输参数
        if any(p in low_link for p in ['hy2', 'hysteria2', 'tuic', 'http://', 'grpc']):
            return link
    return None

def process():
    print(f"🐻 狗熊工厂 6.2 | 均衡配额模式...")
    # 建立协议池，防止某一种协议霸占所有名额
    pool = {'GRPC': [], 'HY2': [], 'TUIC': [], 'HTTP': []}
    
    # 获取所有源
    urls = [GOLDEN_SOURCE]
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            my_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            urls = my_urls + urls # 私人源排在前面
    except: pass

    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                for line in r.text.split('\n'):
                    link = clean_node_link(line)
                    if link:
                        low = link.lower()
                        # 精准归类
                        if 'grpc' in low: pool['GRPC'].append(link)
                        elif 'hy2' in low or 'hysteria2' in low: pool['HY2'].append(link)
                        elif 'tuic' in low: pool['TUIC'].append(link)
                        elif 'http://' in low: pool['HTTP'].append(link)
        except: continue

    # 组装最终名单：每种协议各取前 10 个精华
    final_nodes = []
    for p_type in ['GRPC', 'HY2', 'TUIC', 'HTTP']:
        unique_type_nodes = list(dict.fromkeys(pool[p_type]))
        # 每一类只取前 10 个，保证总数在 40 以内，且协议平衡
        final_nodes.extend(unique_type_nodes[:10])

    # 写入结果
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·均衡配额版 | 数量: {len(final_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_nodes):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            # 自动打标
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 生产完毕！今日配额已填满，共 {len(final_nodes)} 个节点。")

if __name__ == "__main__":
    process()
