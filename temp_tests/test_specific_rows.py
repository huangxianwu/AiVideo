#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定行的图生视频工作流判断逻辑
专门测试第67、73、74、75行
"""

import asyncio
import logging
from config import config
from feishu_client import FeishuClient
from workflow_manager import WorkflowManager, WorkflowMode

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_specific_rows():
    """测试特定行的图生视频工作流判断逻辑"""
    
    target_rows = [67, 73, 74, 75]  # 应该被处理的行
    
    logger.info("🧪 测试特定行的图生视频工作流判断逻辑")
    logger.info("="*60)
    logger.info(f"目标行: {target_rows}")
    
    # 初始化客户端
    feishu_client = FeishuClient(config.feishu)
    workflow_manager = WorkflowManager(config, debug_mode=True)
    
    try:
        # 获取表格数据
        logger.info("\n📊 获取表格数据...")
        rows_data = await feishu_client.get_sheet_data()
        logger.info(f"获取到 {len(rows_data)} 行数据")
        
        # 筛选目标行
        target_rows_data = [row for row in rows_data if row.row_number in target_rows]
        logger.info(f"找到目标行数据: {len(target_rows_data)} 行")
        
        if not target_rows_data:
            logger.error("❌ 没有找到目标行数据")
            return
        
        # 获取图生视频工作流
        video_workflow = workflow_manager.get_workflow(WorkflowMode.IMAGE_TO_VIDEO)
        
        logger.info("\n🔍 详细测试每个目标行:")
        logger.info("-" * 60)
        
        for row_data in target_rows_data:
            logger.info(f"\n📋 第 {row_data.row_number} 行详细信息:")
            logger.info(f"   产品名: {row_data.product_name}")
            logger.info(f"   模特名: {row_data.model_name}")
            logger.info(f"   视频状态: '{row_data.video_status}'")
            logger.info(f"   合成图类型: {type(row_data.composite_image).__name__}")
            if isinstance(row_data.composite_image, dict):
                logger.info(f"   合成图fileToken: {row_data.composite_image.get('fileToken', 'N/A')[:20]}...")
            logger.info(f"   提示词长度: {len(row_data.prompt) if row_data.prompt else 0}")
            logger.info(f"   提示词预览: {row_data.prompt[:50]}...")
            
            # 调用should_process_row方法（会输出详细的调试信息）
            logger.info(f"\n🔍 调用should_process_row方法:")
            should_process = video_workflow.should_process_row(row_data)
            
            logger.info(f"\n🎯 第 {row_data.row_number} 行最终结果: {'✅ 应处理' if should_process else '❌ 跳过'}")
            
            if not should_process:
                logger.error(f"❌ 第 {row_data.row_number} 行被跳过，但应该被处理！")
            else:
                logger.info(f"✅ 第 {row_data.row_number} 行正确识别为应处理")
        
        # 测试完整工作流处理
        logger.info("\n🚀 测试完整工作流处理:")
        logger.info("=" * 60)
        
        # 只处理第一行作为测试
        test_row = target_rows_data[0]
        logger.info(f"测试处理第 {test_row.row_number} 行: {test_row.product_name}")
        
        # 使用工作流管理器处理
        results = await workflow_manager.process_with_workflow(
            WorkflowMode.IMAGE_TO_VIDEO, 
            [test_row]
        )
        
        if results:
            result = results[0]
            logger.info(f"处理结果: {'✅ 成功' if result.success else '❌ 失败'}")
            if result.error:
                logger.error(f"错误信息: {result.error}")
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_rows())