#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试动态列定位功能
验证通过表头名称动态获取列位置的功能是否正常工作
"""

import asyncio
import logging
from config import FeishuConfig
from feishu_client import FeishuClient

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dynamic_column_positioning():
    """测试动态列定位功能"""
    try:
        # 初始化配置和客户端
        from config import config
        feishu_client = FeishuClient(config.feishu)
        
        logger.info("=== 动态列定位功能测试 ===")
        
        # 测试获取合成图列位置
        composite_column = await feishu_client._get_column_letter_by_header(config.feishu.composite_image_column)
        logger.info(f"'{config.feishu.composite_image_column}' 列位置: {composite_column}")
        
        # 测试获取状态列位置
        status_column = await feishu_client._get_column_letter_by_header(config.feishu.status_column)
        logger.info(f"'{config.feishu.status_column}' 列位置: {status_column}")
        
        # 验证结果
        if composite_column and status_column:
            logger.info("✅ 动态列定位功能正常工作")
            logger.info(f"合成图将写入到 {composite_column} 列")
            logger.info(f"状态将更新到 {status_column} 列")
            
            # 模拟测试写入和状态更新逻辑
            logger.info("\n=== 模拟工作流程 ===")
            logger.info(f"1. 图片合成完成后，将写入到 {composite_column} 列 ('{config.feishu.composite_image_column}')")
            logger.info(f"2. 状态将更新到 {status_column} 列 ('{config.feishu.status_column}') 为 '已完成'")
            
            return True
        else:
            logger.error("❌ 动态列定位功能异常")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        return False

async def main():
    """主函数"""
    success = await test_dynamic_column_positioning()
    
    if success:
        logger.info("\n=== 测试总结 ===")
        logger.info("✅ 动态列定位功能测试通过")
        logger.info("✅ 不再需要硬编码列位置")
        logger.info("✅ 系统将根据表头名称自动定位列位置")
    else:
        logger.error("\n=== 测试总结 ===")
        logger.error("❌ 动态列定位功能测试失败")

if __name__ == "__main__":
    asyncio.run(main())