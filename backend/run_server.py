#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("启动后端服务器...")
    print("服务器地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    app.run(host='127.0.0.1', port=5000, debug=False)
