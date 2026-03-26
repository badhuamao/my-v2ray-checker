import base64
import requests
import socket
import time
import os
import json
import re
from urllib.parse import urlparse, unquote

# 地区映射表保持不变...
REGION_MAP = {
    '香港': ['HK', 'HONGKONG', '香港', 'HKG'],
    '日本': ['JP', 'JAPAN', '日本', 'TOKYO', 'OSAKA'],
    '台湾': ['TW', 'TAIWAN', '台湾', 'ROC', '台北'],
    '新加坡': ['SG', 'SINGAPORE', '新加坡', '獅城'],
    '美国': ['US', 'USA', '美国', 'UNITED STATES', 'LA', 'NY'],
    '韩国': ['KR', 'KOREA', '韩国', 'SEOUL'],
}

def is_valid_ip(address):
    """过滤掉内网和非法 IP"""
    if not address or address == '127.0.0.1' or address == '0.0.0.0':
        return False
    # 过滤掉常见的内网段
    if address.startswith(('192.168.', '10.', '172.16.', '172.31.')):
        return False
    return True

def test_tcp_connectivity(host, port, timeout=3):
    """多轮测试，确保不是偶然连通"""
    if not is_valid_ip(host):
        return None
    try:
        target_ip = socket.gethostbyname(host)
        # 进行两次握手测试，只有两次都成功才算可用
        for _ in range(2):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.time()
            result = sock.connect_ex((target_ip, int(port)))
            sock.close()
            if result != 0:
                return None
            time.sleep(0.1) # 短暂间隔
        return int((time.time() - start) * 1000)
    except:
        return None

def process():
    nodes_pool = []
    # 之前的抓取逻辑保持不变...
    # (由于篇幅，这里省略中间重复的获取和解析代码，请保留你现有的解析部分)
    
    # 在写入文件之前，我们再进行一次“去重”和“质量排序”
    nodes_pool.sort(key=lambda x: x['delay'])
    
    # 最终输出逻辑...
    # (同上，保留你之前的统一更名逻辑)
