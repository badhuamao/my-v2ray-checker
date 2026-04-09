import requests, re, time, html

# 目标协议扩展：HY2, TUIC, HTTP, gRPC
TARGET_PROTOCOLS = ['hy2', 'hysteria2', 'tuic', 'http://', 'grpc']
# 高手精品源 (Docker 测速成品)
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    深度清洗：支持解码 HTML 转义，并精准扣取包含 gRPC 在内的多种协议链接
    """
    # 1. 修复 HTML 转义（解决 &amp; 导致参数失效的问题）
    text = html.unescape(raw_str)
    # 2. 增强正则：匹配目标协议开头，直到遇到引号、空格或行尾
    pattern = r'(?P<link>(?:hy2|hysteria2|tuic|http|grpc)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link')
    return None

def process():
    print(f"🐻 狗熊工厂 5.0 | 目标：HY2/TUIC/HTTP/GRPC...")
    final_nodes = []
    
    # 1. 第一优先级：读取你的 urls.txt
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            my_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            for url in my_urls:
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        lines = r.text.split('\n')
                        for line in lines:
                            link = clean_node_link(line)
                            if link: final_nodes.append(link)
                except: continue
    except FileNotFoundError: pass

    # 2. 智能补足：如果私人源节点不够，调用高手库
    print(f"📡 正在从储备源搜索新增的 gRPC 及其他目标协议...")
    try:
        r = requests.get(GOLDEN_SOURCE, timeout=20)
        if r.status_code == 200:
            lines = r.text.split('\n')
            for line in lines:
                # 检查行内是否包含任何一个目标协议关键字
                if any(p in line.lower() for p in TARGET_PROTOCOLS):
                    link = clean_node_link(line)
                    if link: final_nodes.append(link)
    except Exception as e:
        print(f"❌ 储备源抓取异常: {e}")

    # 3. 去重与出厂包装
    final_nodes = list(dict.fromkeys(final_nodes))
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·全能订阅 | 包含: HY2/TUIC/HTTP/GRPC | 数量: {len(final_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_nodes[:100]):
            # 统一清理旧备注并打上狗熊标签
            clean_link = node.split('#')[0]
            # 识别协议类型用于命名
            low_link = clean_link.lower()
            p_tag = "GRPC" if "grpc" in low_link else ("HY2" if "hy" in low_link else ("TUIC" if "tuic" in low_link else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{p_tag}_{i+1:02d}\n")
    
    print(f"🎉 任务圆满完成！共获得 {len(final_nodes)} 个全能节点。")

if __name__ == "__main__":
    process()
