import requests, re, time, html

# 回归最强储备源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    极致提取：修复 HTML 转义，只要是目标协议或带 grpc 参数的，通通带走
    """
    text = html.unescape(raw_str)
    # 扩大匹配口径，确保包含参数的复杂链接不被切断
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        link = match.group('link')
        low = link.lower()
        # 严格执行你的协议指令
        if any(p in low for p in ['hy2', 'hysteria2', 'tuic', 'http://', 'grpc']):
            return link
    return None

def process():
    print(f"🐻 狗熊工厂·回归版 | 正在恢复满血生产...")
    final_nodes = []
    
    # 获取源 (合并私人和高手库)
    urls = [GOLDEN_SOURCE]
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')] + urls
    except: pass

    for url in urls:
        try:
            print(f"📡 抓取源: {url[:40]}...")
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                # 暴力扫描每一行
                lines = r.text.split('\n')
                for line in lines:
                    link = clean_node_link(line)
                    if link: final_nodes.append(link)
        except: continue

    # 去重
    unique_nodes = list(dict.fromkeys(final_nodes))
    
    # 写入结果：不再设 30 个的死限制，让你有更多选择
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·满血版 | 数量: {len(unique_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(unique_nodes[:150]): # 扩容到 150 个，提高出绿灯的概率
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            # 协议识别打标
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务完成！共捞出 {len(unique_nodes)} 个节点，快去客户端测速！")

if __name__ == "__main__":
    process()
