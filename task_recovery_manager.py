#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务恢复管理器
负责处理程序中断后的任务恢复逻辑
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import AppConfig
from comfyui_client import ComfyUIClient
from data.database_manager import DatabaseManager
from data.workflow_database import WorkflowType, WorkflowStatus
from feishu_client import FeishuClient, RowData


class TaskRecoveryManager:
    """任务恢复管理器"""
    
    def __init__(self, config: AppConfig, db_manager: DatabaseManager, 
                 comfyui_client: ComfyUIClient, feishu_client: FeishuClient):
        """
        初始化任务恢复管理器
        
        Args:
            config: 应用配置
            db_manager: 数据库管理器
            comfyui_client: ComfyUI客户端
            feishu_client: 飞书客户端
        """
        self.config = config
        self.db_manager = db_manager
        self.comfyui_client = comfyui_client
        self.feishu_client = feishu_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def check_and_recover_tasks(self) -> Dict[str, int]:
        """
        检查并恢复未完成的任务
        
        Returns:
            Dict[str, int]: 恢复统计信息
        """
        self.logger.info("开始检查未完成的任务...")
        
        # 获取所有未完成的任务
        incomplete_tasks = self.db_manager.get_all_incomplete_tasks()
        
        if not incomplete_tasks:
            self.logger.info("没有发现未完成的任务")
            return {"total": 0, "recovered": 0, "failed": 0, "skipped": 0}
        
        self.logger.info(f"发现 {len(incomplete_tasks)} 个未完成的任务")
        
        # 统计信息
        stats = {"total": len(incomplete_tasks), "recovered": 0, "failed": 0, "skipped": 0}
        
        # 按工作流类型分组处理
        image_tasks = [t for t in incomplete_tasks if t.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value]
        video_tasks = [t for t in incomplete_tasks if t.get('workflow_type') == WorkflowType.IMAGE_TO_VIDEO.value]
        
        # 恢复图片合成任务
        if image_tasks:
            self.logger.info(f"恢复 {len(image_tasks)} 个图片合成任务")
            image_stats = await self._recover_image_composition_tasks(image_tasks)
            stats["recovered"] += image_stats["recovered"]
            stats["failed"] += image_stats["failed"]
            stats["skipped"] += image_stats["skipped"]
        
        # 恢复图生视频任务
        if video_tasks:
            self.logger.info(f"恢复 {len(video_tasks)} 个图生视频任务")
            video_stats = await self._recover_image_to_video_tasks(video_tasks)
            stats["recovered"] += video_stats["recovered"]
            stats["failed"] += video_stats["failed"]
            stats["skipped"] += video_stats["skipped"]
        
        self.logger.info(f"任务恢复完成: 总计 {stats['total']}, 恢复 {stats['recovered']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
        return stats
    
    async def _recover_image_composition_tasks(self, tasks: List[Dict]) -> Dict[str, int]:
        """
        恢复图片合成任务
        
        Args:
            tasks: 图片合成任务列表
            
        Returns:
            Dict[str, int]: 恢复统计信息
        """
        stats = {"recovered": 0, "failed": 0, "skipped": 0}
        
        for task in tasks:
            task_id = task['task_id']
            status = task['status']
            
            try:
                if status == WorkflowStatus.PENDING.value:
                    # 重新开始图片生成
                    await self._restart_image_generation(task)
                    stats["recovered"] += 1
                    
                elif status == WorkflowStatus.IMAGE_GENERATING.value:
                    # 检查ComfyUI任务状态
                    recovery_result = await self._check_and_recover_comfyui_task(task)
                    if recovery_result == "recovered":
                        stats["recovered"] += 1
                    elif recovery_result == "failed":
                        stats["failed"] += 1
                    else:
                        stats["skipped"] += 1
                        
                else:
                    self.logger.warning(f"未知状态的图片合成任务: {task_id}, 状态: {status}")
                    stats["skipped"] += 1
                    
            except Exception as e:
                self.logger.error(f"恢复图片合成任务失败 {task_id}: {e}")
                self.db_manager.mark_task_failed(task_id, f"恢复失败: {str(e)}")
                stats["failed"] += 1
        
        return stats
    
    async def _recover_image_to_video_tasks(self, tasks: List[Dict]) -> Dict[str, int]:
        """
        恢复图生视频任务
        
        Args:
            tasks: 图生视频任务列表
            
        Returns:
            Dict[str, int]: 恢复统计信息
        """
        stats = {"recovered": 0, "failed": 0, "skipped": 0}
        
        for task in tasks:
            task_id = task['task_id']
            status = task['status']
            
            try:
                if status == WorkflowStatus.PENDING.value:
                    # 重新开始视频生成
                    await self._restart_video_generation(task)
                    stats["recovered"] += 1
                    
                elif status == WorkflowStatus.VIDEO_GENERATING.value:
                    # 检查ComfyUI任务状态
                    recovery_result = await self._check_and_recover_comfyui_task(task)
                    if recovery_result == "recovered":
                        stats["recovered"] += 1
                    elif recovery_result == "failed":
                        stats["failed"] += 1
                    else:
                        stats["skipped"] += 1
                        
                else:
                    self.logger.warning(f"未知状态的图生视频任务: {task_id}, 状态: {status}")
                    stats["skipped"] += 1
                    
            except Exception as e:
                self.logger.error(f"恢复图生视频任务失败 {task_id}: {e}")
                self.db_manager.mark_task_failed(task_id, f"恢复失败: {str(e)}")
                stats["failed"] += 1
        
        return stats
    
    async def _restart_image_generation(self, task: Dict) -> None:
        """
        重新开始图片生成任务
        
        Args:
            task: 任务信息
        """
        task_id = task['task_id']
        self.logger.info(f"重新开始图片生成任务: {task_id}")
        
        # 构建RowData对象
        row_data = self._build_row_data_from_task(task)
        
        # 重新提交到ComfyUI
        workflow_data = self._build_image_workflow_data(task)
        comfyui_task_id = await self.comfyui_client.submit_workflow(workflow_data)
        
        if comfyui_task_id:
            # 更新数据库状态
            self.db_manager.update_task_status(task_id, WorkflowStatus.IMAGE_GENERATING)
            self.db_manager.update_task_comfyui_id(task_id, comfyui_task_id)
            self.logger.info(f"图片生成任务重新提交成功: {task_id} -> {comfyui_task_id}")
        else:
            raise Exception("重新提交ComfyUI任务失败")
    
    async def _restart_video_generation(self, task: Dict) -> None:
        """
        重新开始视频生成任务
        
        Args:
            task: 任务信息
        """
        task_id = task['task_id']
        self.logger.info(f"重新开始视频生成任务: {task_id}")
        
        # 检查是否有图片路径
        image_path = task.get('image_path')
        if not image_path:
            raise Exception("缺少图片路径，无法开始视频生成")
        
        # 重新提交到ComfyUI
        workflow_data = self._build_video_workflow_data(task)
        comfyui_task_id = await self.comfyui_client.submit_workflow(workflow_data)
        
        if comfyui_task_id:
            # 更新数据库状态
            self.db_manager.update_task_status(task_id, WorkflowStatus.VIDEO_GENERATING)
            self.db_manager.update_task_comfyui_id(task_id, comfyui_task_id)
            self.logger.info(f"视频生成任务重新提交成功: {task_id} -> {comfyui_task_id}")
        else:
            raise Exception("重新提交ComfyUI任务失败")
    
    async def _check_and_recover_comfyui_task(self, task: Dict) -> str:
        """
        检查并恢复ComfyUI任务
        
        Args:
            task: 任务信息
            
        Returns:
            str: 恢复结果 ("recovered", "failed", "skipped")
        """
        task_id = task['task_id']
        comfyui_task_id = task.get('comfyui_task_id')
        
        if not comfyui_task_id:
            self.logger.warning(f"任务 {task_id} 缺少ComfyUI任务ID，重新提交")
            # 重新提交任务
            if task.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value:
                await self._restart_image_generation(task)
            else:
                await self._restart_video_generation(task)
            return "recovered"
        
        # 检查ComfyUI任务状态
        try:
            comfyui_status = await self.comfyui_client.get_task_status(comfyui_task_id)
            
            if comfyui_status == "completed":
                # 任务已完成，获取结果
                output_files = await self.comfyui_client.get_task_results(comfyui_task_id)
                if output_files:
                    self.db_manager.update_task_with_files(task_id, output_files)
                    
                    # 更新任务状态
                    if task.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value:
                        self.db_manager.complete_image_generation(task_id, output_files[0])
                    else:
                        self.db_manager.complete_video_generation(task_id, output_files[0])
                    
                    self.logger.info(f"任务 {task_id} 已完成，状态已同步")
                    return "recovered"
                else:
                    self.logger.error(f"任务 {task_id} 完成但无输出文件")
                    self.db_manager.mark_task_failed(task_id, "ComfyUI任务完成但无输出文件")
                    return "failed"
                    
            elif comfyui_status == "failed":
                # 任务失败
                error_msg = await self.comfyui_client.get_task_error(comfyui_task_id)
                self.db_manager.mark_task_failed(task_id, f"ComfyUI任务失败: {error_msg}")
                self.logger.error(f"任务 {task_id} 在ComfyUI中失败: {error_msg}")
                return "failed"
                
            elif comfyui_status == "running":
                # 任务仍在运行，保持现状
                self.logger.info(f"任务 {task_id} 仍在ComfyUI中运行")
                return "skipped"
                
            else:
                # 未知状态，重新提交
                self.logger.warning(f"任务 {task_id} 在ComfyUI中状态未知: {comfyui_status}，重新提交")
                if task.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value:
                    await self._restart_image_generation(task)
                else:
                    await self._restart_video_generation(task)
                return "recovered"
                
        except Exception as e:
            self.logger.error(f"检查ComfyUI任务状态失败 {task_id}: {e}")
            # 重新提交任务
            if task.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value:
                await self._restart_image_generation(task)
            else:
                await self._restart_video_generation(task)
            return "recovered"
    
    def _build_row_data_from_task(self, task: Dict) -> RowData:
        """
        从任务信息构建RowData对象
        
        Args:
            task: 任务信息
            
        Returns:
            RowData: 行数据对象
        """
        metadata = task.get('metadata', {})
        
        return RowData(
            row_number=task['row_index'],
            product_name=task.get('product_name', ''),
            prompt=metadata.get('image_prompt', ''),
            video_prompt=metadata.get('video_prompt', ''),
            model_name=metadata.get('model_name', ''),
            additional_data=metadata
        )
    
    def _build_image_workflow_data(self, task: Dict) -> Dict:
        """
        构建图片生成工作流数据
        
        Args:
            task: 任务信息
            
        Returns:
            Dict: 工作流数据
        """
        metadata = task.get('metadata', {})
        
        return {
            "prompt": metadata.get('image_prompt', ''),
            "model_name": metadata.get('model_name', ''),
            "task_id": task['task_id'],
            "workflow_type": "image_composition"
        }
    
    def _build_video_workflow_data(self, task: Dict) -> Dict:
        """
        构建视频生成工作流数据
        
        Args:
            task: 任务信息
            
        Returns:
            Dict: 工作流数据
        """
        metadata = task.get('metadata', {})
        
        return {
            "image_path": task.get('image_path'),
            "video_prompt": metadata.get('video_prompt', ''),
            "task_id": task['task_id'],
            "workflow_type": "image_to_video"
        }
    
    def get_recovery_summary(self) -> Dict:
        """
        获取恢复摘要信息
        
        Returns:
            Dict: 恢复摘要
        """
        incomplete_tasks = self.db_manager.get_all_incomplete_tasks()
        
        summary = {
            "total_incomplete": len(incomplete_tasks),
            "by_type": {},
            "by_status": {},
            "oldest_task": None,
            "newest_task": None
        }
        
        if incomplete_tasks:
            # 按类型统计
            for task in incomplete_tasks:
                workflow_type = task.get('workflow_type', 'unknown')
                summary["by_type"][workflow_type] = summary["by_type"].get(workflow_type, 0) + 1
                
                status = task.get('status', 'unknown')
                summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # 找到最老和最新的任务
            sorted_tasks = sorted(incomplete_tasks, key=lambda x: x.get('created_at', ''))
            summary["oldest_task"] = {
                "task_id": sorted_tasks[0]['task_id'],
                "created_at": sorted_tasks[0].get('created_at'),
                "status": sorted_tasks[0].get('status')
            }
            summary["newest_task"] = {
                "task_id": sorted_tasks[-1]['task_id'],
                "created_at": sorted_tasks[-1].get('created_at'),
                "status": sorted_tasks[-1].get('status')
            }
        
        return summary