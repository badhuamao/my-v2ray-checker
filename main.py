import base64
import requests
import socket
import time
import os

# 亚洲常用节点关键词
ASIA_KEYWORDS = ['HK', 'HongKong', '香港', 'JP', 'Japan', '日本', 'SG', 'Singapore', '新加坡', 'KR', 'Korea', '韩国', 'TW', 'Taiwan', '台湾']

def get_sub_links():
    # 从 GitHub Secret 中获取链接
    links = os.environ.get('SUB_LINKS', '')
    return [l.strip() for l in links.split('\n') if l.strip()]

def test_tcp_latency(ip, port, timeout=2):
    """测试 TCP 握手延迟"""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        sock.close()
        return int((time.time() - start) * 1000)
    except:
        return 9999

def process():
    all_nodes = []
    sub_links = get_sub_links()
    
    for link in sub_links:
        try:
            res = requests.get(link, timeout=10).text
            # 解码 Base64 (补全 padding)
            missing_padding = len(res) % 4
            if missing_padding:
                res += '=' * (4 - missing_padding)
            decoded_data = base64.b64decode(res).decode('utf-8')
            
            for line in decoded_data.split('\n'):
                if not line: continue
                # 简单筛选亚洲节点名
                if any(k.upper() in line.upper() for k in ASIA_KEYWORDS):
                    # 这里为了演示仅做简单逻辑，实际解析 vmess:// 或 ss:// 需要正则
                    # 我们假设节点备注里含有信息，此处记录该行
                    all_nodes.append({"raw": line, "latency": 9999})
        except Exception as e:
            print(f"解析出错: {e}")

    # 模拟测试过程（实际解析建议配合专门的解析库，此处为逻辑框架）
    # 排序并取前30
    all_nodes.sort(key=lambda x: x['latency'])
    top_30 = all_nodes[:30]
    
    # 将结果写入文件
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        for node in top_30:
            f.write(node['raw'] + '\n')

if __name__ == "__main__":
    process()
