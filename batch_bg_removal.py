#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量背景移除脚本
使用rembg库批量处理images/jpg文件夹下的图片，去除背景并输出到images/png
"""

import os
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def batch_remove_background(input_dir="images/jpg", output_dir="images/png", model_name="u2net"):
    """
    批量移除背景
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径  
        model_name: rembg模型名称
    
    Returns:
        dict: 处理结果统计
    """
    try:
        from rembg import remove, new_session
        from PIL import Image
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # 检查输入目录
        if not input_path.exists():
            logger.error(f"输入目录不存在: {input_path}")
            return {'success': False, 'error': '输入目录不存在'}
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(input_path.glob(f'*{ext}'))
            image_files.extend(input_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            logger.warning(f"在 {input_path} 中未找到图片文件")
            return {'success': True, 'processed': 0, 'failed': 0, 'message': '未找到图片文件'}
        
        logger.info(f"找到 {len(image_files)} 个图片文件")
        logger.info(f"使用模型: {model_name}")
        
        # 创建rembg会话
        session = new_session(model_name)
        
        # 处理统计
        processed_count = 0
        failed_count = 0
        failed_files = []
        
        # 批量处理
        for i, image_file in enumerate(image_files, 1):
            try:
                logger.info(f"[{i}/{len(image_files)}] 处理: {image_file.name}")
                
                # 读取图片
                input_image = Image.open(image_file)
                
                # 移除背景
                output_image = remove(input_image, session=session)
                
                # 生成输出文件名
                output_file = output_path / f"{image_file.stem}.png"
                
                # 保存结果
                output_image.save(output_file, 'PNG')
                
                # 验证输出文件
                if output_file.exists() and output_file.stat().st_size > 0:
                    processed_count += 1
                    logger.info(f"✓ 处理完成: {output_file.name}")
                    
                    # 删除原始文件
                    image_file.unlink()
                    logger.info(f"✓ 删除原文件: {image_file.name}")
                else:
                    failed_count += 1
                    failed_files.append(image_file.name)
                    logger.error(f"✗ 输出文件异常: {image_file.name}")
                    
            except Exception as e:
                failed_count += 1
                failed_files.append(image_file.name)
                logger.error(f"✗ 处理失败 {image_file.name}: {e}")
        
        # 返回处理结果
        result = {
            'success': True,
            'processed': processed_count,
            'failed': failed_count,
            'total': len(image_files),
            'failed_files': failed_files,
            'output_dir': str(output_path)
        }
        
        logger.info(f"\n=== 处理完成 ===")
        logger.info(f"总文件数: {result['total']}")
        logger.info(f"成功处理: {result['processed']}")
        logger.info(f"处理失败: {result['failed']}")
        logger.info(f"输出目录: {result['output_dir']}")
        
        if failed_files:
            logger.warning(f"失败文件: {', '.join(failed_files)}")
        
        return result
        
    except ImportError:
        error_msg = "Rembg库未安装，请运行: pip install rembg"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f"批量处理过程中出错: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def main():
    """
    主函数
    """
    print("=" * 60)
    print("🖼️ 批量背景移除工具")
    print("=" * 60)
    
    # 可选的模型列表
    available_models = [
        ('u2net', '经典模型，文字处理效果好，推荐首选'),
        ('silueta', '轮廓检测专用，文字边缘清晰'),
        ('isnet-general-use', '高质量通用模型'),
        ('u2netp', '轻量版本，速度快')
    ]
    
    print("可用模型:")
    for i, (model, desc) in enumerate(available_models, 1):
        print(f"{i}. {model} - {desc}")
    
    # 选择模型
    try:
        choice = input("\n请选择模型 (1-4，默认1): ").strip()
        if not choice:
            choice = "1"
        
        model_index = int(choice) - 1
        if 0 <= model_index < len(available_models):
            selected_model = available_models[model_index][0]
        else:
            print("无效选择，使用默认模型")
            selected_model = "u2net"
    except (ValueError, KeyboardInterrupt):
        print("使用默认模型")
        selected_model = "u2net"
    
    print(f"\n使用模型: {selected_model}")
    
    # 执行批量处理
    result = batch_remove_background(model_name=selected_model)
    
    if result['success']:
        print("\n🎉 批量处理完成!")
    else:
        print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")
        sys.exit(1)

if __name__ == "__main__":
    main()