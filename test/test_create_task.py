#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建一个简单的ComfyUI任务用于测试状态检查
"""

import asyncio
import logging
from config import load_config
from comfyui_client import ComfyUIClient
import tempfile
import os
from PIL import Image
import io

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_test_task():
    """创建一个测试任务"""
    try:
        # 加载配置
        config = load_config()
        client = ComfyUIClient(config.comfyui)
        
        # 创建一个简单的测试图片
        img = Image.new('RGB', (512, 512), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(img_data)
            temp_file_path = temp_file.name
        
        try:
            logger.info("开始创建图生视频任务...")
            
            # 创建图生视频工作流
            result = await client.process_video_workflow(
                image_file_path=temp_file_path,
                prompt="a beautiful landscape"
            )
            
            if result.success:
                logger.info(f"任务创建成功！任务ID: {result.task_id}")
                return result.task_id
            else:
                logger.error(f"任务创建失败: {result.error}")
                return None
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("开始创建测试任务")
    task_id = asyncio.run(create_test_task())
    if task_id:
        logger.info(f"测试任务ID: {task_id}")
        print(f"\n请使用此任务ID进行状态检查测试: {task_id}")
    else:
        logger.error("任务创建失败")