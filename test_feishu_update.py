#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书表格状态更新功能
只测试图片写入和状态更新，不调用runninghub工作流API
"""

import asyncio
import logging
import os
from pathlib import Path
from config import load_config
from feishu_client import FeishuClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_feishu_update():
    """测试飞书表格状态更新功能"""
    try:
        # 加载配置
        config = load_config()
        feishu_client = FeishuClient(config.feishu)
        
        # 测试参数
        test_row_number = 3  # 测试第3行
        test_image_path = "./output/test_image.png"  # 测试图片路径
        
        # 创建一个测试图片文件（如果不存在）
        if not os.path.exists(test_image_path):
            # 创建输出目录
            os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
            
            # 创建一个简单的测试图片（1x1像素的PNG）
            import base64
            # 最小的PNG文件数据
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            )
            with open(test_image_path, 'wb') as f:
                f.write(png_data)
            logger.info(f"创建测试图片: {test_image_path}")
        
        logger.info("=== 开始测试飞书表格状态更新功能 ===")
        
        # 步骤1: 获取飞书Token
        logger.info("步骤1: 获取飞书访问Token")
        token = await feishu_client.get_access_token()
        if token:
            logger.info("✅ Token获取成功")
        else:
            logger.error("❌ Token获取失败")
            return False
        
        # 步骤2: 获取表格信息
        logger.info("步骤2: 获取表格信息")
        sheet_info = await feishu_client.get_sheet_info()
        if sheet_info:
            logger.info(f"✅ 表格信息获取成功: {sheet_info.get('title', 'Unknown')}")
        else:
            logger.error("❌ 表格信息获取失败")
            return False
        
        # 步骤3: 写入图片到第8行
        logger.info("步骤3: 写入图片到第8行")
        image_result_8 = await feishu_client.write_image_to_cell(8, test_image_path)
        if image_result_8:
            logger.info("✅ 第8行图片写入成功")
        else:
            logger.error("❌ 第8行图片写入失败")
            return False
        
        # 步骤4: 更新第8行状态字段
        logger.info("步骤4: 更新第8行状态为'已完成'")
        status_result_8 = await feishu_client.update_cell_status(8, "已完成")
        if status_result_8:
            logger.info("✅ 第8行状态更新成功")
        else:
            logger.error("❌ 第8行状态更新失败")
            return False
        
        # 步骤5: 写入图片到第9行
        logger.info("步骤5: 写入图片到第9行")
        image_result_9 = await feishu_client.write_image_to_cell(9, test_image_path)
        if image_result_9:
            logger.info("✅ 第9行图片写入成功")
        else:
            logger.error("❌ 第9行图片写入失败")
            return False
        
        # 步骤6: 更新第9行状态字段
        logger.info("步骤6: 更新第9行状态为'已完成'")
        status_result_9 = await feishu_client.update_cell_status(9, "已完成")
        if status_result_9:
            logger.info("✅ 第9行状态更新成功")
        else:
            logger.error("❌ 第9行状态更新失败")
            return False
        
        logger.info("=== 测试完成，所有步骤都成功 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        return False

async def main():
    """主函数"""
    logger.info("开始飞书表格状态更新测试")
    
    success = await test_feishu_update()
    
    if success:
        logger.info("🎉 测试成功完成！")
    else:
        logger.error("❌ 测试失败")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())