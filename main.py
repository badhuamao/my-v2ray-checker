import requests, re, time

# 直接锁定高手 Docker 测速后的成品源
GOLDEN_SOURCE = "https://fastly.jsdelivr.net/gh/dongchengjie/airport@main/subs/merged/tested_within.yaml"

def extract_specific_nodes(text):
    """
    精准提取：只保留 HY2, TUIC 和 HTTP 协议
    """
    # 匹配 hysteria2/hy2, tuic 以及 http 协议链接
    # 过滤掉 vmess, vless, ss, ssr, trojan
    pattern = r'(?:hysteria2|hy2|tuic|http)://[a-zA-Z0-9$_.+!*\'(),;?:@&=%/-]+(?:#[^\s"\'<>]+)?'
    return re.findall(pattern, text)

def process():
    print(f"🐻 狗熊工厂 4.5 | 目标：只保留 HY2/TUIC/HTTP 节点...")
    try:
        # 使用加速镜像读取
        r = requests.get(GOLDEN_SOURCE, timeout=20)
        if r.status_code != 200:
            print("❌ 获取源失败，请检查网络或镜像链接"); return
        
        all_nodes = extract_specific_nodes(r.text)
        
        # 简单去重
        unique_nodes = list(dict.fromkeys(all_nodes))
        print(f"✅ 成功提取并过滤出 {len(unique_nodes)} 个目标节点")

    except Exception as e:
        print(f"💥 运行崩溃: {e}"); return

    # 写入结果
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 狗熊·极简订阅 | 协议: HY2/TUIC/HTTP | 数量: {len(unique_nodes)} | 更新: {time.strftime('%Y-%m-%d %H:%M')}\n")
        
        for i, node in enumerate(unique_nodes):
            # 统一清理旧备注并打上“狗熊”标签
            clean_link = node.split('#')[0]
            # 这里可以根据协议类型打标，方便你在客户端区分
            p_type = "HY2" if "hy" in clean_link else ("TUIC" if "tuic" in clean_link else "HTTP")
            f.write(f"{clean_link}#🐻{p_type}_{i+1:02d}\n")
    
    print("🎉 任务圆满完成！")

if __name__ == "__main__":
    process()
