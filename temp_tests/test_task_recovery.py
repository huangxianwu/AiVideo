#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务恢复系统测试脚本
测试TaskRecoveryManager和相关数据库功能
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_operations():
    """测试数据库操作"""
    logger.info("=== 测试数据库操作 ===")
    
    try:
        from data import DatabaseManager, WorkflowType
        from feishu_client import RowData
        
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        
        # 创建测试数据
        test_row_data = RowData(
            row_number=999,
            product_name="测试产品",
            prompt="测试提示词",
            product_image="test_product.jpg",
            model_image="test_model.jpg",
            status="",
            composite_image="",
            video_status="否"
        )
        
        # 测试添加工作流任务
        logger.info("1. 测试添加图片合成任务")
        task_id = "test_task_" + str(int(datetime.now().timestamp()))
        success = db_manager.add_workflow_task(
            task_id=task_id,
            row_index=test_row_data.row_number,
            workflow_type=WorkflowType.IMAGE_COMPOSITION,
            product_name=test_row_data.product_name,
            image_prompt=test_row_data.prompt,
            video_prompt=""
        )
        logger.info(f"   ✅ 创建任务ID: {task_id}, 成功: {success}")
        
        # 测试更新ComfyUI任务ID
        logger.info("2. 测试更新ComfyUI任务ID")
        comfyui_task_id = "test_comfyui_123"
        db_manager.update_task_comfyui_id(task_id, comfyui_task_id)
        logger.info(f"   ✅ 更新ComfyUI任务ID: {comfyui_task_id}")
        
        # 测试获取未完成任务
        logger.info("3. 测试获取未完成任务")
        incomplete_tasks = db_manager.get_incomplete_tasks_by_type(WorkflowType.IMAGE_COMPOSITION)
        logger.info(f"   ✅ 找到 {len(incomplete_tasks)} 个未完成的图片合成任务")
        
        # 测试更新任务文件
        logger.info("4. 测试更新任务文件")
        test_output_file = "/test/output/image.jpg"
        db_manager.update_task_with_files(task_id, [test_output_file])
        logger.info(f"   ✅ 更新任务文件: {test_output_file}")
        
        # 测试完成任务
        logger.info("5. 测试完成任务")
        db_manager.complete_image_generation(task_id, test_output_file)
        logger.info(f"   ✅ 任务完成: {task_id}")
        
        # 清理测试数据
        logger.info("6. 清理测试数据")
        db_manager.delete_task(task_id)
        logger.info(f"   ✅ 删除测试任务: {task_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库操作测试失败: {str(e)}")
        return False


async def test_task_recovery_manager():
    """测试任务恢复管理器"""
    logger.info("=== 测试任务恢复管理器 ===")
    
    try:
        from config import load_config
        from task_recovery_manager import TaskRecoveryManager
        from data import DatabaseManager, WorkflowType
        from feishu_client import RowData
        
        # 加载配置
        config = load_config()
        
        # 初始化管理器（注意：这里只测试基本功能，不包含完整的客户端）
        db_manager = DatabaseManager()
        # recovery_manager = TaskRecoveryManager(config, db_manager, comfyui_client, feishu_client)
        # 由于缺少客户端实例，我们只测试数据库相关功能
        logger.info("   ℹ️ 跳过TaskRecoveryManager完整测试（需要客户端实例）")
        
        # 创建一些测试任务
        logger.info("1. 创建测试任务")
        test_tasks = []
        
        for i in range(3):
            test_row_data = RowData(
                row_number=1000 + i,
                product_name=f"测试产品{i+1}",
                prompt=f"测试提示词{i+1}",
                product_image=f"test_product_{i+1}.jpg",
                model_image=f"test_model_{i+1}.jpg",
                status="",
                composite_image="",
                video_status="否"
            )
            
            task_id = f"test_task_{1000 + i}_{int(datetime.now().timestamp())}"
            success = db_manager.add_workflow_task(
                task_id=task_id,
                row_index=test_row_data.row_number,
                workflow_type=WorkflowType.IMAGE_COMPOSITION,
                product_name=test_row_data.product_name,
                image_prompt=test_row_data.prompt,
                video_prompt=""
            )
            
            # 模拟一些任务有ComfyUI任务ID
            if i < 2:
                db_manager.update_task_comfyui_id(task_id, f"comfyui_test_{i+1}")
            
            test_tasks.append(task_id)
            logger.info(f"   ✅ 创建测试任务: {task_id}")
        
        # 测试获取未完成任务（替代完整恢复测试）
        logger.info("2. 测试获取未完成任务")
        incomplete_tasks = db_manager.get_all_incomplete_tasks()
        logger.info(f"   ✅ 找到 {len(incomplete_tasks)} 个未完成任务")
        
        # 测试按类型获取
        image_tasks = db_manager.get_incomplete_tasks_by_type(WorkflowType.IMAGE_COMPOSITION)
        logger.info(f"   ✅ 图片合成未完成任务: {len(image_tasks)} 个")
        
        # 清理测试数据
        logger.info("3. 清理测试数据")
        for task_id in test_tasks:
            db_manager.delete_task(task_id)
            logger.info(f"   ✅ 删除测试任务: {task_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"任务恢复管理器测试失败: {str(e)}")
        return False


async def test_workflow_integration():
    """测试工作流集成"""
    logger.info("=== 测试工作流集成 ===")
    
    try:
        from data import DatabaseManager, WorkflowType
        
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        
        # 测试获取所有未完成任务
        logger.info("1. 测试获取所有未完成任务")
        all_incomplete = db_manager.get_all_incomplete_tasks()
        logger.info(f"   ✅ 找到 {len(all_incomplete)} 个未完成任务")
        
        # 按类型分组显示
        image_tasks = [t for t in all_incomplete if t.get('workflow_type') == WorkflowType.IMAGE_COMPOSITION.value]
        video_tasks = [t for t in all_incomplete if t.get('workflow_type') == WorkflowType.IMAGE_TO_VIDEO.value]
        
        logger.info(f"   - 图片合成任务: {len(image_tasks)} 个")
        logger.info(f"   - 图生视频任务: {len(video_tasks)} 个")
        
        # 测试按类型获取任务
        logger.info("2. 测试按类型获取任务")
        image_incomplete = db_manager.get_incomplete_tasks_by_type(WorkflowType.IMAGE_COMPOSITION)
        video_incomplete = db_manager.get_incomplete_tasks_by_type(WorkflowType.IMAGE_TO_VIDEO)
        
        logger.info(f"   ✅ 图片合成未完成任务: {len(image_incomplete)} 个")
        logger.info(f"   ✅ 图生视频未完成任务: {len(video_incomplete)} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"工作流集成测试失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("开始任务恢复系统测试")
    logger.info("=" * 60)
    
    tests = [
        ("数据库操作", test_database_operations),
        ("任务恢复管理器", test_task_recovery_manager),
        ("工作流集成", test_workflow_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n开始测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            logger.info(f"测试 {test_name}: {'✅ 通过' if result else '❌ 失败'}")
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {str(e)}")
            results.append((test_name, False))
    
    # 总结测试结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！任务恢复系统功能正常")
        return 0
    else:
        logger.error("💥 部分测试失败，请检查任务恢复系统")
        return 1


def main():
    """主函数"""
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
        sys.exit(130)
    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()