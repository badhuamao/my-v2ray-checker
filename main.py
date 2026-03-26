import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

def safe_base64_decode(data):
    """通用的 Base64 解码"""
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
    return []

def test_tcp_connectivity(host, port, timeout=3):
    """测试 TCP 连通性，稍微延长超时时间提高成功率"""
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
    seen_ips = set() # 防止同一个服务器重复测试

    for link in sub_links:
        try:
            print(f"📡 正在拉取: {link[:50]}...")
            # 增加 User-Agent 伪装，防止被部分订阅服务器拒绝
            headers = {'User-Agent': 'v2rayN/6.23'}
            response = requests.get(link, headers=headers, timeout=15).text
            
            # 识别并解码 Base64 订阅内容
            content = safe_base64_decode(response) if "://" not in response[:20] else response
            
            lines = content.splitlines()
            print(f"解析到 {len(lines)} 行原始数据")

            for line in lines:
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, name = "", 0, ""
                # 兼容多种协议解析
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, name = cfg.get('add'), cfg.get('port'), cfg.get('ps', 'VMess Node')
                    except: continue
                else:
                    # 兼容 ss, ssr, vless, trojan, hysteria2 等
                    try:
                        p = urlparse(line)
                        addr, port, name = p.hostname, p.port, unquote(p.fragment) if p.fragment else "Unknown"
                    except: continue
                
                # 只要有地址和端口，就进行测试
                if addr and port:
                    if addr in seen_ips: continue # 相同 IP 只测一次
                    
                    delay = test_tcp_connectivity(addr, port)
                    if delay:
                        seen_ips.add(addr)
                        nodes_pool.append({"raw": line, "delay": delay, "name": name})
                        print(f"✅ 可用: [{delay}ms] {name}")
                        
        except Exception as e:
            print(f"❌ 抓取失败: {e}")

    # 排序：按延迟从小到大
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 写入结果
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 节点池总量: {len(nodes_pool)} | 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for n in nodes_pool[:50]: # 这次我们多存一点，存前 50 个
            f.write(f"{n['raw']}\n")
    
    print(f"\n🎉 完成！已精选出 {len(nodes_pool[:50])} 个最快节点。")

if __name__ == "__main__":
    process()
