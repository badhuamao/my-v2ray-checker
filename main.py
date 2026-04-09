import requests, re, time, html, socket

# 目标源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def is_port_open(link):
    """
    轻量级探测：检查服务器端口是否开放
    """
    try:
        # 提取域名和端口
        host_port = re.search(r'@(?P<host>[^:]+):(?P<port>\d+)', link)
        if not host_port: return True # 无法解析的默认通过，由客户端处理
        
        host = host_port.group('host')
        port = int(host_port.group('port'))
        
        with socket.create_connection((host, port), timeout=2):
            return True
    except:
        return False

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    # 扩大侦察范围：捕获所有链接，后面再精准过滤
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        link = match.group('link')
        low_link = link.lower()
        
        # 核心过滤逻辑：
        # 1. 明确是 hy2, tuic, http 协议的
        # 2. 或者链接参数里包含 grpc 关键字的 (这解决了 gRPC 节点消失的问题)
        if any(p in low_link for p in ['hy2', 'hysteria2', 'tuic', 'http://']) or 'grpc' in low_link:
            return link
    return None

def process():
    print(f"🐻 狗熊工厂 6.0 | 正在执行精兵策略 (上限30个)...")
    raw_nodes = []
    
    # 1. 抓取 (私人源+高手源)
    sources = [GOLDEN_SOURCE]
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            my_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            sources = my_urls + sources
    except: pass

    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.split('\n'):
                    link = clean_node_link(line)
                    if link: raw_nodes.append(link)
        except: continue

    # 2. 去重
    unique_nodes = list(dict.fromkeys(raw_nodes))
    print(f"📡 初步提取到 {len(unique_nodes)} 个潜在节点，开始存活探测...")

    # 3. 核心升级：存活过滤 + 数量封顶
    final_nodes = []
    for node in unique_nodes:
        if len(final_nodes) >= 30: break # 达到30个直接收工
        
        if is_port_open(node):
            final_nodes.append(node)
            print(f"✅ 节点存活: {len(final_nodes)}/30")
        else:
            print(f"❌ 剔除死节点")

    # 4. 写入结果
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·精兵版 | 仅存活节点 | 封顶: 30 | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_nodes):
            clean_link = node.split('#')[0]
            low_link = clean_link.lower()
            
            # 协议打标
            if "grpc" in low_link: p_tag = "GRPC"
            elif "hy2" in low_link or "hysteria2" in low_link: p_tag = "HY2"
            elif "tuic" in low_link: p_tag = "TUIC"
            else: p_tag = "HTTP"
            
            f.write(f"{clean_link}#🚀狗熊_{p_tag}_{i+1:02d}\n")
    
    print(f"🎉 生产完毕！今日精选 {len(final_nodes)} 个高可用节点。")

if __name__ == "__main__":
    process()
