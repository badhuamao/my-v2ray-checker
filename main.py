import requests, re, time, html, json

# 国家代码转国旗图标的映射表
FLAG_MAP = {
    'CN': '🇨🇳', 'HK': '🇭🇰', 'TW': '🇹🇼', 'JP': '🇯🇵', 'US': '🇺🇸', 
    'SG': '🇸🇬', 'KR': '🇰🇷', 'GB': '🇬🇧', 'FR': '🇫🇷', 'DE': '🇩🇪',
    'NL': '🇳🇱', 'RU': '🇷🇺', 'CA': '🇨🇦', 'AU': '🇦🇺', 'IN': '🇮🇳'
}

def get_country_info(link):
    """简单识别国家代码，默认给个地球仪"""
    # 尝试从域名后缀或常见的节点命名中提取（这是一种快速但不完全精准的方法）
    low = link.lower()
    for code, emoji in FLAG_MAP.items():
        if f".{code.lower()}" in low or f"-{code.lower()}" in low:
            return emoji
    return '🌐' # 默认图标

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def get_node_key(link):
    return link.split('#')[0].split('?')[0]

def process():
    print(f"🐻 狗熊工厂 9.0 | 国际化精选模式启动...")
    raw_pool = []
    
    # 1. 抓取 urls.txt
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
                except: continue
    except:
        print("⚠️ 找不到 urls.txt")
        return

    # 2. 深度去重
    seen_keys = set()
    unique_nodes = []
    for node in raw_pool:
        key = get_node_key(node)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_nodes.append(node)
    
    # 3. 协议排序并取前 30
    grpc_nodes = [n for n in unique_nodes if 'grpc' in n.lower()]
    others = [n for n in unique_nodes if n not in grpc_nodes]
    final_output = (grpc_nodes + others)[:30]

    # 4. 写入文件，更换图标并增加国家标识
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·国际30强 | 数量: {len(final_output)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_output):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            
            # 识别协议标签
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            # 获取国家图标
            flag = get_country_info(clean_link)
            
            # 最终格式：链接#国旗 狗熊_协议_编号
            f.write(f"{clean_link}#{flag} 🐻_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务完成！30 个带国旗的狗熊节点已就位。")

if __name__ == "__main__":
    process()
