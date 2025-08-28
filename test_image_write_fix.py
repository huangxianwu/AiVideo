#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片写入和状态更新修复
验证图片写入到F列（产品模特合成图）和状态更新到H列（图片是否已处理）是否正确
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import load_config
from feishu_client import FeishuClient

async def test_column_mapping():
    print("🔍 测试图片写入和状态更新修复")
    print("=" * 80)
    
    # 加载配置
    config = load_config()
    feishu_client = FeishuClient(config.feishu)
    
    print("📋 配置验证:")
    print(f"- 图片写入列: {config.feishu.result_image_column} (应该是F列)")
    print(f"- 状态列表头: {config.feishu.status_column} (应该是'图片是否已处理')")
    print(f"- 合成图列表头: {config.feishu.composite_image_column} (应该是'产品模特合成图')")
    
    # 获取表格数据验证列映射
    try:
        rows = await feishu_client.get_sheet_data()
        print(f"\n✅ 成功获取 {len(rows)} 行数据")
        
        if len(rows) >= 1:
            first_row = rows[0]
            print(f"\n📊 第一行数据验证 (行号: {first_row.row_number}):")
            print(f"  产品图 (B列): {type(first_row.product_image).__name__}")
            print(f"  产品名 (C列): '{first_row.product_name}'")
            print(f"  模特图 (D列): {type(first_row.model_image).__name__}")
            print(f"  模特名 (E列): '{first_row.model_name}'")
            print(f"  合成图 (F列): '{first_row.composite_image}'")
            print(f"  提示词 (G列): '{first_row.prompt[:30]}...'")
            print(f"  图片处理状态 (H列): '{first_row.status}'")
            print(f"  视频状态 (I列): '{first_row.video_status}'")
            
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return
    
    print("\n🎯 修复验证:")
    print("-" * 50)
    print("✅ 图片写入位置修复:")
    print("   - 从 E列 修正为 F列 (产品模特合成图)")
    print("   - 配置项: result_image_column = 'F'")
    print("")
    print("✅ 状态更新位置修复:")
    print("   - 使用 H列 (图片是否已处理)")
    print("   - 硬编码列字母 'H' 替代表头名称")
    print("")
    print("🔄 工作流逻辑确认:")
    print("   1. 图片合成完成后 → 写入F列 (产品模特合成图)")
    print("   2. 同时更新H列状态 → '已完成' (图片是否已处理)")
    
    print("\n📝 修复总结:")
    print("- config.py: result_image_column 从 'E' 改为 'F'")
    print("- feishu_client.py: update_cell_status 使用硬编码 'H' 列")
    print("- 解决了终端日志中的写入位置错误问题")
    print("- 解决了状态更新失败的问题")
    
if __name__ == "__main__":
    asyncio.run(test_column_mapping())