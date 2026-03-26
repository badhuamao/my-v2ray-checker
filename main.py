import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

# 亚洲常用节点关键词
ASIA_KEYWORDS = ['HK', 'HONGKONG', '香港', 'JP', 'JAPAN', '日本', 'SG', 'SINGAPORE', '新加坡', 'KR', 'KOREA', '韩国', 'TW', 'TAIWAN', '台湾']

def safe_base64_decode(data):
    """鲁棒性强的 Base64 解码"""
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def get_sub_links():
    """从本地 urls.txt 文件读取订阅链接"""
    file_path = 'urls.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    print("错误：未找到 urls.txt 文件！")
    return []

def test_tcp_connectivity(host, port, timeout=2):
    """测试 TCP 连通性"""
    try:
        target_ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        result = sock.connect_ex((target_ip, int(port)))
        delay = int((time.time() - start) * 1000)
        sock.close()
        return delay if result == 0 else None
    except:
        return None

def process():
    nodes_pool = []
    sub_links = get_sub_links()
    seen_ips = set()

    for link in sub_links:
        try:
            print(f"📡 正在抓取源: {link[:50]}...")
            response = requests.get(link, timeout=15).text
            
            # 自动识别订阅格式
            content = safe_base64_decode(response) if "://" not in response[:20] else response
            
            for line in content.splitlines():
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, name = "", 0, ""
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    p = urlparse(line)
                    addr, port, name = p.hostname, p.port, unquote(p.fragment)
                
                # 筛选亚洲关键词
                if addr and port and any(k.upper() in name.upper() for k in ASIA_KEYWORDS):
                    if addr in seen_ips: continue
                    
                    delay = test_tcp_connectivity(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        nodes_pool.append({"raw": line, "delay": delay, "name": name})
                        print(f"✅ 发现可用节点: [{delay}ms] {name}")
                        
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

    # 按延迟排序
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 写入结果，并加上时间戳方便观察更新
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 最后更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
        for n in nodes_pool[:30]:
            f.write(f"{n['raw']}\n")
    
    print(f"\n🎉 筛选完成！已保存 {len(nodes_pool[:30])} 个最快节点到 top_asia_nodes.txt")

if __name__ == "__main__":
    process()
