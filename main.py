import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

# 关键词扩展：包含地区简称和常用中文名
ASIA_KEYWORDS = ['HK', 'HONGKONG', '香港', 'JP', 'JAPAN', '日本', 'SG', 'SINGAPORE', '新加坡', 'KR', 'KOREA', '韩国', 'TW', 'TAIWAN', '台湾']

def safe_base64_decode(data):
    """鲁棒性强的 Base64 解码"""
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def test_tcp_connectivity(host, port, timeout=2):
    """测试 TCP 连通性，增加域名解析异常处理"""
    try:
        # 显式解析 IP，避免某些 DNS 污染导致脚本卡死
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
    sub_links = os.environ.get('SUB_LINKS', '').split('\n')
    seen_ips = set() # 去重，防止同一个服务器重复出现

    for link in [l.strip() for l in sub_links if l.strip()]:
        try:
            print(f"📡 抓取源: {link[:40]}...")
            response = requests.get(link, timeout=15).text
            
            # 自动识别订阅格式：Base64 还是 明文
            content = safe_base64_decode(response) if "://" not in response[:20] else response
            
            for line in content.splitlines():
                line = line.strip()
                if "://" not in line: continue
                
                # 协议解析：获取核心三要素 (地址, 端口, 备注)
                addr, port, name = "", 0, ""
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    p = urlparse(line)
                    addr, port, name = p.hostname, p.port, unquote(p.fragment)
                
                # 核心筛选：必须是亚洲关键词，且 IP 唯一
                if addr and port and any(k.upper() in name.upper() for k in ASIA_KEYWORDS):
                    if addr in seen_ips: continue
                    
                    delay = test_tcp_connectivity(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        nodes_pool.append({"raw": line, "delay": delay, "name": name})
                        print(f"✅ 捕获亚洲节点: [{delay}ms] {name}")
                        
        except Exception as e:
            print(f"❌ 订阅解析失败: {e}")

    # 排序：按延迟从小到大
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 输出结果：只保留前 30 个最精良的
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        for n in nodes_pool[:30]:
            f.write(f"{n['raw']}\n")
    
    print(f"\n🎉 筛选完成！当前可用亚洲节点总数: {len(nodes_pool)}")

if __name__ == "__main__":
    process()
