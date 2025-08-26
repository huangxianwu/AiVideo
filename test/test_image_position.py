#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片写入位置的脚本
验证图片能否正确写入到对应行的E列
"""

import asyncio
import os
from config import load_config
from feishu_client import FeishuClient

async def test_image_position():
    """测试图片写入位置功能"""
    print("=" * 60)
    print("🧪 图片位置写入测试")
    print("=" * 60)
    
    # 初始化配置和客户端
    config = load_config()
    feishu_client = FeishuClient(config.feishu)
    
    try:
        # 获取访问令牌
        await feishu_client.get_access_token()
        print("✅ 飞书访问令牌获取成功")
        
        # 读取表格数据
        print("\n🔄 步骤1: 读取飞书表格数据...")
        data_rows = await feishu_client.get_sheet_data()
        
        if not data_rows:
            print("❌ 没有找到数据行")
            return
            
        print(f"✅ 成功读取 {len(data_rows)} 行数据")
        
        # 查找现有的图片文件
        print("\n🔄 步骤2: 查找现有图片文件...")
        output_dir = config.output_dir
        image_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        
        if not image_files:
            print("❌ 没有找到图片文件")
            return
            
        # 使用最新的图片文件
        test_image = os.path.join(output_dir, image_files[-1])
        print(f"✅ 找到测试图片: {image_files[-1]}")
        
        # 测试每一行的图片写入
        print("\n🔄 步骤3: 测试图片写入位置...")
        
        for i, row_data in enumerate(data_rows[:3]):  # 只测试前3行
            print(f"\n📍 测试第 {i+1} 行数据:")
            print(f"   行号: {row_data.row_number}")
            print(f"   产品名: {row_data.product_name}")
            print(f"   目标位置: E{row_data.row_number}")
            
            # 写入图片到对应行的E列
            success = await feishu_client.write_image_to_cell(
                row_number=row_data.row_number,
                image_path=test_image
            )
            
            if success:
                print(f"   ✅ 图片成功写入 E{row_data.row_number}")
            else:
                print(f"   ❌ 图片写入失败 E{row_data.row_number}")
            
            # 等待一下避免API限制
            await asyncio.sleep(1)
        
        print("\n🔄 步骤4: 验证写入结果...")
        print("请检查飞书表格，确认图片是否写入到正确的位置:")
        for i, row_data in enumerate(data_rows[:3]):
            print(f"   第{i+1}行 -> E{row_data.row_number} (产品: {row_data.product_name})")
        
        print("\n" + "=" * 60)
        print("✅ 图片位置测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_position())