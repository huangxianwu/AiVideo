#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图生视频工作流逻辑测试脚本
测试修复后的should_process_row方法是否正确判断处理条件
"""

import asyncio
import logging
from config import config
from feishu_client import FeishuClient
from workflow_manager import WorkflowManager, WorkflowMode

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_video_workflow_logic():
    """测试图生视频工作流判断逻辑"""
    
    logger.info("🧪 开始测试图生视频工作流判断逻辑")
    logger.info("="*60)
    
    # 检查配置
    logger.info(f"📋 配置检查:")
    logger.info(f"   - video_workflow_enabled: {config.comfyui.video_workflow_enabled}")
    logger.info(f"   - video_workflow_id: {config.comfyui.video_workflow_id}")
    logger.info(f"   - video_image_node_id: {config.comfyui.video_image_node_id}")
    logger.info(f"   - video_prompt_node_id: {config.comfyui.video_prompt_node_id}")
    
    if not config.comfyui.video_workflow_enabled:
        logger.error("❌ 视频工作流未启用！")
        return
    
    # 初始化客户端
    feishu_client = FeishuClient(config.feishu)
    workflow_manager = WorkflowManager(config, debug_mode=True)
    
    try:
        # 获取表格数据
        logger.info("\n📊 获取表格数据...")
        rows_data = await feishu_client.get_sheet_data()
        logger.info(f"获取到 {len(rows_data)} 行数据")
        
        if not rows_data:
            logger.error("❌ 没有获取到数据")
            return
        
        # 获取图生视频工作流
        video_workflow = workflow_manager.get_workflow(WorkflowMode.IMAGE_TO_VIDEO)
        
        # 统计分析
        total_rows = len(rows_data)
        should_process_count = 0
        skip_reasons = {
            'video_disabled': 0,
            'video_status_not_no': 0,
            'no_composite_image': 0,
            'no_prompt': 0,
            'should_process': 0
        }
        
        logger.info("\n🔍 逐行分析判断条件:")
        logger.info("-" * 60)
        
        for i, row_data in enumerate(rows_data[:10]):  # 只检查前10行
            logger.info(f"\n第 {row_data.row_number} 行分析:")
            
            # 检查各个条件
            video_enabled = config.comfyui.video_workflow_enabled
            video_status_is_no = row_data.video_status == "否"
            
            has_composite_image = (
                hasattr(row_data, 'composite_image') and 
                row_data.composite_image and 
                (
                    (isinstance(row_data.composite_image, str) and bool(row_data.composite_image.strip())) or
                    (isinstance(row_data.composite_image, dict) and bool(row_data.composite_image.get('fileToken')))
                )
            )
            
            has_prompt = (
                hasattr(row_data, 'prompt') and 
                row_data.prompt and 
                bool(row_data.prompt.strip())
            )
            
            logger.info(f"   - 视频工作流启用: {video_enabled}")
            logger.info(f"   - 视频状态为'否': {video_status_is_no} (当前: '{row_data.video_status}')")
            logger.info(f"   - 有合成图: {has_composite_image} (类型: {type(row_data.composite_image).__name__})")
            logger.info(f"   - 有提示词: {has_prompt} (长度: {len(row_data.prompt) if row_data.prompt else 0})")
            
            # 使用工作流的判断方法
            should_process = video_workflow.should_process_row(row_data)
            logger.info(f"   - 最终判断: {'✅ 应处理' if should_process else '❌ 跳过'}")
            
            # 统计原因
            if not video_enabled:
                skip_reasons['video_disabled'] += 1
            elif not video_status_is_no:
                skip_reasons['video_status_not_no'] += 1
            elif not has_composite_image:
                skip_reasons['no_composite_image'] += 1
            elif not has_prompt:
                skip_reasons['no_prompt'] += 1
            else:
                skip_reasons['should_process'] += 1
                should_process_count += 1
        
        # 输出统计结果
        logger.info("\n📈 统计结果:")
        logger.info("=" * 60)
        logger.info(f"总行数: {min(10, total_rows)}")
        logger.info(f"应处理行数: {should_process_count}")
        logger.info(f"跳过行数: {min(10, total_rows) - should_process_count}")
        logger.info("\n跳过原因分布:")
        logger.info(f"   - 视频工作流未启用: {skip_reasons['video_disabled']}")
        logger.info(f"   - 视频状态不是'否': {skip_reasons['video_status_not_no']}")
        logger.info(f"   - 没有合成图: {skip_reasons['no_composite_image']}")
        logger.info(f"   - 没有提示词: {skip_reasons['no_prompt']}")
        logger.info(f"   - 符合处理条件: {skip_reasons['should_process']}")
        
        if should_process_count > 0:
            logger.info(f"\n✅ 发现 {should_process_count} 行符合图生视频处理条件")
        else:
            logger.warning("\n⚠️ 没有发现符合图生视频处理条件的行")
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_video_workflow_logic())