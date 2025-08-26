#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片写入飞书表格功能
"""

import asyncio
import os
from config import load_config
from feishu_client import FeishuClient

async def test_write_image_to_cell():
    """测试将图片写入飞书表格单元格"""
    
    # 加载配置
    config = load_config()
    feishu_client = FeishuClient(config.feishu)
    
    # 使用现有的输出图片进行测试
    test_image_path = "/Users/winston/Desktop/Gitlab/repository/tk/toolKit/output/0826-Its Past My Bedtime Tshirt_08-26-13-44.png"
    
    # 检查图片文件是否存在
    if not os.path.exists(test_image_path):
        print(f"❌ 测试图片不存在: {test_image_path}")
        return False
    
    print(f"📝 开始测试图片写入功能...")
    print(f"📁 测试图片路径: {test_image_path}")
    print(f"📊 目标表格: {config.feishu.spreadsheet_token}")
    print(f"📋 目标工作表: {config.feishu.sheet_name}")
    
    try:
        # 测试写入到第1行E列
        test_row = 1
        print(f"\n🔄 正在写入图片到第{test_row}行E列...")
        
        success = await feishu_client.write_image_to_cell(test_row, test_image_path)
        
        if success:
            print(f"✅ 图片写入成功！")
            print(f"📍 位置: {config.feishu.sheet_name}!E{test_row}")
            return True
        else:
            print(f"❌ 图片写入失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        return False

async def main():
    """主函数"""
    print("=" * 50)
    print("🧪 飞书表格图片写入功能测试")
    print("=" * 50)
    
    success = await test_write_image_to_cell()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成：图片写入功能正常")
    else:
        print("💥 测试失败：图片写入功能异常")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())