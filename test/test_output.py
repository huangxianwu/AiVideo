#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 测试获取任务输出文件功能
"""

import asyncio
import os
from datetime import datetime
from config import load_config
from comfyui_client import ComfyUIClient


async def test_get_task_outputs():
    """测试获取任务输出文件"""
    # 加载配置
    config = load_config()
    
    # 创建ComfyUI客户端
    client = ComfyUIClient(config.comfyui)
    
    # 测试任务ID
    task_id = "1960192719241039874"
    
    print(f"开始测试获取任务 {task_id} 的输出文件...")
    
    try:
        # 获取任务输出
        result = await client.get_task_outputs(task_id)
        
        if result.success:
            print(f"✅ 成功获取到 {len(result.output_urls)} 个输出文件")
            
            # 确保output/img目录存在
            img_dir = "./output/img"
            os.makedirs(img_dir, exist_ok=True)
            
            # 下载并保存每个文件
            for i, url in enumerate(result.output_urls):
                print(f"正在下载文件 {i+1}/{len(result.output_urls)}: {url}")
                
                try:
                    # 下载文件
                    file_data = await client.download_result(url)
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"task_{task_id}_output_{i+1}_{timestamp}.png"
                    filepath = os.path.join(img_dir, filename)
                    
                    # 保存文件
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    print(f"✅ 文件保存成功: {filepath} ({len(file_data)} bytes)")
                    
                except Exception as e:
                    print(f"❌ 下载文件失败: {str(e)}")
        else:
            print(f"❌ 获取任务输出失败: {result.error}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")


if __name__ == "__main__":
    print("=== 任务输出文件测试脚本 ===")
    asyncio.run(test_get_task_outputs())
    print("=== 测试完成 ===")