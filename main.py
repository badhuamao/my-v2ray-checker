import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

# 更加严格的亚洲关键字（避免匹配到包含这些字母的随机字符串）
ASIA_KEYWORDS = ['香港', 'HK', 'HONGKONG', '日本', 'JP', 'JAPAN', '新加坡', 'SG', 'SINGAPORE', '韩国', 'KR', 'KOREA', '台湾', 'TW', 'TAIWAN']

def get_sub_links():
    links = os.environ.get('SUB_LINKS', '')
    return [l.strip() for l in links.split('\n') if l.strip()]

def test_tcp(ip, port, timeout=1.5):
    """快速过滤不可连接的 IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def safe_base64_decode(data):
    """通用的 Base64 解码，处理各种不规范的 padding"""
    data = data.replace('-', '+').replace('_', '/')
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    try:
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return ""

def process():
    final_nodes = []
    sub_links = get_sub_links()
    
    for link in sub_links:
        try:
            print(f"正在获取: {link[:30]}...")
            raw_content = requests.get(link, timeout=15).text.strip()
            
            # 自动识别是否为 Base64 加密的订阅内容
            if not raw_content.startswith(('vmess://', 'ss://', 'vless://', 'trojan://')):
                decoded_content = safe_base64_decode(raw_content)
            else:
                decoded_content = raw_content

            lines = decoded_content.splitlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # 提取节点名称进行区域过滤
                node_name = ""
                addr, port = "", ""
                
                if line.startswith('vmess://'):
                    try:
                        v_config = json.loads(safe_base64_decode(line[8:]))
                        node_name = v_config.get('ps', '')
                        addr, port = v_config.get('add'), v_config.get('port')
                    except: continue
                else:
                    parsed = urlparse(line)
                    node_name = unquote(parsed.fragment)
                    addr, port = parsed.hostname, parsed.port

                # 核心筛选逻辑
                if addr and port and any(k.upper() in node_name.upper() for k in ASIA_KEYWORDS):
                    # 只有 TCP 连通的才加入列表
                    start_time = time.time()
                    if test_tcp(addr, port):
                        latency = int((time.time() - start_time) * 1000)
                        final_nodes.append({"raw": line, "latency": latency})
                        print(f"✅ 发现可用亚洲节点: {node_name} ({latency}ms)")
        except Exception as e:
            print(f"解析出错: {e}")

    # 排序并保存
    final_nodes.sort(key=lambda x: x['latency'])
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        for node in final_nodes[:30]:
            f.write(f"{node['raw']}\n")

if __name__ == "__main__":
    process()
