#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流数据库模块
基于JSON文件的轻量级数据存储系统
用于记录工作流状态、任务ID等数据
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import threading
from pathlib import Path


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    IMAGE_GENERATING = "图片生成中"
    VIDEO_GENERATING = "视频生成中"
    COMPLETED = "已完成"
    FAILED = "失败"
    PENDING = "等待中"


class WorkflowType(Enum):
    """工作流类型枚举"""
    IMAGE_COMPOSITION = "图片合成"
    IMAGE_TO_VIDEO = "图生视频"


class WorkflowDatabase:
    """工作流数据库类"""
    
    def __init__(self, db_file: str = "data/workflow_db.json"):
        """
        初始化数据库
        
        Args:
            db_file: 数据库文件路径
        """
        self.db_file = Path(db_file)
        self._lock = threading.Lock()
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库文件和目录存在"""
        # 创建data目录
        self.db_file.parent.mkdir(exist_ok=True)
        
        # 如果数据库文件不存在，创建初始结构
        if not self.db_file.exists():
            initial_data = {
                "workflows": {},
                "statistics": {
                    "total_tasks": 0,
                    "completed": 0,
                    "image_generating": 0,
                    "video_generating": 0,
                    "failed": 0,
                    "pending": 0
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """加载数据库数据"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"数据库加载失败: {e}")
            return {"workflows": {}, "statistics": {}, "metadata": {}}
    
    def _save_data(self, data: Dict):
        """保存数据到文件"""
        try:
            # 更新最后修改时间
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"数据库保存失败: {e}")
    
    def add_task(self, task_id: str, row_index: int, 
                 product_name: str = "", metadata: Dict = None) -> bool:
        """添加新任务
        
        Args:
            task_id: 任务ID
            row_index: 表格行索引
            product_name: 产品名称
            metadata: 额外元数据
            
        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                # 检查任务是否已存在
                if task_id in data["workflows"]:
                    print(f"任务 {task_id} 已存在")
                    return False
                
                # 创建新任务记录
                task_data = {
                    "task_id": task_id,
                    "status": WorkflowStatus.PENDING.value,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "row_index": row_index,
                    "product_name": product_name,
                    "image_path": None,
                    "video_path": None,
                    "error_message": None,
                    "metadata": metadata or {}
                }
                
                data["workflows"][task_id] = task_data
                
                # 更新统计信息
                data["statistics"]["total_tasks"] += 1
                data["statistics"]["pending"] += 1
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"添加任务失败: {e}")
                return False
    
    def add_workflow_task(self, task_id: str, row_index: int, workflow_type: WorkflowType,
                         product_name: str = "", image_prompt: str = "", 
                         video_prompt: str = "", metadata: Dict = None) -> bool:
        """添加新的工作流任务
        
        Args:
            task_id: 任务ID
            row_index: 表格行索引
            workflow_type: 工作流类型
            product_name: 产品名称
            image_prompt: 图片生成提示词
            video_prompt: 视频生成提示词
            metadata: 额外元数据
            
        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                # 检查任务是否已存在
                if task_id in data["workflows"]:
                    print(f"工作流任务 {task_id} 已存在")
                    return False
                
                # 创建新的工作流任务记录
                task_data = {
                    "task_id": task_id,
                    "workflow_type": workflow_type.value,
                    "status": WorkflowStatus.PENDING.value,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "row_index": row_index,
                    "product_name": product_name,
                    "image_prompt": image_prompt,
                    "video_prompt": video_prompt,
                    "image_path": None,
                    "video_path": None,
                    "error_message": None,
                    "metadata": metadata or {}
                }
                
                data["workflows"][task_id] = task_data
                
                # 更新统计信息
                data["statistics"]["total_tasks"] += 1
                data["statistics"]["pending"] += 1
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"添加工作流任务失败: {e}")
                return False
    
    def update_task_status(self, task_id: str, status: WorkflowStatus, 
                          image_path: str = None, video_path: str = None,
                          error_message: str = None) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            image_path: 图片路径
            video_path: 视频路径
            error_message: 错误信息
            
        Returns:
            bool: 是否更新成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if task_id not in data["workflows"]:
                    print(f"任务 {task_id} 不存在")
                    return False
                
                task = data["workflows"][task_id]
                old_status = task["status"]
                
                # 更新任务信息
                task["status"] = status.value
                task["updated_at"] = datetime.now().isoformat()
                
                if image_path:
                    task["image_path"] = image_path
                if video_path:
                    task["video_path"] = video_path
                if error_message:
                    task["error_message"] = error_message
                
                # 更新统计信息
                self._update_statistics(data, old_status, status.value)
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"更新任务状态失败: {e}")
                return False
    
    def _update_statistics(self, data: Dict, old_status: str, new_status: str):
        """更新统计信息"""
        stats = data["statistics"]
        
        # 减少旧状态计数
        if old_status == WorkflowStatus.PENDING.value:
            stats["pending"] = max(0, stats["pending"] - 1)
        elif old_status == WorkflowStatus.IMAGE_GENERATING.value:
            stats["image_generating"] = max(0, stats["image_generating"] - 1)
        elif old_status == WorkflowStatus.VIDEO_GENERATING.value:
            stats["video_generating"] = max(0, stats["video_generating"] - 1)
        elif old_status == WorkflowStatus.COMPLETED.value:
            stats["completed"] = max(0, stats["completed"] - 1)
        elif old_status == WorkflowStatus.FAILED.value:
            stats["failed"] = max(0, stats["failed"] - 1)
        
        # 增加新状态计数
        if new_status == WorkflowStatus.PENDING.value:
            stats["pending"] += 1
        elif new_status == WorkflowStatus.IMAGE_GENERATING.value:
            stats["image_generating"] += 1
        elif new_status == WorkflowStatus.VIDEO_GENERATING.value:
            stats["video_generating"] += 1
        elif new_status == WorkflowStatus.COMPLETED.value:
            stats["completed"] += 1
        elif new_status == WorkflowStatus.FAILED.value:
            stats["failed"] += 1
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 任务信息，如果不存在返回None
        """
        try:
            data = self._load_data()
            return data["workflows"].get(task_id)
        except Exception as e:
            print(f"获取任务失败: {e}")
            return None
    
    def get_tasks_by_status(self, status: WorkflowStatus) -> List[Dict]:
        """根据状态获取任务列表
        
        Args:
            status: 任务状态
            
        Returns:
            List[Dict]: 任务列表
        """
        try:
            data = self._load_data()
            return [task for task in data["workflows"].values() 
                   if task["status"] == status.value]
        except Exception as e:
            print(f"获取任务列表失败: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            data = self._load_data()
            return data.get("statistics", {})
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    def get_incomplete_tasks(self) -> List[Dict]:
        """获取未完成的任务（用于程序中断后恢复）
        
        Returns:
            List[Dict]: 未完成任务列表
        """
        try:
            data = self._load_data()
            incomplete_statuses = [
                WorkflowStatus.PENDING.value,
                WorkflowStatus.IMAGE_GENERATING.value,
                WorkflowStatus.VIDEO_GENERATING.value
            ]
            return [task for task in data["workflows"].values() 
                   if task["status"] in incomplete_statuses]
        except Exception as e:
            print(f"获取未完成任务失败: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否删除成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if task_id not in data["workflows"]:
                    print(f"任务 {task_id} 不存在")
                    return False
                
                task = data["workflows"][task_id]
                status = task["status"]
                
                # 删除任务
                del data["workflows"][task_id]
                
                # 更新统计信息
                data["statistics"]["total_tasks"] = max(0, data["statistics"]["total_tasks"] - 1)
                if status == WorkflowStatus.PENDING.value:
                    data["statistics"]["pending"] = max(0, data["statistics"]["pending"] - 1)
                elif status == WorkflowStatus.IMAGE_GENERATING.value:
                    data["statistics"]["image_generating"] = max(0, data["statistics"]["image_generating"] - 1)
                elif status == WorkflowStatus.VIDEO_GENERATING.value:
                    data["statistics"]["video_generating"] = max(0, data["statistics"]["video_generating"] - 1)
                elif status == WorkflowStatus.COMPLETED.value:
                    data["statistics"]["completed"] = max(0, data["statistics"]["completed"] - 1)
                elif status == WorkflowStatus.FAILED.value:
                    data["statistics"]["failed"] = max(0, data["statistics"]["failed"] - 1)
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"删除任务失败: {e}")
                return False
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务
        
        Returns:
            int: 清理的任务数量
        """
        with self._lock:
            try:
                data = self._load_data()
                completed_tasks = [task_id for task_id, task in data["workflows"].items() 
                                 if task["status"] == WorkflowStatus.COMPLETED.value]
                
                for task_id in completed_tasks:
                    del data["workflows"][task_id]
                
                # 更新统计信息
                data["statistics"]["total_tasks"] -= len(completed_tasks)
                data["statistics"]["completed"] = 0
                
                self._save_data(data)
                return len(completed_tasks)
                
            except Exception as e:
                print(f"清理已完成任务失败: {e}")
                return 0
    
    def backup_database(self, backup_path: str = None) -> bool:
        """备份数据库
        
        Args:
            backup_path: 备份文件路径，默认为当前时间戳
            
        Returns:
            bool: 是否备份成功
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"data/workflow_db_backup_{timestamp}.json"
            
            data = self._load_data()
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(exist_ok=True)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"数据库备份成功: {backup_path}")
            return True
            
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return False
    
    def get_incomplete_tasks_by_type(self, workflow_type: WorkflowType) -> List[Dict]:
        """按工作流类型获取未完成的任务
        
        Args:
            workflow_type: 工作流类型
            
        Returns:
            List[Dict]: 未完成任务列表
        """
        try:
            data = self._load_data()
            incomplete_statuses = [
                WorkflowStatus.PENDING.value,
                WorkflowStatus.IMAGE_GENERATING.value,
                WorkflowStatus.VIDEO_GENERATING.value
            ]
            return [task for task in data["workflows"].values() 
                   if task["status"] in incomplete_statuses and 
                   task.get("workflow_type") == workflow_type.value]
        except Exception as e:
            print(f"获取未完成任务失败: {e}")
            return []
    
    def update_task_comfyui_id(self, task_id: str, comfyui_task_id: str) -> bool:
        """更新任务的ComfyUI任务ID
        
        Args:
            task_id: 任务ID
            comfyui_task_id: ComfyUI任务ID
            
        Returns:
            bool: 是否更新成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if task_id not in data["workflows"]:
                    print(f"任务 {task_id} 不存在")
                    return False
                
                data["workflows"][task_id]["comfyui_task_id"] = comfyui_task_id
                data["workflows"][task_id]["updated_at"] = datetime.now().isoformat()
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"更新ComfyUI任务ID失败: {e}")
                return False
    
    def update_task_with_files(self, task_id: str, output_files: List[str]) -> bool:
        """更新任务文件信息
        
        Args:
            task_id: 任务ID
            output_files: 输出文件列表
            
        Returns:
            bool: 是否更新成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if task_id not in data["workflows"]:
                    print(f"任务 {task_id} 不存在")
                    return False
                
                task = data["workflows"][task_id]
                task["output_files"] = output_files
                task["updated_at"] = datetime.now().isoformat()
                
                # 根据工作流类型设置相应的路径
                if task.get("workflow_type") == WorkflowType.IMAGE_COMPOSITION.value:
                    task["image_path"] = output_files[0] if output_files else None
                elif task.get("workflow_type") == WorkflowType.IMAGE_TO_VIDEO.value:
                    task["video_path"] = output_files[0] if output_files else None
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"更新任务文件信息失败: {e}")
                return False
    
    def get_workflows(self) -> List[Dict]:
        """获取所有工作流列表
        
        Returns:
            List[Dict]: 工作流列表
        """
        try:
            data = self._load_data()
            workflows = []
            
            # 如果数据中有custom_workflows字段，返回自定义工作流
            if "custom_workflows" in data:
                for workflow_id, workflow_data in data["custom_workflows"].items():
                    workflow_info = {
                        "id": workflow_id,
                        "workflow_id": workflow_id,
                        "workflow_name": workflow_data.get("name", workflow_id),
                        "name": workflow_data.get("name", workflow_id),
                        "description": workflow_data.get("description", ""),
                        "created_at": workflow_data.get("created_at", ""),
                        "updated_at": workflow_data.get("updated_at", ""),
                        "nodes": workflow_data.get("nodes", [])
                    }
                    workflows.append(workflow_info)
            
            return workflows
            
        except Exception as e:
            print(f"获取工作流列表失败: {e}")
            return []
    
    def create_workflow(self, workflow_id: str, name: str, description: str = "") -> bool:
        """创建新工作流
        
        Args:
            workflow_id: 工作流ID
            name: 工作流名称
            description: 工作流描述
            
        Returns:
            bool: 是否创建成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                # 确保custom_workflows字段存在
                if "custom_workflows" not in data:
                    data["custom_workflows"] = {}
                
                # 检查工作流是否已存在
                if workflow_id in data["custom_workflows"]:
                    print(f"工作流 {workflow_id} 已存在")
                    return False
                
                # 创建新工作流
                workflow_data = {
                    "name": name,
                    "description": description,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "nodes": []
                }
                
                data["custom_workflows"][workflow_id] = workflow_data
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"创建工作流失败: {e}")
                return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """获取单个工作流详情
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict: 工作流信息，如果不存在返回None
        """
        try:
            data = self._load_data()
            
            if "custom_workflows" in data and workflow_id in data["custom_workflows"]:
                workflow_data = data["custom_workflows"][workflow_id]
                return {
                    "id": workflow_id,
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_data.get("name", workflow_id),
                    "name": workflow_data.get("name", workflow_id),
                    "description": workflow_data.get("description", ""),
                    "created_at": workflow_data.get("created_at", ""),
                    "updated_at": workflow_data.get("updated_at", ""),
                    "nodes": workflow_data.get("nodes", [])
                }
            
            return None
            
        except Exception as e:
            print(f"获取工作流失败: {e}")
            return None
    
    def update_workflow(self, workflow_id: str, name: str = None, description: str = None) -> bool:
        """更新工作流信息
        
        Args:
            workflow_id: 工作流ID
            name: 新名称（可选）
            description: 新描述（可选）
            
        Returns:
            bool: 是否更新成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if "custom_workflows" not in data or workflow_id not in data["custom_workflows"]:
                    print(f"工作流 {workflow_id} 不存在")
                    return False
                
                workflow_data = data["custom_workflows"][workflow_id]
                
                if name is not None:
                    workflow_data["name"] = name
                if description is not None:
                    workflow_data["description"] = description
                
                workflow_data["updated_at"] = datetime.now().isoformat()
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"更新工作流失败: {e}")
                return False
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否删除成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if "custom_workflows" not in data or workflow_id not in data["custom_workflows"]:
                    print(f"工作流 {workflow_id} 不存在")
                    return False
                
                del data["custom_workflows"][workflow_id]
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"删除工作流失败: {e}")
                return False
    
    def get_workflow_nodes(self, workflow_id: str) -> List[Dict]:
        """获取工作流的节点列表
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            List[Dict]: 节点列表
        """
        try:
            workflow = self.get_workflow(workflow_id)
            if workflow:
                return workflow.get("nodes", [])
            return []
            
        except Exception as e:
            print(f"获取工作流节点失败: {e}")
            return []
    
    def add_workflow_node(self, workflow_id: str, node_id: str, name: str, 
                         node_type: str, description: str = "", 
                         required: bool = True, default_value: Any = None) -> str:
        """向工作流添加节点
        
        Args:
            workflow_id: 工作流ID
            node_id: 节点ID
            name: 节点名称
            node_type: 节点类型
            description: 节点描述
            required: 是否必填
            default_value: 默认值
            
        Returns:
            str: 节点ID
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if "custom_workflows" not in data or workflow_id not in data["custom_workflows"]:
                    raise ValueError(f"工作流 {workflow_id} 不存在")
                
                workflow_data = data["custom_workflows"][workflow_id]
                
                # 创建节点数据
                node_data = {
                    "node_id": node_id,
                    "name": name,
                    "type": node_type,
                    "description": description,
                    "required": required,
                    "default_value": default_value,
                    "created_at": datetime.now().isoformat()
                }
                
                workflow_data["nodes"].append(node_data)
                workflow_data["updated_at"] = datetime.now().isoformat()
                
                self._save_data(data)
                return node_id
                
            except Exception as e:
                print(f"添加工作流节点失败: {e}")
                raise
    
    def delete_workflow_node(self, workflow_id: str, node_id: str) -> bool:
        """删除工作流节点
        
        Args:
            workflow_id: 工作流ID
            node_id: 节点ID
            
        Returns:
            bool: 是否删除成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if "custom_workflows" not in data or workflow_id not in data["custom_workflows"]:
                    print(f"工作流 {workflow_id} 不存在")
                    return False
                
                workflow_data = data["custom_workflows"][workflow_id]
                nodes = workflow_data["nodes"]
                
                # 查找并删除节点
                for i, node in enumerate(nodes):
                    if node.get("id") == node_id or node.get("node_id") == node_id:
                        del nodes[i]
                        workflow_data["updated_at"] = datetime.now().isoformat()
                        self._save_data(data)
                        return True
                
                print(f"节点 {node_id} 不存在")
                return False
                
            except Exception as e:
                print(f"删除工作流节点失败: {e}")
                return False
    
    def clear_workflow_nodes(self, workflow_id: str) -> bool:
        """清空工作流的所有节点
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否清空成功
        """
        with self._lock:
            try:
                data = self._load_data()
                
                if "custom_workflows" not in data or workflow_id not in data["custom_workflows"]:
                    print(f"工作流 {workflow_id} 不存在")
                    return False
                
                workflow_data = data["custom_workflows"][workflow_id]
                workflow_data["nodes"] = []
                workflow_data["updated_at"] = datetime.now().isoformat()
                
                self._save_data(data)
                return True
                
            except Exception as e:
                print(f"清空工作流节点失败: {e}")
                return False