#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库集成修复
验证 DatabaseManager 方法调用是否正确
"""

import sys
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data import DatabaseManager
from config import load_config

@dataclass
class MockRowData:
    """模拟行数据"""
    row_number: int
    product_name: str = "测试产品"
    composite_image: Optional[Dict] = None
    prompt: Optional[str] = None
    video_status: str = "否"
    
    def __post_init__(self):
        if self.composite_image is None:
            self.composite_image = {
                'type': 'embed-image',
                'fileToken': 'test_token_123'
            }
        if self.prompt is None:
            self.prompt = "测试提示词：镜头平行缓移跟拍，模特自然走路"

def test_database_manager_methods():
    """测试 DatabaseManager 的方法调用"""
    print("🧪 测试数据库管理器方法")
    print("=" * 50)
    
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    
    # 测试数据
    row_data = MockRowData(row_number=999, product_name="测试产品")
    
    print("📋 测试可用方法:")
    methods = [method for method in dir(db_manager) if not method.startswith('_')]
    for method in methods:
        print(f"   ✅ {method}")
    
    print()
    
    # 测试任务ID生成
    print("🔧 测试任务ID生成:")
    task_id = db_manager.generate_task_id(row_data.row_number, row_data.product_name)
    print(f"   生成的任务ID: {task_id}")
    
    print()
    
    # 测试开始图片生成（这是正确的方法）
    print("🎨 测试开始图片生成:")
    metadata = {
        'prompt': row_data.prompt,
        'workflow_type': 'image_composition'
    }
    
    success = db_manager.start_image_generation(
        task_id, 
        row_data.row_number, 
        row_data.product_name, 
        metadata
    )
    
    if success:
        print(f"   ✅ 成功开始图片生成任务: {task_id}")
    else:
        print(f"   ❌ 开始图片生成任务失败: {task_id}")
    
    print()
    
    # 测试获取任务信息
    print("📊 测试获取任务信息:")
    task_info = db_manager.get_task_info(task_id)
    if task_info:
        print(f"   任务ID: {task_info['task_id']}")
        print(f"   状态: {task_info['status']}")
        print(f"   产品名称: {task_info['product_name']}")
        print(f"   行索引: {task_info['row_index']}")
        print(f"   创建时间: {task_info['created_at']}")
    else:
        print(f"   ❌ 未找到任务信息: {task_id}")
    
    print()
    
    # 测试完成图片生成
    print("🖼️ 测试完成图片生成:")
    image_path = "./output/test/img/test_image.png"
    success = db_manager.complete_image_generation(task_id, image_path)
    if success:
        print(f"   ✅ 成功完成图片生成: {image_path}")
    else:
        print(f"   ❌ 完成图片生成失败")
    
    print()
    
    # 测试开始视频生成
    print("🎬 测试开始视频生成:")
    success = db_manager.start_video_generation(task_id)
    if success:
        print(f"   ✅ 成功开始视频生成")
    else:
        print(f"   ❌ 开始视频生成失败")
    
    print()
    
    # 测试完成视频生成
    print("📹 测试完成视频生成:")
    video_path = "./output/test/video/test_video.mp4"
    success = db_manager.complete_video_generation(task_id, video_path)
    if success:
        print(f"   ✅ 成功完成视频生成: {video_path}")
    else:
        print(f"   ❌ 完成视频生成失败")
    
    print()
    
    # 测试获取统计信息
    print("📈 测试获取统计信息:")
    stats = db_manager.get_dashboard_stats()
    print(f"   总任务数: {stats['total_tasks']}")
    print(f"   已完成: {stats['completed']}")
    print(f"   完成率: {stats['completion_rate']}%")
    print(f"   进行中: {stats['in_progress']}")
    print(f"   失败: {stats['failed']}")
    
    print()
    
    # 测试清理（删除测试任务）
    print("🧹 清理测试数据:")
    # 注意：这里我们不删除任务，因为 DatabaseManager 没有提供删除方法
    # 这是为了保持数据的完整性
    print("   测试任务将保留在数据库中作为测试记录")
    
    print()
    print("=" * 50)
    print("✅ 数据库管理器方法测试完成")

def test_workflow_manager_integration():
    """测试工作流管理器集成"""
    print("\n🔗 测试工作流管理器集成")
    print("=" * 50)
    
    try:
        from workflow_manager import WorkflowManager
        from feishu_client import RowData
        
        # 加载配置
        config = load_config()
        
        # 初始化工作流管理器
        workflow_manager = WorkflowManager(config, debug_mode=True)
        
        print("✅ 工作流管理器初始化成功")
        print(f"   数据库管理器类型: {type(workflow_manager.db_manager)}")
        
        # 检查数据库管理器的方法
        db_manager = workflow_manager.db_manager
        
        # 验证关键方法存在
        required_methods = [
            'start_image_generation',
            'complete_image_generation', 
            'start_video_generation',
            'complete_video_generation',
            'mark_task_failed',
            'generate_task_id',
            'get_task_info'
        ]
        
        print("\n📋 验证必需方法:")
        for method_name in required_methods:
            if hasattr(db_manager, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} - 缺失！")
        
        # 验证不应该存在的方法
        print("\n🚫 验证不应存在的方法:")
        if hasattr(db_manager, 'add_task'):
            print("   ❌ add_task - 不应该直接调用！")
        else:
            print("   ✅ add_task - 正确，不应直接调用")
        
    except Exception as e:
        print(f"❌ 工作流管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=" * 50)
    print("✅ 工作流管理器集成测试完成")

if __name__ == "__main__":
    print("🔧 数据库集成修复验证")
    print("=" * 60)
    
    # 测试数据库管理器方法
    test_database_manager_methods()
    
    # 测试工作流管理器集成
    test_workflow_manager_integration()
    
    print("\n🎉 所有测试完成！")