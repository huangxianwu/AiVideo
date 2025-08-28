#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
白底产品图抠图工具
支持批量处理，自动检测白色背景并转换为透明PNG
"""

import cv2
import numpy as np
from PIL import Image
import os
import argparse
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhiteBackgroundRemover:
    def __init__(self):
        # 白色阈值设置，可根据需要调整
        self.white_threshold = 240  # RGB值高于此阈值被认为是白色
        self.tolerance = 15  # 白色容差范围
        
    def detect_white_background(self, image):
        """
        检测图像是否有白色背景
        """
        # 转换为HSV色彩空间进行更准确的白色检测
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 检测白色区域 - HSV中白色的特征
        # H可以是任意值，S很低，V很高
        lower_white = np.array([0, 0, self.white_threshold])
        upper_white = np.array([180, 30, 255])
        
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 检查边缘是否主要是白色（判断是否为白底图片）
        h, w = image.shape[:2]
        edge_pixels = np.concatenate([
            white_mask[0, :],  # 上边缘
            white_mask[-1, :],  # 下边缘
            white_mask[:, 0],  # 左边缘
            white_mask[:, -1]  # 右边缘
        ])
        
        white_edge_ratio = np.sum(edge_pixels > 0) / len(edge_pixels)
        return white_edge_ratio > 0.7, white_mask
    
    def remove_white_background_cv2(self, image):
        """
        使用OpenCV方法移除白色背景
        """
        # 检测白色背景
        has_white_bg, white_mask = self.detect_white_background(image)
        
        if not has_white_bg:
            logger.warning("未检测到明显的白色背景")
        
        # 创建更精确的白色掩码
        # 方法1: RGB阈值
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary_mask = cv2.threshold(gray, self.white_threshold, 255, cv2.THRESH_BINARY)
        
        # 方法2: 颜色容差
        lower_white = np.array([self.white_threshold] * 3)
        upper_white = np.array([255, 255, 255])
        color_mask = cv2.inRange(image, lower_white, upper_white)
        
        # 结合两种方法
        final_mask = cv2.bitwise_or(binary_mask, color_mask)
        
        # 形态学操作，清理掩码
        kernel = np.ones((3, 3), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)
        
        # 边缘平滑处理
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0)
        
        # 转换为4通道BGRA图像
        bgra = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        
        # 反转掩码（白色区域变透明）
        alpha_channel = 255 - final_mask
        bgra[:, :, 3] = alpha_channel
        
        return bgra
    
    def remove_white_background_pil(self, image_path):
        """
        使用PIL方法移除白色背景（备用方法）
        """
        try:
            with Image.open(image_path).convert('RGBA') as img:
                data = np.array(img)
                
                # 创建透明度掩码
                # 白色像素 (R,G,B都接近255) 设为透明
                white_pixels = (
                    (data[:, :, 0] > self.white_threshold) & 
                    (data[:, :, 1] > self.white_threshold) & 
                    (data[:, :, 2] > self.white_threshold)
                )
                
                # 设置透明度
                data[:, :, 3] = np.where(white_pixels, 0, data[:, :, 3])
                
                return Image.fromarray(data, 'RGBA')
        except Exception as e:
            logger.error(f"PIL方法处理失败: {e}")
            return None
    
    def enhance_edges(self, image):
        """
        增强边缘，提高抠图质量
        """
        # 边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 膨胀操作，加强边缘
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # 将边缘信息融入alpha通道
        alpha = image[:, :, 3]
        enhanced_alpha = np.where(edges > 0, 255, alpha)
        image[:, :, 3] = enhanced_alpha
        
        return image
    
    def process_single_image(self, input_path, output_path=None, enhance_edges=True):
        """
        处理单张图片
        """
        try:
            # 读取图像
            image = cv2.imread(input_path)
            if image is None:
                logger.error(f"无法读取图像: {input_path}")
                return False
            
            logger.info(f"处理图像: {input_path}")
            
            # OpenCV方法抠图
            result = self.remove_white_background_cv2(image)
            
            # 可选的边缘增强
            if enhance_edges:
                result = self.enhance_edges(result)
            
            # 设置输出路径
            if output_path is None:
                input_file = Path(input_path)
                output_path = input_file.parent / f"{input_file.stem}_no_bg.png"
            
            # 保存结果
            success = cv2.imwrite(str(output_path), result)
            
            if success:
                logger.info(f"抠图完成: {output_path}")
                
                # 验证输出文件
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                else:
                    logger.error("输出文件异常")
                    return False
            else:
                logger.error("保存失败")
                return False
                
        except Exception as e:
            logger.error(f"处理图像时发生错误: {e}")
            
            # 尝试PIL方法作为备选
            try:
                logger.info("尝试使用PIL方法...")
                result_pil = self.remove_white_background_pil(input_path)
                if result_pil:
                    if output_path is None:
                        input_file = Path(input_path)
                        output_path = input_file.parent / f"{input_file.stem}_no_bg.png"
                    
                    result_pil.save(output_path, 'PNG')
                    logger.info(f"PIL方法处理完成: {output_path}")
                    return True
            except Exception as pil_e:
                logger.error(f"PIL方法也失败了: {pil_e}")
            
            return False
    
    def process_batch(self, input_dir, output_dir=None, supported_formats=None):
        """
        批量处理图片
        """
        if supported_formats is None:
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path / "output"
            output_path.mkdir(exist_ok=True)
        
        # 查找所有支持的图片文件
        image_files = []
        for ext in supported_formats:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.warning(f"在 {input_dir} 中未找到支持的图片文件")
            return
        
        logger.info(f"找到 {len(image_files)} 张图片，开始批量处理...")
        
        success_count = 0
        for img_file in image_files:
            output_file = output_path / f"{img_file.stem}_no_bg.png"
            
            if self.process_single_image(str(img_file), str(output_file)):
                success_count += 1
        
        logger.info(f"批量处理完成！成功处理 {success_count}/{len(image_files)} 张图片")

def main():
    parser = argparse.ArgumentParser(description='白底产品图抠图工具')
    parser.add_argument('input', help='输入图片路径或目录')
    parser.add_argument('-o', '--output', help='输出路径（文件或目录）')
    parser.add_argument('-b', '--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--threshold', type=int, default=240, help='白色检测阈值 (0-255)')
    parser.add_argument('--no-enhance', action='store_true', help='禁用边缘增强')
    
    args = parser.parse_args()
    
    # 创建抠图工具实例
    remover = WhiteBackgroundRemover()
    
    # 设置自定义阈值
    if args.threshold:
        remover.white_threshold = args.threshold
    
    # 处理图片
    if args.batch or os.path.isdir(args.input):
        # 批量处理
        remover.process_batch(args.input, args.output)
    else:
        # 单张图片处理
        enhance = not args.no_enhance
        success = remover.process_single_image(args.input, args.output, enhance)
        if not success:
            exit(1)

if __name__ == "__main__":
    # 如果直接运行脚本，可以在这里测试
    # 或者通过命令行参数运行
    
    # 示例用法：
    # python white_bg_remover.py input.jpg -o output.png
    # python white_bg_remover.py input_folder -b -o output_folder
    
    main()