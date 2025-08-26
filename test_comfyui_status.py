#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ComfyUI任务状态检查接口
"""

import asyncio
import logging
from config import load_config
from comfyui_client import ComfyUIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_task_status_check():
    """测试任务状态检查接口"""
    try:
        # 加载配置
        config = load_config()
        client = ComfyUIClient(config.comfyui)
        
        # 使用一个已知的任务ID进行测试（从日志中获取的最近任务ID）
        test_task_id = "1960288078382473217"  # 从最新日志中获取的任务ID
        
        logger.info(f"开始测试任务状态检查接口，任务ID: {test_task_id}")
        
        # 测试check_task_status方法
        logger.info("=== 测试 check_task_status 方法 ===")
        
        # 手动调用API进行详细测试
        import aiohttp
        url = f"{config.comfyui.base_url}/task/openapi/status"
        headers = {"Host": "www.runninghub.cn", "Content-Type": "application/json"}
        payload = {"apiKey": config.comfyui.api_key, "taskId": test_task_id}
        
        logger.info(f"请求URL: {url}")
        logger.info(f"请求头: {headers}")
        logger.info(f"请求数据: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    logger.info(f"响应状态码: {response.status}")
                    response_text = await response.text()
                    logger.info(f"响应内容: {response_text}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            logger.info(f"解析后的JSON: {result}")
                        except Exception as json_e:
                            logger.error(f"JSON解析失败: {json_e}")
                    
        except Exception as api_e:
            logger.error(f"直接API调用失败: {api_e}")
        
        # 使用客户端方法测试
        status_result = await client.check_task_status(test_task_id)
        logger.info(f"客户端方法结果: {status_result}")
        
        # 测试get_task_outputs方法
        logger.info("=== 测试 get_task_outputs 方法 ===")
        outputs_result = await client.get_task_outputs(test_task_id)
        logger.info(f"输出获取结果: {outputs_result}")
        
        # 测试不存在的任务ID
        logger.info("=== 测试不存在的任务ID ===")
        fake_task_id = "9999999999999999999"
        fake_status_result = await client.check_task_status(fake_task_id)
        logger.info(f"假任务ID状态检查结果: {fake_status_result}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始ComfyUI状态检查接口测试")
    result = asyncio.run(test_task_status_check())
    if result:
        logger.info("测试完成")
    else:
        logger.error("测试失败")