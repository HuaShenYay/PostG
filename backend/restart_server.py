#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import sys

def restart_server():
    print("重启后端服务器...")
    
    # 杀死现有进程
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
    except:
        pass
    
    # 等待一下
    time.sleep(2)
    
    # 启动新服务器
    print("启动新服务器...")
    subprocess.run([sys.executable, 'run_server.py'])

if __name__ == '__main__':
    restart_server()
