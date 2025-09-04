#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理器
提供工作流和节点的高级管理功能
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from .workflow_database import WorkflowDatabase, WorkflowStatus

class NodeType(Enum):
    """节点类型枚举"""
    TEXT = "text"
    NUMBER = "number"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"

class WorkflowManager:
    """工作流管理器类"""
    
    def __init__(self, db_path: str = None):
        """初始化工作流管理器
        
        Args:
            db_path: 数据库文件路径，默认为data/custom_workflows.json
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'custom_workflows.json')
        
        self.db = WorkflowDatabase(db_path)
    
    # 工作流管理方法
    def create_workflow(self, workflow_id: str, description: str = "") -> str:
        """创建新工作流
        
        Args:
            workflow_id: 工作流ID（用户输入的标识符）
            description: 工作流描述
            
        Returns:
            str: 工作流ID
            
        Raises:
            ValueError: 如果工作流ID已存在
        """
        # 检查工作流ID是否已存在
        existing_workflows = self.db.get_workflows()
        for workflow in existing_workflows:
            if workflow['id'] == workflow_id:
                raise ValueError(f"工作流ID '{workflow_id}' 已存在")
        
        # 使用workflow_id作为name参数传递给数据库
        success = self.db.create_workflow(workflow_id, workflow_id, description)
        if success:
            return workflow_id
        else:
            raise ValueError("创建工作流失败")
    
    def create_workflow_with_name(self, workflow_id: str, name: str, description: str = "") -> str:
        """创建新工作流（支持分离的ID和名称）
        
        Args:
            workflow_id: 工作流ID（用户输入的标识符）
            name: 工作流名称（用户输入的显示名称）
            description: 工作流描述
            
        Returns:
            str: 工作流ID
            
        Raises:
            ValueError: 如果工作流ID已存在
        """
        # 检查工作流ID是否已存在
        existing_workflows = self.db.get_workflows()
        for workflow in existing_workflows:
            if workflow['id'] == workflow_id:
                raise ValueError(f"工作流ID '{workflow_id}' 已存在")
        
        # 使用workflow_id作为标识符，name作为显示名称
        success = self.db.create_workflow(workflow_id, name, description)
        if success:
            return workflow_id
        else:
            raise ValueError("创建工作流失败")
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流详情
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict: 工作流信息，包含节点列表
        """
        workflow = self.db.get_workflow(workflow_id)
        if workflow:
            # 获取工作流的节点
            nodes = self.db.get_workflow_nodes(workflow_id)
            workflow['nodes'] = nodes
        return workflow
    
    def update_workflow(self, workflow_id: str, name: str = None, description: str = None) -> bool:
        """更新工作流信息
        
        Args:
            workflow_id: 工作流ID
            name: 新名称（可选）
            description: 新描述（可选）
            
        Returns:
            bool: 是否更新成功
        """
        # 如果要更新名称，检查是否与其他工作流重名
        if name:
            existing_workflows = self.db.get_workflows()
            for workflow in existing_workflows:
                if workflow['id'] != workflow_id and workflow['name'] == name:
                    raise ValueError(f"工作流名称 '{name}' 已存在")
        
        return self.db.update_workflow(workflow_id, name, description)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.db.delete_workflow(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流列表
        
        Returns:
            List[Dict]: 工作流列表
        """
        workflows = self.db.get_workflows()
        # 为每个工作流添加节点数量信息和workflow_id字段
        for workflow in workflows:
            nodes = self.db.get_workflow_nodes(workflow['id'])
            workflow['node_count'] = len(nodes)
            # 添加workflow_id字段，用于前端显示
            workflow['workflow_id'] = workflow['id']
        return workflows
    
    # 节点管理方法
    def add_node(self, workflow_id: str, name: str, node_type: str, 
                 description: str = "", required: bool = True, 
                 default_value: Any = None) -> str:
        """向工作流添加节点
        
        Args:
            workflow_id: 工作流ID
            name: 节点名称
            node_type: 节点类型（text/image/video/audio/number）
            description: 节点描述
            required: 是否必填
            default_value: 默认值
            
        Returns:
            str: 节点ID
            
        Raises:
            ValueError: 如果工作流不存在或节点类型无效
        """
        # 验证工作流是否存在
        if not self.db.get_workflow(workflow_id):
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        # 验证节点类型
        try:
            NodeType(node_type)
        except ValueError:
            raise ValueError(f"无效的节点类型: {node_type}")
        
        # 生成节点ID
        import uuid
        node_id = str(uuid.uuid4())
        
        # 检查节点ID在该工作流中是否唯一（理论上UUID应该是唯一的，但为了安全起见）
        existing_nodes = self.db.get_workflow_nodes(workflow_id)
        for node in existing_nodes:
            if node['node_id'] == node_id:
                # 如果万一重复，重新生成
                node_id = str(uuid.uuid4())
                break
        
        return self.db.add_workflow_node(workflow_id, node_id, name, node_type, description, required, default_value)
    
    def add_node_with_id(self, workflow_id: str, node_id: str, name: str, node_type: str, 
                        description: str = "", required: bool = True, 
                        default_value: Any = None) -> str:
        """向工作流添加节点（使用指定的节点ID）
        
        Args:
            workflow_id: 工作流ID
            node_id: 指定的节点ID
            name: 节点名称
            node_type: 节点类型（text/image/video/audio/number）
            description: 节点描述
            required: 是否必填
            default_value: 默认值
            
        Returns:
            str: 节点ID
            
        Raises:
            ValueError: 如果工作流不存在或节点类型无效
        """
        # 验证工作流是否存在
        if not self.db.get_workflow(workflow_id):
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        # 验证节点类型
        try:
            NodeType(node_type)
        except ValueError:
            raise ValueError(f"无效的节点类型: {node_type}")
        
        # 检查节点ID在该工作流中是否唯一
        existing_nodes = self.db.get_workflow_nodes(workflow_id)
        for node in existing_nodes:
            if node['node_id'] == node_id:
                raise ValueError(f"节点ID '{node_id}' 在该工作流中已存在")
        
        return self.db.add_workflow_node(workflow_id, node_id, name, node_type, description, required, default_value)
    
    def update_node(self, node_id: str, name: str = None, description: str = None, 
                   required: bool = None, default_value: Any = None) -> bool:
        """更新节点信息
        
        Args:
            node_id: 节点ID
            name: 新名称（可选）
            description: 新描述（可选）
            required: 是否必填（可选）
            default_value: 默认值（可选）
            
        Returns:
            bool: 是否更新成功
        """
        return self.db.update_node(node_id, name, description, required, default_value)
    
    def remove_node(self, workflow_id: str, node_id: str) -> bool:
        """从工作流中移除节点
        
        Args:
            workflow_id: 工作流ID
            node_id: 节点ID
            
        Returns:
            bool: 是否移除成功
        """
        return self.db.remove_node(workflow_id, node_id)
    
    def get_workflow_nodes(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取工作流的所有节点
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            List[Dict]: 节点列表
        """
        return self.db.get_workflow_nodes(workflow_id)
    
    def clear_workflow_nodes(self, workflow_id: str) -> bool:
        """清空工作流的所有节点
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否清空成功
        """
        return self.db.clear_workflow_nodes(workflow_id)
    
    # 工作流执行记录管理
    def create_execution(self, workflow_id: str, input_data: Dict[str, Any]) -> str:
        """创建工作流执行记录
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            
        Returns:
            str: 执行记录ID
            
        Raises:
            ValueError: 如果工作流不存在或输入数据验证失败
        """
        # 验证工作流是否存在
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        # 验证输入数据
        validation_result = self.validate_input_data(workflow_id, input_data)
        if not validation_result['valid']:
            raise ValueError(f"输入数据验证失败: {validation_result['errors']}")
        
        return self.db.create_execution(workflow_id, input_data)
    
    def update_execution_status(self, execution_id: str, status: str, 
                              result_data: Dict[str, Any] = None, 
                              error_message: str = None) -> bool:
        """更新执行记录状态
        
        Args:
            execution_id: 执行记录ID
            status: 新状态（pending/running/completed/failed）
            result_data: 结果数据（可选）
            error_message: 错误信息（可选）
            
        Returns:
            bool: 是否更新成功
        """
        return self.db.update_execution_status(execution_id, status, result_data, error_message)
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行记录详情
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            Dict: 执行记录信息
        """
        return self.db.get_execution(execution_id)
    
    def get_workflow_executions(self, workflow_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取工作流的执行记录
        
        Args:
            workflow_id: 工作流ID
            limit: 返回记录数量限制
            
        Returns:
            List[Dict]: 执行记录列表
        """
        return self.db.get_workflow_executions(workflow_id, limit)
    
    # 数据验证方法
    def validate_input_data(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证工作流输入数据
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            
        Returns:
            Dict: 验证结果 {'valid': bool, 'errors': List[str]}
        """
        errors = []
        nodes = self.db.get_workflow_nodes(workflow_id)
        
        # 检查必填字段
        for node in nodes:
            node_id = node['id']
            node_name = node['name']
            if node['required'] and node_id not in input_data:
                errors.append(f"缺少必填字段: {node_name}")
            
            # 如果提供了数据，验证类型
            if node_id in input_data:
                value = input_data[node_id]
                node_type = node['type']
                
                if node_type == NodeType.NUMBER.value:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"字段 {node_name} 必须是数字")
                elif node_type == NodeType.TEXT.value:
                    if not isinstance(value, str):
                        errors.append(f"字段 {node_name} 必须是文本")
                # 对于文件类型（image/video/audio），这里只做基本检查
                elif node_type in [NodeType.IMAGE.value, NodeType.VIDEO.value, NodeType.AUDIO.value]:
                    if not isinstance(value, str) or not value:
                        errors.append(f"字段 {node_name} 必须提供有效的文件路径")
                elif node_type == NodeType.FILE.value:
                    if not isinstance(value, str) or not value:
                        errors.append(f"字段 {node_name} 必须提供有效的文件路径")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    # 统计方法
    def get_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息
        
        Returns:
            Dict: 统计信息
        """
        workflows = self.db.get_workflows()
        total_workflows = len(workflows)
        total_nodes = 0
        total_executions = 0
        
        for workflow in workflows:
            nodes = self.db.get_workflow_nodes(workflow['id'])
            total_nodes += len(nodes)
            
            executions = self.db.get_workflow_executions(workflow['id'])
            total_executions += len(executions)
        
        return {
            'total_workflows': total_workflows,
            'total_nodes': total_nodes,
            'total_executions': total_executions,
            'workflows': workflows
        }