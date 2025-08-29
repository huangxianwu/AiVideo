#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析表格中视频状态分布
找出哪些行的视频状态为"否"，应该被图生视频工作流处理
"""

import asyncio
import logging
from collections import Counter
from config import config
from feishu_client import FeishuClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def analyze_video_status():
    """分析表格中的视频状态分布"""
    
    logger.info("📊 开始分析表格中的视频状态分布")
    logger.info("="*60)
    
    # 初始化客户端
    feishu_client = FeishuClient(config.feishu)
    
    try:
        # 获取表格数据
        logger.info("📋 获取表格数据...")
        rows_data = await feishu_client.get_sheet_data()
        logger.info(f"获取到 {len(rows_data)} 行数据")
        
        if not rows_data:
            logger.error("❌ 没有获取到数据")
            return
        
        # 统计视频状态分布
        video_status_counter = Counter()
        rows_with_no_status = []
        rows_with_composite_and_prompt = []
        
        logger.info("\n🔍 分析每行数据...")
        
        for row_data in rows_data:
            video_status = row_data.video_status
            video_status_counter[video_status] += 1
            
            # 记录状态为"否"的行
            if video_status == "否":
                rows_with_no_status.append(row_data.row_number)
                
                # 检查是否同时有合成图和提示词
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
                
                if has_composite_image and has_prompt:
                    rows_with_composite_and_prompt.append({
                        'row_number': row_data.row_number,
                        'product_name': row_data.product_name,
                        'prompt_preview': row_data.prompt[:50] + '...' if len(row_data.prompt) > 50 else row_data.prompt
                    })
        
        # 输出统计结果
        logger.info("\n📈 视频状态分布统计:")
        logger.info("=" * 60)
        for status, count in video_status_counter.most_common():
            percentage = (count / len(rows_data)) * 100
            logger.info(f"   '{status}': {count} 行 ({percentage:.1f}%)")
        
        logger.info(f"\n🎯 状态为'否'的行: {len(rows_with_no_status)} 行")
        if rows_with_no_status:
            logger.info(f"   行号: {rows_with_no_status}")
        
        logger.info(f"\n✅ 符合图生视频处理条件的行: {len(rows_with_composite_and_prompt)} 行")
        logger.info("   (视频状态='否' + 有合成图 + 有提示词)")
        
        if rows_with_composite_and_prompt:
            logger.info("\n详细信息:")
            for row_info in rows_with_composite_and_prompt:
                logger.info(f"   第 {row_info['row_number']} 行: {row_info['product_name']} - {row_info['prompt_preview']}")
        
        # 分析问题
        logger.info("\n🔍 问题分析:")
        logger.info("-" * 60)
        
        if len(rows_with_composite_and_prompt) == 0:
            if len(rows_with_no_status) == 0:
                logger.warning("⚠️ 所有行的视频状态都不是'否'，可能已经全部处理完成")
                logger.info("💡 建议: 手动将某些行的视频状态改为'否'来测试图生视频工作流")
            else:
                logger.warning("⚠️ 虽然有视频状态为'否'的行，但它们缺少合成图或提示词")
                logger.info("💡 建议: 检查这些行的合成图和提示词数据")
        else:
            logger.info(f"✅ 发现 {len(rows_with_composite_and_prompt)} 行符合图生视频处理条件")
            logger.info("💡 这些行应该会被图生视频工作流处理")
        
        # 检查配置
        logger.info("\n⚙️ 配置检查:")
        logger.info("-" * 60)
        logger.info(f"   video_workflow_enabled: {config.comfyui.video_workflow_enabled}")
        if not config.comfyui.video_workflow_enabled:
            logger.error("❌ 视频工作流被禁用！这是图生视频被跳过的主要原因")
            logger.info("💡 解决方案: 设置环境变量 VIDEO_WORKFLOW_ENABLED=true 或修改配置文件")
        
    except Exception as e:
        logger.error(f"❌ 分析过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_video_status())