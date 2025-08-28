#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复杂背景移除测试脚本
针对非白底、复杂背景图片的背景移除
"""

import os
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rembg_models(input_path, output_dir):
    """测试不同的rembg模型"""
    try:
        from rembg import remove, new_session
        from PIL import Image
        
        # 不同模型适合不同类型的图片
        models_to_test = [
            ('isnet-general-use', '高质量通用模型，推荐首选'),
            ('u2net', '经典模型，人像效果好'), 
            ('u2netp', '轻量版本，速度快'),
            ('silueta', '人像专用模型'),
            ('sam', '最新SAM模型')
        ]
        
        input_image = Image.open(input_path)
        results = {}
        
        for model_name, description in models_to_test:
            try:
                logger.info(f"测试模型: {model_name} - {description}")
                
                # 创建会话
                session = new_session(model_name)
                
                # 移除背景
                output_image = remove(input_image, session=session)
                
                # 保存结果
                output_path = Path(output_dir) / f"{Path(input_path).stem}_{model_name}.png"
                output_image.save(output_path)
                
                results[model_name] = {
                    'success': True,
                    'path': str(output_path),
                    'description': description
                }
                
                logger.info(f"✓ {model_name} 处理完成: {output_path}")
                
            except Exception as e:
                logger.error(f"✗ {model_name} 处理失败: {e}")
                results[model_name] = {
                    'success': False,
                    'error': str(e),
                    'description': description
                }
        
        return results
        
    except ImportError:
        logger.error("Rembg未安装，请运行: pip install rembg[gpu]")
        return None

def test_with_preprocessing(input_path, output_dir):
    """带预处理的背景移除"""
    try:
        from rembg import remove, new_session
        from PIL import Image, ImageEnhance, ImageFilter
        import numpy as np
        
        # 读取原图
        original = Image.open(input_path)
        
        # 预处理选项
        preprocessing_options = [
            ('original', lambda img: img, '原图直接处理'),
            ('enhanced_contrast', lambda img: ImageEnhance.Contrast(img).enhance(1.2), '增强对比度'),
            ('enhanced_sharpness', lambda img: ImageEnhance.Sharpness(img).enhance(1.1), '锐化处理'),
            ('resize_large', lambda img: img.resize((1024, int(img.height * 1024 / img.width)), Image.Resampling.LANCZOS), '放大到1024px')
        ]
        
        results = {}
        session = new_session('isnet-general-use')  # 使用最佳模型
        
        for prep_name, prep_func, description in preprocessing_options:
            try:
                logger.info(f"测试预处理: {prep_name} - {description}")
                
                # 应用预处理
                processed_image = prep_func(original.copy())
                
                # 移除背景
                output_image = remove(processed_image, session=session)
                
                # 保存结果
                output_path = Path(output_dir) / f"{Path(input_path).stem}_prep_{prep_name}.png"
                output_image.save(output_path)
                
                results[prep_name] = {
                    'success': True,
                    'path': str(output_path),
                    'description': description
                }
                
                logger.info(f"✓ {prep_name} 处理完成: {output_path}")
                
            except Exception as e:
                logger.error(f"✗ {prep_name} 处理失败: {e}")
                results[prep_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
        
    except ImportError:
        logger.error("依赖库未安装")
        return None

def test_backgroundremover(input_path, output_path):
    """测试BackgroundRemover"""
    try:
        import subprocess
        
        logger.info("测试BackgroundRemover...")
        
        # 使用命令行调用
        cmd = ['backgroundremover', '-i', input_path, '-o', output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"✓ BackgroundRemover 处理完成: {output_path}")
            return True
        else:
            logger.error(f"✗ BackgroundRemover 失败: {result.stderr}")
            return False
            
    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"BackgroundRemover 不可用: {e}")
        return False

def compare_results(results_dir):
    """比较不同方法的结果"""
    logger.info("\n=== 结果比较 ===")
    
    results_path = Path(results_dir)
    if not results_path.exists():
        logger.error("结果目录不存在")
        return
    
    png_files = list(results_path.glob("*.png"))
    
    if not png_files:
        logger.warning("未找到处理结果")
        return
    
    logger.info(f"找到 {len(png_files)} 个结果文件:")
    
    # 按文件大小排序（通常更大的文件保留了更多细节）
    png_files.sort(key=lambda x: x.stat().st_size, reverse=True)
    
    for i, file in enumerate(png_files, 1):
        size_mb = file.stat().st_size / (1024 * 1024)
        logger.info(f"{i}. {file.name} ({size_mb:.2f} MB)")
    
    logger.info(f"\n推荐查看效果最好的几个文件，通常文件较大的效果更好")
    logger.info("请在图片查看器中打开这些文件进行视觉比较")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python test_script.py <输入图片路径>")
        print("示例: python test_script.py image1.jpg")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        logger.error(f"输入文件不存在: {input_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path("background_removal_test_results")
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"开始测试背景移除工具，输入图片: {input_path}")
    logger.info(f"结果保存到: {output_dir}")
    
    # 测试不同的rembg模型
    logger.info("\n=== 测试Rembg不同模型 ===")
    rembg_results = test_rembg_models(input_path, output_dir)
    
    # 测试预处理
    logger.info("\n=== 测试预处理方法 ===")
    preprocessing_results = test_with_preprocessing(input_path, output_dir)
    
    # 测试BackgroundRemover
    logger.info("\n=== 测试BackgroundRemover ===")
    bg_remover_path = output_dir / f"{Path(input_path).stem}_backgroundremover.png"
    test_backgroundremover(input_path, str(bg_remover_path))
    
    # 比较结果
    compare_results(output_dir)
    
    # 使用建议
    logger.info("\n=== 使用建议 ===")
    logger.info("1. 首选 'isnet-general-use' 模型的结果")
    logger.info("2. 如果边缘不够精细，尝试预处理后的结果")
    logger.info("3. 人像图片可以尝试 'silueta' 模型")
    logger.info("4. 如果所有结果都不理想，考虑使用InSPyReNet或BRIA模型")

if __name__ == "__main__":
    main()