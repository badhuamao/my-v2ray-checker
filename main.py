import requests, re, time, html

# 国家关键字映射表
FLAG_MAP = {
    'HK': '🇭🇰', 'HKG': '🇭🇰', '香港': '🇭🇰',
    'JP': '🇯🇵', 'JPN': '🇯🇵', '日本': '🇯🇵', '东京': '🇯🇵', '大阪': '🇯🇵',
    'TW': '🇹🇼', 'TWN': '🇹🇼', '台湾': '🇹🇼',
    'US': '🇺🇸', 'USA': '🇺🇸', '美国': '🇺🇸', '洛杉矶': '🇺🇸',
    'SG': '🇸🇬', 'SGP': '🇸🇬', '新加坡': '🇸🇬',
    'KR': '🇰🇷', 'KOR': '🇰🇷', '韩国': '🇰🇷',
    'GB': '🇬🇧', 'UK': '🇬🇧', '英国': '🇬🇧',
    'DE': '🇩🇪', '德国': '🇩🇪',
    'FR': '🇫🇷', '法国': '🇫🇷'
}

def get_country_flag(text):
    upper_text = text.upper()
    for key, emoji in FLAG_MAP.items():
        if key in upper_text:
            return emoji
    return '🌐'

def clean_node_link(raw_str):
    text = html.unescape(raw_str)
    pattern = r'(?P<link>(?:vmess|vless|ss|ssr|trojan|tuic|hy2|hysteria2|http)://[^\s\'"]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group('link').strip()
    return None

def get_node_key(link):
    """提取唯一特征防止重复"""
    return link.split('#')[0].split('?')[0]

def process():
    print(f"🐻 狗熊工厂 9.1 | 独立自主模式 | 目标 30 强")
    raw_pool = []
    
    # 仅挖掘 urls.txt 矿山
    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            for url in f:
                url = url.strip()
                if not url or url.startswith('#'): continue
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        for line in r.text.split('\n'):
                            link = clean_node_link(line)
                            if link:
                                raw_pool.append({'link': link, 'raw': line})
                except: continue
    except:
        print("⚠️ 找不到 urls.txt")
        return

    # 1. 深度去重
    seen_keys = set()
    unique_entries = []
    for entry in raw_pool:
        key = get_node_key(entry['link'])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_entries.append(entry)
    
    print(f"📡 矿山原始节点: {len(raw_pool)} | 唯一节点: {len(unique_entries)}")

    # 2. 协议排序并取前 30
    grpc_entries = [e for e in unique_entries if 'grpc' in e['link'].lower()]
    others = [e for e in unique_entries if e not in grpc_entries]
    final_selection = (grpc_entries + others)[:30]

    # 3. 写入文件
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·独立国际版 | 数量: {len(final_selection)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        for i, entry in enumerate(final_selection):
            link = entry['link']
            flag = get_country_flag(entry['raw'])
            
            low = link.lower()
            tag = "GRPC" if "grpc" in low else ("HY2" if "hy" in low else ("TUIC" if "tuic" in low else "HTTP"))
            
            # 格式：链接#国旗 🐻_协议_编号
            new_remark = f"{flag} 🐻_{tag}_{i+1:02d}"
            clean_link = link.split('#')[0]
            f.write(f"{clean_link}#{new_remark}\n")
    
    print(f"🎉 独立运行任务圆满完成！")

if __name__ == "__main__":
    process()
