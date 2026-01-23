#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def debug_api():
    base_url = "http://127.0.0.1:5000"
    
    print("调试全站统计API...")
    try:
        response = requests.get(f"{base_url}/api/global/stats")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n调试趋势API...")
    try:
        response = requests.get(f"{base_url}/api/global/trends")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    debug_api()
