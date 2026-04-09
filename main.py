import requests, re, time, html

# 高手的精品源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    """
    深度清洗：去掉引号、修复转义字符
    """
    # 1. 修复 HTML 转义（比如 &amp; 变回 &）
    text = html.unescape(raw_str)
    # 2. 提取真正的链接部分（匹配到空格、引号或末尾为止）
    match = re.search(r'(?P<link>(?:hy2|hysteria2|tuic|http)://[^\s\'"]+)', text)
    if match:
        return match.group('link')
    return None

def process():
    print(f"🐻 狗熊工厂 4.9 | 正在修复正则，强攻 YAML 源...")
    final_nodes = []
    
    # 1. 读取 urls.txt (保持第一优先级)
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            my_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            for url in my_urls:
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        # 在私人源里找目标协议
                        lines = r.text.split('\n')
                        for line in lines:
                            link = clean_node_link(line)
                            if link: final_nodes.append(link)
                except: continue
    except FileNotFoundError: pass

    # 2. 核心修正：如果私人源不够，去高手库里用“宽口径”抓取
    print(f"📡 正在从高手库提取 HY2/TUIC/HTTP...")
    try:
        r = requests.get(GOLDEN_SOURCE, timeout=20)
        if r.status_code == 200:
            # 不再用全局正则，而是逐行扫描，确保不漏掉 YAML 里的任何一个
            lines = r.text.split('\n')
            for line in lines:
                # 只要行里包含目标协议关键字
                if any(p in line.lower() for p in ['hy2', 'hysteria2', 'tuic', 'http://']):
                    link = clean_node_link(line)
                    if link: final_nodes.append(link)
    except Exception as e:
        print(f"❌ 抓取高手库失败: {e}")

    # 3. 去重与输出
    final_nodes = list(dict.fromkeys(final_nodes))
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·修正版 | 成功提取: {len(final_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_nodes[:100]):
            # 移除可能存在的旧备注，统一狗熊标签
            clean_link = node.split('#')[0]
            p_tag = "HY2" if "hy" in clean_link else ("TUIC" if "tuic" in clean_link else "HTTP")
            f.write(f"{clean_link}#🚀狗熊_{p_tag}_{i+1:02d}\n")
    
    print(f"🎉 修复完成！共捞出 {len(final_nodes)} 个精品节点。")

if __name__ == "__main__":
    process()
