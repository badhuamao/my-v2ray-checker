import requests, re, time

# 定义一个保底源，防止 urls.txt 为空
DEFAULT_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def extract_specific_nodes(text):
    # 只提取 HY2, TUIC 和 HTTP
    pattern = r'(?:hysteria2|hy2|tuic|http)://[a-zA-Z0-9$_.+!*\'(),;?:@&=%/-]+(?:#[^\s"\'<>]+)?'
    return re.findall(pattern, text)

def process():
    print(f"🐻 狗熊工厂 4.6 | 正在从 urls.txt 读取原材料...")
    
    # 1. 加载源列表
    target_urls = []
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            target_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print("⚠️ urls.txt 不存在，将使用保底成品源")
        target_urls = [DEFAULT_SOURCE]

    if not target_urls:
        target_urls = [DEFAULT_SOURCE]

    # 2. 批量吞噬节点
    all_raw_nodes = []
    for url in target_urls:
        try:
            print(f"正在读取: {url[:30]}...")
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                found = extract_specific_nodes(r.text)
                all_raw_nodes.extend(found)
        except Exception as e:
            print(f"❌ 读取失败 {url}: {e}")

    # 3. 去重与精炼
    unique_nodes = list(dict.fromkeys(all_raw_nodes))
    print(f"✅ 过滤完成，共获得 {len(unique_nodes)} 个 HY2/TUIC/HTTP 节点")

    # 4. 写入成品
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·全能订阅 | 来源数: {len(target_urls)} | 数量: {len(unique_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(unique_nodes):
            clean_link = node.split('#')[0]
            p_type = "HY2" if "hy" in clean_link else ("TUIC" if "tuic" in clean_link else "HTTP")
            f.write(f"{clean_link}#🐻{p_type}_{i+1:02d}\n")
    
    print("🎉 生产完毕！")

if __name__ == "__main__":
    process()
