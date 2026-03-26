import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

# 地区映射表：用于规范化显示名称
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG', '廣港', '深港'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA', '東京', '大阪'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC', '台北', '新北'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡', '獅城'],
    '美国': ['US', 'USA', '美国', 'UNITED STATES', 'LA', 'NY', '圣何塞'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL', '首尔'],
}

def is_valid_node(host):
    """基本合法性校验：排除非法/内网IP"""
    if not host or host in ['127.0.0.1', '0.0.0.0', 'localhost']:
        return False
    # 排除常见的内网私有地址段
    if host.startswith(('10.', '192.168.', '172.16.', '172.31.')):
        return False
    return True

def get_region_name(raw_name):
    upper_name = raw_name.upper()
    for region, keywords in REGION_MAP.items():
        if any(k.upper() in upper_name for k in keywords):
            return region
    return "其他"

def safe_base64_decode(data):
    try:
        data = data.strip().replace('-', '+').replace('_', '/')
        while len(data) % 4 != 0: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def test_connectivity(host, port, timeout=2.5):
    """深度 TCP 测试：双轮握手，确保稳定性"""
    if not is_valid_node(host):
        return None
    try:
        target_ip = socket.gethostbyname(host)
        # 连续进行两次测试，只要有一次失败就视为不可用
        for _ in range(2):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.time()
            result = sock.connect_ex((target_ip, int(port)))
            sock.close()
            if result != 0:
                return None
            time.sleep(0.05)
        return int((time.time() - start) * 1000)
    except:
        return None

def process():
    nodes_pool = []
    file_path = 'urls.txt'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sub_links = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    seen_ips = set()
    for link in sub_links:
        try:
            print(f"📡 抓取源: {link[:40]}...")
            headers = {'User-Agent': 'v2rayN/6.23'}
            response = requests.get(link, headers=headers, timeout=10).text
            content = safe_base64_decode(response) if "://" not in response[:20] else response
            
            for line in content.splitlines():
                line = line.strip()
                if "://" not in line: continue
                
                addr, port, raw_name = "", 0, ""
                if line.startswith('vmess://'):
                    try:
                        cfg = json.loads(safe_base64_decode(line[8:]))
                        addr, port, raw_name = cfg.get('add'), cfg.get('port'), cfg.get('ps', '')
                    except: continue
                else:
                    try:
                        p = urlparse(line)
                        addr, port, raw_name = p.hostname, p.port, unquote(p.fragment) if p.fragment else ""
                    except: continue
                
                if addr and port:
                    # 彻底查杀：相同 IP 的节点只留第一个
                    if addr in seen_ips: continue
                    
                    delay = test_connectivity(addr, port)
                    # 过滤掉延迟过高(>2500ms)或连接失败的节点
                    if delay and delay < 2500:
                        seen_ips.add(addr)
                        region = get_region_name(raw_name)
                        nodes_pool.append({"raw": line, "delay": delay, "region": region})
                        print(f"✅ 有效节点: [{delay}ms] {region}")
                        
        except Exception as e:
            print(f"❌ 链接跳过: {e}")

    # 按延迟排序
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 写入文件并重新编号命名
    region_counter = {}
    with open('top_asia_nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 纯净订阅 | 筛选时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for n in nodes_pool[:50]:
            reg = n['region']
            region_counter[reg] = region_counter.get(reg, 0) + 1
            new_name = f"[{reg}] {region_counter[reg]:02d}"
            
            final_link = n['raw']
            # 重命名逻辑 (VMess / 其他)
            if final_link.startswith('vmess://'):
                try:
                    cfg = json.loads(safe_base64_decode(final_link[8:]))
                    cfg['ps'] = new_name
                    final_link = "vmess://" + base64.b64encode(json.dumps(cfg).encode('utf-8')).decode('utf-8')
                except: pass
            else:
                base_url = final_link.split('#')[0]
                final_link = f"{base_url}#{new_name}"
            
            f.write(f"{final_link}\n")
    
    print(f"\n🎉 清洗完成！保留了 {len(nodes_pool[:50])} 个最稳节点。")

if __name__ == "__main__":
    process()
