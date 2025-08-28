#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期工具模块 - 用于按日期组织输出文件
"""

import os
from datetime import datetime
from pathlib import Path


def get_date_folder_path(base_output_dir: str) -> str:
    """
    获取按当前日期组织的输出文件夹路径
    
    Args:
        base_output_dir: 基础输出目录路径
        
    Returns:
        str: 包含日期子文件夹的完整路径
    """
    # 获取当前日期，格式为MMDD（如0828）
    current_date = datetime.now().strftime('%m%d')
    
    # 构建日期文件夹路径
    date_folder_path = os.path.join(base_output_dir, current_date)
    
    # 确保日期文件夹存在
    os.makedirs(date_folder_path, exist_ok=True)
    
    return date_folder_path


def get_date_subfolder_path(base_output_dir: str, subfolder: str) -> str:
    """
    获取按日期组织的子文件夹路径（如img、video等）
    
    Args:
        base_output_dir: 基础输出目录路径
        subfolder: 子文件夹名称（如'img', 'video'）
        
    Returns:
        str: 包含日期和子文件夹的完整路径
    """
    # 先获取日期文件夹路径
    date_folder_path = get_date_folder_path(base_output_dir)
    
    # 构建子文件夹路径
    subfolder_path = os.path.join(date_folder_path, subfolder)
    
    # 确保子文件夹存在
    os.makedirs(subfolder_path, exist_ok=True)
    
    return subfolder_path


def create_date_organized_filepath(base_output_dir: str, subfolder: str, filename: str) -> str:
    """
    创建按日期组织的完整文件路径
    
    Args:
        base_output_dir: 基础输出目录路径
        subfolder: 子文件夹名称（如'img', 'video'）
        filename: 文件名
        
    Returns:
        str: 完整的文件路径
    """
    subfolder_path = get_date_subfolder_path(base_output_dir, subfolder)
    return os.path.join(subfolder_path, filename)