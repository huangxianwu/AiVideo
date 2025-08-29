#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
提供高级数据库操作接口
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .workflow_database import WorkflowDatabase, WorkflowStatus, WorkflowType


class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_file: str = "data/workflow_db.json"):
        """
        初始化数据库管理器
        
        Args:
            db_file: 数据库文件路径
        """
        self.db = WorkflowDatabase(db_file)
    
    def start_image_generation(self, task_id: str, row_index: int, 
                              product_name: str = "", metadata: Dict = None) -> bool:
        """开始图片生成
        
        Args:
            task_id: 任务ID
            row_index: 表格行索引
            product_name: 产品名称
            metadata: 额外元数据
            
        Returns:
            bool: 是否成功
        """
        # 添加任务
        if self.db.add_task(task_id, row_index, product_name, metadata):
            # 更新状态为图片生成中
            return self.db.update_task_status(task_id, WorkflowStatus.IMAGE_GENERATING)
        return False
    
    def complete_image_generation(self, task_id: str, image_path: str) -> bool:
        """完成图片生成
        
        Args:
            task_id: 任务ID
            image_path: 图片路径
            
        Returns:
            bool: 是否成功
        """
        return self.db.update_task_status(
            task_id, 
            WorkflowStatus.VIDEO_GENERATING, 
            image_path=image_path
        )
    
    def start_video_generation(self, task_id: str) -> bool:
        """开始视频生成
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        return self.db.update_task_status(task_id, WorkflowStatus.VIDEO_GENERATING)
    
    def complete_video_generation(self, task_id: str, video_path: str) -> bool:
        """完成视频生成
        
        Args:
            task_id: 任务ID
            video_path: 视频路径
            
        Returns:
            bool: 是否成功
        """
        return self.db.update_task_status(
            task_id, 
            WorkflowStatus.COMPLETED, 
            video_path=video_path
        )
    
    def mark_task_failed(self, task_id: str, error_message: str) -> bool:
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            bool: 是否成功
        """
        return self.db.update_task_status(
            task_id, 
            WorkflowStatus.FAILED, 
            error_message=error_message
        )
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 任务信息
        """
        return self.db.get_task(task_id)
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取等待中的任务
        
        Returns:
            List[Dict]: 等待任务列表
        """
        return self.db.get_tasks_by_status(WorkflowStatus.PENDING)
    
    def get_image_generating_tasks(self) -> List[Dict]:
        """获取图片生成中的任务
        
        Returns:
            List[Dict]: 图片生成任务列表
        """
        return self.db.get_tasks_by_status(WorkflowStatus.IMAGE_GENERATING)
    
    def get_video_generating_tasks(self) -> List[Dict]:
        """获取视频生成中的任务
        
        Returns:
            List[Dict]: 视频生成任务列表
        """
        return self.db.get_tasks_by_status(WorkflowStatus.VIDEO_GENERATING)
    
    def get_completed_tasks(self) -> List[Dict]:
        """获取已完成的任务
        
        Returns:
            List[Dict]: 已完成任务列表
        """
        return self.db.get_tasks_by_status(WorkflowStatus.COMPLETED)
    
    def get_failed_tasks(self) -> List[Dict]:
        """获取失败的任务
        
        Returns:
            List[Dict]: 失败任务列表
        """
        return self.db.get_tasks_by_status(WorkflowStatus.FAILED)
    
    def get_recovery_tasks(self) -> List[Dict]:
        """获取需要恢复的任务（程序中断后使用）
        
        Returns:
            List[Dict]: 需要恢复的任务列表
        """
        return self.db.get_incomplete_tasks()
    
    def get_dashboard_stats(self) -> Dict:
        """获取仪表板统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = self.db.get_statistics()
        
        # 添加额外的统计信息
        total = stats.get('total_tasks', 0)
        completed = stats.get('completed', 0)
        
        if total > 0:
            completion_rate = (completed / total) * 100
        else:
            completion_rate = 0
        
        stats['completion_rate'] = round(completion_rate, 2)
        stats['in_progress'] = (
            stats.get('image_generating', 0) + 
            stats.get('video_generating', 0)
        )
        
        return stats
    
    def cleanup_old_completed_tasks(self, days: int = 7) -> int:
        """清理旧的已完成任务
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的任务数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            completed_tasks = self.get_completed_tasks()
            
            cleaned_count = 0
            for task in completed_tasks:
                updated_at = datetime.fromisoformat(task['updated_at'])
                if updated_at < cutoff_date:
                    if self.db.delete_task(task['task_id']):
                        cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"清理旧任务失败: {e}")
            return 0
    
    def export_tasks_to_csv(self, output_file: str = None) -> bool:
        """导出任务到CSV文件
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import csv
            
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"data/tasks_export_{timestamp}.csv"
            
            # 获取所有任务
            all_tasks = []
            for status in WorkflowStatus:
                tasks = self.db.get_tasks_by_status(status)
                all_tasks.extend(tasks)
            
            if not all_tasks:
                print("没有任务可导出")
                return False
            
            # 写入CSV文件
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'task_id', 'status', 'created_at', 'updated_at', 
                    'row_index', 'product_name', 'image_path', 'video_path', 
                    'error_message'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for task in all_tasks:
                    # 只写入基本字段，忽略metadata
                    row = {field: task.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            print(f"任务导出成功: {output_file}")
            return True
            
        except Exception as e:
            print(f"导出任务失败: {e}")
            return False
    
    def generate_task_id(self, row_index: int, product_name: str = "") -> str:
        """生成任务ID
        
        Args:
            row_index: 表格行索引
            product_name: 产品名称
            
        Returns:
            str: 任务ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if product_name:
            # 清理产品名称，只保留字母数字
            clean_name = ''.join(c for c in product_name if c.isalnum())[:10]
            return f"task_{row_index}_{clean_name}_{timestamp}"
        else:
            return f"task_{row_index}_{timestamp}"
    
    def backup_database(self, backup_path: str = None) -> bool:
        """备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        return self.db.backup_database(backup_path)
    
    def get_task_by_row_index(self, row_index: int) -> Optional[Dict]:
        """根据行索引获取任务
        
        Args:
            row_index: 表格行索引
            
        Returns:
            Dict: 任务信息，如果不存在返回None
        """
        try:
            data = self.db._load_data()
            for task in data["workflows"].values():
                if task.get("row_index") == row_index:
                    return task
            return None
        except Exception as e:
            print(f"根据行索引获取任务失败: {e}")
            return None
    
    def is_task_exists(self, task_id: str) -> bool:
        """检查任务是否存在
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否存在
        """
        return self.get_task_info(task_id) is not None
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 任务状态，如果不存在返回None
        """
        task = self.get_task_info(task_id)
        return task.get('status') if task else None
    
    # ===== 任务恢复相关方法 =====
    
    def add_workflow_task(self, task_id: str, row_index: int, workflow_type: WorkflowType,
                         product_name: str = "", image_prompt: str = "", 
                         video_prompt: str = "", metadata: Dict = None) -> bool:
        """添加工作流任务记录
        
        Args:
            task_id: 任务ID
            row_index: 表格行索引
            workflow_type: 工作流类型
            product_name: 产品名称
            image_prompt: 图片提示词
            video_prompt: 视频提示词
            metadata: 额外元数据
            
        Returns:
            bool: 是否成功
        """
        return self.db.add_workflow_task(
            task_id, row_index, workflow_type, product_name,
            image_prompt, video_prompt, metadata
        )
    
    def get_incomplete_tasks_by_type(self, workflow_type: WorkflowType) -> List[Dict]:
        """按工作流类型获取未完成的任务
        
        Args:
            workflow_type: 工作流类型
            
        Returns:
            List[Dict]: 未完成任务列表
        """
        return self.db.get_incomplete_tasks_by_type(workflow_type)
    
    def update_task_comfyui_id(self, task_id: str, comfyui_task_id: str) -> bool:
        """更新任务的ComfyUI任务ID
        
        Args:
            task_id: 任务ID
            comfyui_task_id: ComfyUI任务ID
            
        Returns:
            bool: 是否更新成功
        """
        return self.db.update_task_comfyui_id(task_id, comfyui_task_id)
    
    def update_task_with_files(self, task_id: str, output_files: List[str]) -> bool:
        """更新任务文件信息
        
        Args:
            task_id: 任务ID
            output_files: 输出文件列表
            
        Returns:
            bool: 是否更新成功
        """
        return self.db.update_task_with_files(task_id, output_files)
    
    def get_all_incomplete_tasks(self) -> List[Dict]:
        """获取所有未完成的任务（用于启动时恢复检查）
        
        Returns:
            List[Dict]: 所有未完成任务列表
        """
        return self.db.get_incomplete_tasks()
    
    def check_comfyui_task_status(self, task_id: str) -> Optional[str]:
        """检查任务的ComfyUI状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: ComfyUI任务ID，如果不存在返回None
        """
        task = self.get_task_info(task_id)
        return task.get('comfyui_task_id') if task else None
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.db.delete_task(task_id)