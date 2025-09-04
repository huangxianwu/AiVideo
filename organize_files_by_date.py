#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按日期整理images目录下的文件
根据文件创建日期，将文件移动到对应的日期文件夹中
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def get_file_creation_date(file_path):
    """获取文件创建日期，返回MMDD格式"""
    try:
        # 获取文件的创建时间
        creation_time = os.path.getctime(file_path)
        creation_date = datetime.fromtimestamp(creation_time)
        return creation_date.strftime("%m%d")
    except Exception as e:
        print(f"获取文件创建日期失败 {file_path}: {e}")
        # 如果获取失败，使用当前日期
        return datetime.now().strftime("%m%d")

def organize_files_in_directory(base_dir, subdir_name):
    """整理指定子目录中的文件"""
    subdir_path = Path(base_dir) / subdir_name
    
    if not subdir_path.exists():
        print(f"目录不存在: {subdir_path}")
        return
    
    print(f"\n正在整理 {subdir_name} 目录...")
    
    # 获取所有文件（排除.gitkeep和目录）
    files = [f for f in subdir_path.iterdir() 
             if f.is_file() and f.name != '.gitkeep']
    
    if not files:
        print(f"  {subdir_name} 目录中没有需要整理的文件")
        return
    
    moved_count = 0
    
    for file_path in files:
        try:
            # 获取文件创建日期
            date_folder = get_file_creation_date(file_path)
            
            # 创建日期文件夹
            date_dir = subdir_path / date_folder
            date_dir.mkdir(exist_ok=True)
            
            # 移动文件
            new_path = date_dir / file_path.name
            
            # 如果目标文件已存在，添加序号
            counter = 1
            original_new_path = new_path
            while new_path.exists():
                stem = original_new_path.stem
                suffix = original_new_path.suffix
                new_path = date_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(file_path), str(new_path))
            print(f"  移动: {file_path.name} -> {date_folder}/{new_path.name}")
            moved_count += 1
            
        except Exception as e:
            print(f"  移动文件失败 {file_path.name}: {e}")
    
    print(f"  {subdir_name} 目录整理完成，共移动 {moved_count} 个文件")

def main():
    """主函数"""
    images_dir = Path("images")
    
    if not images_dir.exists():
        print("images目录不存在")
        return
    
    print("开始整理images目录下的文件...")
    print("=" * 50)
    
    # 需要整理的子目录
    subdirs_to_organize = ['jpg', 'png']
    
    for subdir in subdirs_to_organize:
        organize_files_in_directory(images_dir, subdir)
    
    print("\n" + "=" * 50)
    print("文件整理完成！")
    
    # 显示整理后的目录结构
    print("\n整理后的目录结构:")
    for subdir in subdirs_to_organize:
        subdir_path = images_dir / subdir
        if subdir_path.exists():
            print(f"\n{subdir}/")
            for item in sorted(subdir_path.iterdir()):
                if item.is_dir():
                    file_count = len([f for f in item.iterdir() if f.is_file()])
                    print(f"  {item.name}/ ({file_count} 个文件)")
                elif item.name != '.gitkeep':
                    print(f"  {item.name} (未整理)")

if __name__ == "__main__":
    main()