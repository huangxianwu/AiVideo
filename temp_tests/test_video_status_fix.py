#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频状态更新修复
验证update_video_status方法是否能正确更新飞书表格中的视频状态
"""

import asyncio
import logging
from feishu_client import FeishuClient
from config import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_video_status_update():
    """测试视频状态更新功能"""
    
    logger.info("🧪 开始测试视频状态更新修复")
    logger.info("="*60)
    
    # 初始化客户端
    feishu_client = FeishuClient(config.feishu)
    
    try:
        # 获取表格数据，找一个视频状态为"否"的行进行测试
        logger.info("📋 获取表格数据...")
        rows_data = await feishu_client.get_sheet_data()
        
        if not rows_data:
            logger.error("❌ 没有获取到数据")
            return
        
        # 找到一个视频状态为"否"的行
        test_row = None
        for row_data in rows_data:
            if row_data.video_status == "否":
                test_row = row_data.row_number
                break
        
        if not test_row:
            logger.warning("⚠️ 没有找到视频状态为'否'的行，使用第一行进行测试")
            test_row = rows_data[0].row_number if rows_data else 2
        
        logger.info(f"🎯 选择第{test_row}行进行测试")
        
        # 测试更新视频状态为"测试中"
        logger.info(f"📝 测试更新第{test_row}行的视频状态为'测试中'")
        
        success = await feishu_client.update_video_status(test_row, "测试中")
        
        if success:
            logger.info("✅ 视频状态更新成功")
            
            # 等待一秒后恢复原状态
            await asyncio.sleep(1)
            logger.info("🔄 恢复原状态为'否'...")
            restore_success = await feishu_client.update_video_status(test_row, "否")
            
            if restore_success:
                logger.info("✅ 状态恢复成功")
            else:
                logger.error("❌ 状态恢复失败")
        else:
            logger.error("❌ 视频状态更新失败")
            return
        
        # 测试更新为"已完成"
        logger.info(f"📝 测试更新第{test_row}行的视频状态为'已完成'")
        
        success = await feishu_client.update_video_status(test_row, "已完成")
        
        if success:
            logger.info("✅ 视频状态更新为'已完成'成功")
            
            # 等待一秒后恢复原状态
            await asyncio.sleep(1)
            logger.info("🔄 恢复原状态为'否'...")
            restore_success = await feishu_client.update_video_status(test_row, "否")
            
            if restore_success:
                logger.info("✅ 状态恢复成功")
                logger.info("🎉 所有测试通过！视频状态更新功能正常")
            else:
                logger.error("❌ 状态恢复失败")
        else:
            logger.error("❌ 视频状态更新失败")
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_video_status_update())