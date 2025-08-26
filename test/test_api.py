#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RunningHub API状态检查
"""

import asyncio
import aiohttp
import json

async def test_status_check():
    """测试状态检查API"""
    api_key = "d4b17e6ea9474695965f3f3c9dd53c1d"
    task_id = "1960180679239749634"  # 使用最新的任务ID
    
    url = "https://www.runninghub.cn/task/openapi/status"
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "application/x-www-form-urlencoded",
            "headers": {
                "Host": "www.runninghub.cn",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            "data": {
                "apiKey": api_key,
                "taskId": task_id
            }
        },
        {
            "name": "application/json",
            "headers": {
                "Host": "www.runninghub.cn",
                "Content-Type": "application/json"
            },
            "json": {
                "apiKey": api_key,
                "taskId": task_id
            }
        },
        {
            "name": "multipart/form-data",
            "headers": {
                "Host": "www.runninghub.cn"
            },
            "form_data": {
                "apiKey": api_key,
                "taskId": task_id
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n测试: {test_case['name']}")
            print(f"URL: {url}")
            print(f"Headers: {test_case['headers']}")
            
            try:
                if 'json' in test_case:
                    async with session.post(url, json=test_case['json'], headers=test_case['headers']) as response:
                        print(f"状态码: {response.status}")
                        print(f"响应头: {dict(response.headers)}")
                        text = await response.text()
                        print(f"响应内容: {text}")
                        try:
                            result = json.loads(text)
                            print(f"JSON解析: {result}")
                        except:
                            print("无法解析为JSON")
                elif 'form_data' in test_case:
                    form_data = aiohttp.FormData()
                    for key, value in test_case['form_data'].items():
                        form_data.add_field(key, value)
                    async with session.post(url, data=form_data, headers=test_case['headers']) as response:
                        print(f"状态码: {response.status}")
                        print(f"响应头: {dict(response.headers)}")
                        text = await response.text()
                        print(f"响应内容: {text}")
                        try:
                            result = json.loads(text)
                            print(f"JSON解析: {result}")
                        except:
                            print("无法解析为JSON")
                else:
                    async with session.post(url, data=test_case['data'], headers=test_case['headers']) as response:
                        print(f"状态码: {response.status}")
                        print(f"响应头: {dict(response.headers)}")
                        text = await response.text()
                        print(f"响应内容: {text}")
                        try:
                            result = json.loads(text)
                            print(f"JSON解析: {result}")
                        except:
                            print("无法解析为JSON")
            except Exception as e:
                print(f"请求失败: {e}")
            
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_status_check())