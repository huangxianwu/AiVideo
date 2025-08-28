#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PNG处理器：批量处理images/jpg文件夹下的图片，去除白色背景并输出到images/png文件夹
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from png_processor import WhiteBackgroundRemover
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_batch_process():
    """
    测试批量处理功能：将images/jpg文件夹下的图片转换为去白底的PNG格式
    """
    # 设置路径
    input_dir = project_root / "images" / "jpg"
    output_dir = project_root / "images" / "png"
    
    logger.info(f"输入目录: {input_dir}")
    logger.info(f"输出目录: {output_dir}")
    
    # 检查输入目录是否存在
    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        return False
    
    # 创建输出目录（如果不存在）
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建白底移除器实例
    remover = WhiteBackgroundRemover()
    
    # 执行批量处理
    logger.info("开始批量处理图片...")
    remover.process_batch(str(input_dir), str(output_dir))
    
    # 检查处理结果
    png_files = list(output_dir.glob("*.png"))
    logger.info(f"处理完成，输出目录中共有 {len(png_files)} 个PNG文件")
    
    return True

def test_single_image():
    """
    测试单张图片处理功能（如果有测试图片的话）
    """
    # 查找jpg文件夹中的第一张图片进行测试
    input_dir = project_root / "images" / "jpg"
    output_dir = project_root / "images" / "png"
    
    # 查找支持的图片格式
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    test_image = None
    
    for ext in supported_formats:
        images = list(input_dir.glob(f"*{ext}")) + list(input_dir.glob(f"*{ext.upper()}"))
        if images:
            test_image = images[0]
            break
    
    if test_image:
        logger.info(f"找到测试图片: {test_image}")
        
        # 创建白底移除器实例
        remover = WhiteBackgroundRemover()
        
        # 设置输出路径
        output_path = output_dir / f"{test_image.stem}_no_bg.png"
        
        # 处理单张图片
        success = remover.process_single_image(str(test_image), str(output_path))
        
        if success:
            logger.info(f"单张图片处理成功: {output_path}")
        else:
            logger.error("单张图片处理失败")
            
        return success
    else:
        logger.warning("未找到测试图片")
        return True

def main():
    """
    主函数：执行PNG处理测试
    """
    logger.info("=== PNG处理器测试开始 ===")
    
    try:
        # 测试批量处理
        logger.info("\n--- 测试批量处理 ---")
        batch_success = test_batch_process()
        
        # 测试单张图片处理
        logger.info("\n--- 测试单张图片处理 ---")
        single_success = test_single_image()
        
        # 总结测试结果
        logger.info("\n=== 测试结果总结 ===")
        logger.info(f"批量处理测试: {'成功' if batch_success else '失败'}")
        logger.info(f"单张处理测试: {'成功' if single_success else '失败'}")
        
        if batch_success and single_success:
            logger.info("所有测试通过！")
            return True
        else:
            logger.error("部分测试失败")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)