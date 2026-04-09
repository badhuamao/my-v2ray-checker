import requests, re, time, html

GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def get_node_key(link):
    """提取节点的唯一身份，用于去重"""
    # 只要 协议+域名+端口 一样，就认为是同一个节点
    clean_part = link.split('#')[0].split('?')[0]
    return clean_part

def process():
    print(f"🐻 狗熊工厂 7.1 | 私人源优先模式启动...")
    
    # 分别存放私人节点和公共节点
    private_nodes = []
    public_nodes = []
    
    # 1. 首先抓取 urls.txt (你的私人地盘)
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            my_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            for url in my_urls:
                print(f"📥 正在抓取私人源: {url[:30]}...")
                try:
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        for line in r.text.split('\n'):
                            link = clean_node_link(line)
                            if link: private_nodes.append(link)
                except: continue
    except FileNotFoundError:
        print("⚠️ 未发现 urls.txt，跳过私人源。")

    # 2. 抓取高手源 (作为备用弹药库)
    try:
        r = requests.get(GOLDEN_SOURCE, timeout=20)
        if r.status_code == 200:
            for line in r.text.split('\n'):
                link = clean_node_link(line)
                if link: public_nodes.append(link)
    except:
        print("⚠️ 高手源抓取失败，仅使用私人源。")

    # 3. 智能去重逻辑 (私人源拥有绝对优先权)
    seen_keys = set()
    final_list = []

    # 先放私人节点
    for node in private_nodes:
        key = get_node_key(node)
        if key not in seen_keys:
            seen_keys.add(key)
            final_list.append(node)
    
    print(f"✅ 私人唯一节点: {len(final_list)} 个")

    # 再用公共节点填补空位，直到凑够 150 个
    for node in public_nodes:
        if len(final_list) >= 150: break
        key = get_node_key(node)
        if key not in seen_keys:
            seen_keys.add(key)
            final_list.append(node)

    # 4. 写入结果
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·私人优先版 | 私人: {len(private_nodes)} | 总数: {len(final_list)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_list):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 生产完毕！私人源已置顶，共导出 {len(final_list)} 个节点。")

if __name__ == "__main__":
    process()
