import base64
import requests
import socket
import time
import os
import re
import json

# 亚洲常用节点关键词
ASIA_KEYWORDS = ['HK', 'HongKong', '香港', 'JP', 'Japan', '日本', 'SG', 'Singapore', '新加坡', 'KR', 'Korea', '韩国', 'TW', 'Taiwan', '台湾']

def get_sub_links():
    links = os.environ.get('SUB_LINKS', '')
    return [l.strip() for l in links.split('\n') if l.strip()]

def test_latency(ip, port, timeout=3):
    """真正的 TCP 延迟测试"""
    start = time.time()
    try:
        # 尝试建立 TCP 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        sock.close()
        return int((time.time() - start) * 1000)
    except:
        return None # 连接失败返回 None

def parse_vmess(vmess_str):
    """解析 vmess:// 链接获取 IP 和端口"""
    try:
        data = vmess_str.replace('vmess://', '')
        # 处理 padding
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        config = json.loads(base64.b64decode(data).decode('utf-8'))
        return config.get('add'), config.get('port'), config.get('ps')
    except:
        return None, None, None

def process():
    valid_nodes = []
    sub_links = get_sub_links()
    
    for link in sub_links:
        try:
            res = requests.get(link, timeout=10).text
            missing_padding = len(res) % 4
            if missing_padding: res += '=' * (4 - missing_padding)
            decoded_data = base64.b64decode(res).decode('utf-8')
            
            for line in decoded_data.split('\n'):
                if not line.startswith('vmess://'): continue # 目前先处理 vmess
                
                addr, port, name = parse_vmess(line)
                if addr and any(k in name for k in ASIA_KEYWORDS):
                    print(f"正在测试: {name}...")
                    delay = test_latency(addr, port)
                    if delay is not None:
                        valid_nodes.append({"raw": line, "latency": delay, "name": name})
                        
        except Exception as e:
            print(f"解析出错: {e}")

    # 按延迟从小到大排序，取前 30
    valid_nodes.sort(key=lambda x: x['latency'])
    top_30 = valid_nodes[:30]
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        for node in top_30:
            f.write(f"{node['raw']}\n")
    
    print(f"完成！筛选出 {len(top_30)} 个可用亚洲节点。")

if __name__ == "__main__":
    process()
