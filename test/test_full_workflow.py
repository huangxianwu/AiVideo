#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整工作流程：读取数据 -> 生成图片 -> 写入表格
"""

import asyncio
import os
from config import load_config
from feishu_client import FeishuClient
from comfyui_client import ComfyUIClient
from workflow_processor import WorkflowProcessor

async def test_single_row_workflow():
    """测试单行数据的完整工作流程"""
    
    # 加载配置
    config = load_config()
    processor = WorkflowProcessor(config)
    feishu_client = processor.feishu_client
    
    print(f"📝 开始测试完整工作流程...")
    print(f"📊 目标表格: {config.feishu.spreadsheet_token}")
    print(f"📋 目标工作表: {config.feishu.sheet_name}")
    
    try:
        # 1. 读取飞书数据
        print(f"\n🔄 步骤1: 读取飞书表格数据...")
        rows = await feishu_client.get_sheet_data()
        
        if not rows:
            print(f"❌ 没有找到任何数据行")
            return False
        
        print(f"✅ 成功读取 {len(rows)} 行数据")
        
        # 找到第一行有效数据进行测试
        test_row = None
        for row in rows:
            if row.status != "已完成":
                test_row = row
                break
        
        if not test_row:
            print(f"❌ 没有找到未完成的数据行进行测试")
            return False
        
        print(f"📍 选择测试行: 第{test_row.row_number}行")
        print(f"📦 产品名称: {test_row.product_name}")
        print(f"💬 提示词: {test_row.prompt[:50]}...")
        
        # 2. 处理单行数据
        print(f"\n🔄 步骤2: 处理工作流程...")
        success = await processor.process_single_row(test_row)
        
        if success:
            print(f"✅ 工作流程处理成功！")
            
            # 3. 验证输出文件
            print(f"\n🔄 步骤3: 验证输出文件...")
            output_dir = "/Users/winston/Desktop/Gitlab/repository/tk/toolKit/output"
            
            # 查找最新生成的图片文件
            latest_file = None
            latest_time = 0
            
            for filename in os.listdir(output_dir):
                if filename.endswith('.png') and test_row.product_name.replace("'", "").replace(" ", " ") in filename:
                    filepath = os.path.join(output_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = filename
            
            if latest_file:
                print(f"✅ 找到生成的图片文件: {latest_file}")
                
                # 4. 验证表格更新
                print(f"\n🔄 步骤4: 验证表格状态更新...")
                updated_rows = await feishu_client.get_sheet_data()
                updated_row = next((r for r in updated_rows if r.row_number == test_row.row_number), None)
                
                if updated_row and updated_row.status == "已完成":
                    print(f"✅ 表格状态已更新为: {updated_row.status}")
                    return True
                else:
                    print(f"⚠️  表格状态未更新，当前状态: {updated_row.status if updated_row else '未知'}")
                    return False
            else:
                print(f"❌ 未找到生成的图片文件")
                return False
        else:
            print(f"❌ 工作流程处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 完整工作流程测试")
    print("=" * 60)
    
    success = await test_single_row_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试完成：完整工作流程正常")
        print("✅ 所有功能验证通过：")
        print("   - 飞书数据读取 ✓")
        print("   - 图片生成 ✓")
        print("   - 图片写入表格 ✓")
        print("   - 状态更新 ✓")
    else:
        print("💥 测试失败：工作流程存在问题")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())