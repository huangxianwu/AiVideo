#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块测试脚本 - 用于验证各个模块的基本功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_config():
    """测试配置模块"""
    logger.info("=== 测试配置模块 ===")
    
    try:
        from config import load_config
        config = load_config()
        
        logger.info(f"飞书配置: App ID = {config.feishu.app_id[:10]}...")
        logger.info(f"ComfyUI配置: API Key = {config.comfyui.api_key[:10]}...")
        logger.info(f"应用配置: 临时目录 = {config.temp_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"配置模块测试失败: {str(e)}")
        return False


async def test_feishu_auth():
    """测试飞书认证"""
    logger.info("=== 测试飞书认证 ===")
    
    try:
        from config import load_config
        from feishu_client import FeishuClient
        
        config = load_config()
        client = FeishuClient(config.feishu)
        
        # 测试获取访问令牌
        token = await client.get_access_token()
        logger.info(f"访问令牌获取成功: {token[:20]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"飞书认证测试失败: {str(e)}")
        return False


async def test_feishu_sheet_info():
    """测试飞书表格信息获取"""
    logger.info("=== 测试飞书表格信息 ===")
    
    try:
        from config import load_config
        from feishu_client import FeishuClient
        
        config = load_config()
        client = FeishuClient(config.feishu)
        
        # 测试获取表格信息
        sheet_info = await client.get_sheet_info()
        logger.info(f"表格信息: {sheet_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"飞书表格信息测试失败: {str(e)}")
        return False


async def test_feishu_data():
    """测试飞书数据获取"""
    logger.info("=== 测试飞书数据获取 ===")
    
    try:
        from config import load_config
        from feishu_client import FeishuClient
        
        config = load_config()
        client = FeishuClient(config.feishu)
        
        # 测试获取表格数据
        rows_data = await client.get_sheet_data()
        logger.info(f"获取到 {len(rows_data)} 行数据")
        
        # 显示前几行数据
        for i, row in enumerate(rows_data[:3]):
            logger.info(f"行 {row.row_number}: 提示词='{row.prompt[:50]}...', 状态='{row.status}'")
        
        return True
        
    except Exception as e:
        logger.error(f"飞书数据获取测试失败: {str(e)}")
        return False


async def test_comfyui_connection():
    """测试ComfyUI连接"""
    logger.info("=== 测试ComfyUI连接 ===")
    
    try:
        from config import load_config
        from comfyui_client import ComfyUIClient
        
        config = load_config()
        client = ComfyUIClient(config.comfyui)
        
        # 创建测试图片数据
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # 测试图片上传
        upload_result = await client.upload_image(test_image_data, "test.png")
        
        if upload_result.success:
            logger.info(f"测试图片上传成功: {upload_result.file_name}")
            return True
        else:
            logger.error(f"测试图片上传失败: {upload_result.error}")
            return False
        
    except Exception as e:
        logger.error(f"ComfyUI连接测试失败: {str(e)}")
        return False


async def test_workflow_processor():
    """测试工作流处理器初始化"""
    logger.info("=== 测试工作流处理器 ===")
    
    try:
        from config import load_config
        from workflow_processor import WorkflowProcessor
        
        config = load_config()
        processor = WorkflowProcessor(config)
        
        logger.info("工作流处理器初始化成功")
        logger.info(f"临时目录: {processor.temp_dir}")
        logger.info(f"输出目录: {processor.output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"工作流处理器测试失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行模块测试...")
    
    tests = [
        ("配置模块", test_config),
        ("飞书认证", test_feishu_auth),
        ("飞书表格信息", test_feishu_sheet_info),
        ("飞书数据获取", test_feishu_data),
        ("ComfyUI连接", test_comfyui_connection),
        ("工作流处理器", test_workflow_processor),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"{test_name}: ❌ 异常 - {str(e)}")
        
        logger.info("-" * 50)
    
    # 汇总结果
    logger.info("\n=== 测试结果汇总 ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.warning(f"⚠️  有 {total - passed} 个测试失败")
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