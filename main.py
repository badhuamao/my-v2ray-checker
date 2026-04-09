import requests, re, time, html

GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    # 采用最宽松的匹配，确保 HY2 的端口范围和 gRPC 参数完整
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def process():
    print(f"🐻 狗熊工厂 7.0 | 锁定前排新鲜节点...")
    
    # 分协议存储，但我们只取源文件里靠前的部分
    pool = {'GRPC': [], 'HY2': [], 'TUIC': [], 'HTTP': []}
    
    try:
        r = requests.get(GOLDEN_SOURCE, timeout=15)
        if r.status_code == 200:
            lines = r.text.split('\n')
            # 💡 核心改动：我们只扫描源文件的前 1000 行
            # 因为高手测速后的精华全在头部，后面的基本是死节点
            scan_range = lines[:1000] 
            
            for line in scan_range:
                link = clean_node_link(line)
                if link:
                    low = link.lower()
                    if 'grpc' in low: pool['GRPC'].append(link)
                    elif 'hy2' in low or 'hysteria2' in low: pool['HY2'].append(link)
                    elif 'tuic' in low: pool['TUIC'].append(link)
                    elif 'http://' in low: pool['HTTP'].append(link)
    except Exception as e:
        print(f"❌ 抓取失败: {e}")

    # 组装最终名单：从精华里挑精华
    # 既然 40 号后不通，我们只保留最强的 50 个节点
    final_nodes = []
    # 强制让 gRPC 和 HTTP 插队到最前面，看看能不能抢到活口
    final_nodes.extend(list(dict.fromkeys(pool['GRPC']))[:10])
    final_nodes.extend(list(dict.fromkeys(pool['HTTP']))[:5])
    final_nodes.extend(list(dict.fromkeys(pool['HY2']))[:25])
    final_nodes.extend(list(dict.fromkeys(pool['TUIC']))[:10])

    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·前排精选 | 总数: {len(final_nodes)} | 40号魔咒突破版 | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, node in enumerate(final_nodes):
            clean_link = node.split('#')[0]
            low = clean_link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            f.write(f"{clean_link}#🚀狗熊_{tag}_{i+1:02d}\n")
    
    print(f"🎉 任务完成！共精选 {len(final_nodes)} 个新鲜度最高的节点。")

if __name__ == "__main__":
    process()
