import base64
import requests
import socket
import time
import os
import re
import json
from urllib.parse import urlparse, unquote

# 亚洲常用节点关键词
ASIA_KEYWORDS = ['HK', 'HongKong', '香港', 'JP', 'Japan', '日本', 'SG', 'Singapore', '新加坡', 'KR', 'Korea', '韩国', 'TW', 'Taiwan', '台湾']

def get_sub_links():
    links = os.environ.get('SUB_LINKS', '')
    return [l.strip() for l in links.split('\n') if l.strip()]

def test_latency(ip, port, timeout=2):
    """测试 TCP 握手延迟"""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        sock.close()
        return int((time.time() - start) * 1000)
    except:
        return None

def parse_node(line):
    """通用解析逻辑：提取 IP, 端口和备注名称"""
    try:
        if line.startswith('vmess://'):
            data = line.replace('vmess://', '')
            missing_padding = len(data) % 4
            if missing_padding: data += '=' * (4 - missing_padding)
            config = json.loads(base64.b64decode(data).decode('utf-8'))
            return config.get('add'), config.get('port'), config.get('ps')
        
        elif line.startswith(('ss://', 'trojan://', 'vless://', 'ssr://')):
            # 使用 URL 解析库处理通用格式
            parsed = urlparse(line)
            addr = parsed.hostname
            port = parsed.port
            # 备注通常在 # 后面
            name = unquote(parsed.fragment) if parsed.fragment else "Unknown"
            return addr, port, name
    except:
        pass
    return None, None, None

def process():
    valid_nodes = []
    sub_links = get_sub_links()
    
    for link in sub_links:
        try:
            print(f"正在抓取订阅: {link[:20]}...")
            res = requests.get(link, timeout=15).text
            # 处理可能的 Base64 订阅内容
            try:
                missing_padding = len(res) % 4
                if missing_padding: res += '=' * (4 - missing_padding)
                content = base64.b64decode(res).decode('utf-8')
            except:
                content = res # 如果不是 base64，尝试直接解析文本
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                
                addr, port, name = parse_node(line)
                
                # 筛选条件：1. 成功解析 2. 包含亚洲关键字
                if addr and port and any(k.upper() in name.upper() for k in ASIA_KEYWORDS):
                    delay = test_latency(addr, port)
                    if delay is not None:
                        valid_nodes.append({"raw": line, "latency": delay, "name": name})
                        print(f"有效节点: [{delay}ms] {name}")
                        
        except Exception as e:
            print(f"处理订阅出错: {e}")

    # 排序：延迟越低越靠前
    valid_nodes.sort(key=lambda x: x['latency'])
    top_30 = valid_nodes[:30]
    
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        for node in top_30:
            f.write(f"{node['raw']}\n")
    
    print(f"\n✅ 任务完成！已从大量节点中精选出 {len(top_30)} 个最快亚洲节点。")

if __name__ == "__main__":
    process()
