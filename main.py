import requests, re, time, html

def clean_node_link(raw_str):
    """
    最强提取命令：
    1. 修复 HTML 转义
    2. 支持 HY2 端口范围 (如 41000-42000)
    3. 支持 gRPC 复杂参数
    """
    text = html.unescape(raw_str)
    # 采用非贪婪匹配，保证链接完整性
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def get_node_key(link):
    """提取唯一特征：协议+域名+端口，彻底干掉重复节点"""
    return link.split('#')[0].split('?')[0]

def process():
    print(f"🐻 狗熊工厂 8.1 | 纯净私人领地 | 目标 30 强")
    raw_pool = []
    
    # 仅从你的私人订阅源获取数据
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            for url in f:
                url = url.strip()
                if not url or url.startswith('#'): continue
                try:
                    # 适当延长超时，确保你的矿山能挖透
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        for line in r.text.split('\n'):
                            link = clean_node_link(line)
                            if link: raw_pool.append(link)
                except: continue
    except FileNotFoundError:
        print("⚠️ 找不到 urls.txt！")
        return

    # 1. 深度去重：不管备注怎么变，同一个服务器只留一个
    seen_keys = set()
    unique_nodes = []
    for node in raw_pool:
        key = get_node_key(node)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_nodes.append(node)
    
    print(f"📡 私人源总量: {len(raw_pool)} | 唯一节点: {len(unique_nodes)}")

    # 2. 协议优先级：让 gRPC 排在最前面，其他紧随其后
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    others = [n for n in unique_nodes if n not in grpc_nodes]
    
    # 严格锁死 30 个名额，让你测速不费劲
    final_output = (grpc_nodes + others)[:30]

    # 3. 写入文件
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·私有精选 | 数量: {len(final_output)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_output):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            # 自动打标，方便你在客户端一眼认出
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务圆满完成！30 个精选名额已就位。")

if __name__ == "__main__":
    process()
