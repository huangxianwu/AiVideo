#!/usr/bin/env python3
"""
非交互式工作流执行器
用于Web界面调用工作流，避免交互式输入
"""

import asyncio
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

from config import load_config
from workflow_processor import WorkflowProcessor
from workflow_manager import WorkflowManager, WorkflowMode
from png_processor import WhiteBackgroundRemover
from main import main_process, generate_workflow_report, setup_logging, process_png_images


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="非交互式工作流执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python workflow_runner.py --workflow image_composition
  python workflow_runner.py --workflow image_to_video
  python workflow_runner.py --workflow full_workflow
  python workflow_runner.py --workflow png_processor
        """
    )
    
    parser.add_argument(
        '--workflow',
        required=True,
        choices=['image_composition', 'image_to_video', 'full_workflow', 'png_processor'],
        help='工作流类型'
    )
    
    parser.add_argument(
        '--retry',
        action='store_true',
        help='重试失败的行'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='最大重试次数 (默认: 3)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式，跳过ComfyUI API调用以加快测试'
    )
    
    return parser.parse_args()


def get_workflow_mode(workflow_type):
    """根据工作流类型获取对应的模式"""
    workflow_mapping = {
        'image_composition': WorkflowMode.IMAGE_COMPOSITION,
        'image_to_video': WorkflowMode.IMAGE_TO_VIDEO,
        'full_workflow': 'FULL_WORKFLOW',
        'png_processor': 'PNG_PROCESSOR'
    }
    return workflow_mapping.get(workflow_type)


def get_workflow_name(workflow_type):
    """获取工作流显示名称"""
    workflow_names = {
        'image_composition': '图片合成工作流',
        'image_to_video': '图生视频工作流',
        'full_workflow': '完整工作流',
        'png_processor': '图片去背景处理'
    }
    return workflow_names.get(workflow_type, workflow_type)


async def main():
    """主函数"""
    args = parse_arguments()
    
    # 确保输出立即刷新
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    try:
        print("="*60)
        print(f"🚀 开始执行{get_workflow_name(args.workflow)}")
        print("="*60)
        sys.stdout.flush()
        
        # 获取工作流模式
        workflow_mode = get_workflow_mode(args.workflow)
        if workflow_mode is None:
            print(f"❌ 不支持的工作流类型: {args.workflow}")
            sys.stdout.flush()
            return 1
        
        # 处理图片去白底模式
        if workflow_mode == "PNG_PROCESSOR":
            print("📋 执行模式: 图片去背景处理")
            sys.stdout.flush()
            success = process_png_images()
            exit_code = 0 if success else 1
        else:
            # 正常执行模式
            if args.retry:
                print("📋 执行模式: 重试失败行")
                print(f"   - 最大重试次数: {args.max_retries}")
            else:
                print("📋 执行模式: 正常处理")
            print(f"   - 日志级别: {args.log_level}")
            print(f"   - 工作流: {get_workflow_name(args.workflow)}")
            sys.stdout.flush()
            
            exit_code = await main_process(args, workflow_mode)
        
        print("="*60)
        if exit_code == 0:
            print("✅ 工作流执行成功")
        else:
            print("❌ 工作流执行失败")
        print("="*60)
        sys.stdout.flush()
            
        return exit_code
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.stdout.flush()
        return 130
    except Exception as e:
        print(f"❌ 程序执行失败: {str(e)}")
        sys.stdout.flush()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)