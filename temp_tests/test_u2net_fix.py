#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试u2net模型修复白色文字问题
"""

import os
from pathlib import Path
from .batch_bg_removal import batch_remove_background
import shutil

def test_u2net_fix():
    """
    测试u2net模型修复白色文字边缘问题
    """
    print("=" * 60)
    print("🔧 测试u2net模型修复白色文字问题")
    print("=" * 60)
    
    # 创建测试目录
    test_input = Path("test_images/jpg")
    test_output = Path("test_images/png")
    
    test_input.mkdir(parents=True, exist_ok=True)
    test_output.mkdir(parents=True, exist_ok=True)
    
    # 查找有问题的图片文件
    problem_files = [
        "0828-i have_no_bg.png",  # 对应原图可能是 "0828-i have.jpeg"
        "0828-I Identify As A Problem _no_bg.png"  # 对应原图
    ]
    
    print("正在查找原始图片文件...")
    
    # 从images目录查找可能的原始文件
    images_dir = Path("images")
    found_files = []
    
    for file in images_dir.rglob("*.jpeg"):
        if "i have" in file.name.lower() or "identify" in file.name.lower():
            # 复制到测试目录
            dest = test_input / file.name
            shutil.copy2(file, dest)
            found_files.append(file.name)
            print(f"✓ 找到并复制: {file.name}")
    
    if not found_files:
        print("❌ 未找到相关的原始图片文件")
        print("请手动将有问题的原始图片放入 test_images/jpg/ 目录")
        return
    
    print(f"\n找到 {len(found_files)} 个文件，开始使用u2net模型处理...")
    
    # 使用u2net模型处理
    result = batch_remove_background(
        input_dir="test_images/jpg",
        output_dir="test_images/png", 
        model_name="u2net"
    )
    
    if result['success']:
        print("\n🎉 u2net模型处理完成!")
        print(f"✓ 成功处理: {result['processed']} 个文件")
        print(f"✓ 输出目录: test_images/png")
        print("\n请检查输出的图片，对比白色文字的边缘效果")
        
        # 列出输出文件
        output_files = list(test_output.glob("*.png"))
        if output_files:
            print("\n生成的文件:")
            for file in output_files:
                print(f"  - {file.name}")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    test_u2net_fix()