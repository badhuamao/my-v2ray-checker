import base64
import requests
import socket
import time
import os
import json
from urllib.parse import urlparse, unquote

# 亚洲常用节点关键词
ASIA_KEYWORDS = ['HK', 'HONGKONG', '香港', 'JP', 'JAPAN', '日本', 'SG', 'SINGAPORE', '新加坡', 'KR', 'KOREA', '韩国', 'TW', 'TAIWAN', '台湾']

def get_sub_links():
    """改为从本地 urls.txt 文件读取链接"""
    file_path = 'urls.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# ... 后面的 test_tcp_connectivity 和 process 函数保持不变 ...
# 确保 process() 内部调用的是这个新的 get_sub_links() 即可
