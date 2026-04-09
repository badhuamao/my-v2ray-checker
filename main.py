import requests, re, time, html

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    # 核心正则：支持 HY2 端口范围和 gRPC 复杂参数
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def get_node_key(link):
    """提取唯一特征防止重复"""
    return link.split('#')[0].split('?')[0]

def process():
    print(f"🐻 狗熊工厂 8.0 | 纯净私人模式 | 目标 30 强")
    raw_pool = []
    
    # 只抓取 urls.txt
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            for url in f:
                url = url.strip()
                if not url or url.startswith('#'): continue
                try:
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        for line in r.text.split('\n'):
                            link = clean_node_link(line)
                            if link: raw_pool.append(link)
                except Exception as e:
                    print(f"❌ 抓取失败 {url[:20]}: {e}")
    except FileNotFoundError:
        print("⚠️ 找不到 urls.txt，请检查文件是否存在！")
        return

    # 1. 深度去重
    seen_keys = set()
    unique_nodes = []
    for node in raw_pool:
        key = get_node_key(node)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_nodes.append(node)
    
    print(f"📡 私人矿山总量: {len(raw_pool)} | 唯一节点: {len(unique_nodes)}")

    # 2. 协议排序与严格限额 30 个
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    others = [n for n in unique_nodes if n not in grpc_nodes]
    
    # 组合并取前 30
    final_output = (grpc_nodes + others)[:30]

    # 3. 写入文件
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·私有30强 | 数量: {len(final_output)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_output):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务完成！已从你的私有源中选出 {len(final_output)} 个节点。")

if __name__ == "__main__":
    process()
