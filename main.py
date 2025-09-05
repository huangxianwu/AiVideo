#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口 - 飞书表格数据处理ComfyUI工作流
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
# 移除了temp_tests.batch_bg_removal导入，使用本地WhiteBackgroundRemover替代


def select_workflow_mode():
    """让用户选择工作流模式"""
    print("\n" + "="*60)
    print("🔧 请选择工作流模式:")
    print("="*60)
    print("0. 图片去背景处理 - 使用AI模型批量移除图片背景")
    print("1. 图片合成工作流 - 合成产品图和模特图")
    print("2. 图生视频工作流 - 基于合成图生成视频")
    print("3. 完整工作流 - 先完成所有图片合成，再完成所有图生视频")
    print("="*60)
    
    while True:
        try:
            choice = input("请输入选择 (0、1、2 或 3): ").strip()
            if choice == "0":
                print("✅ 已选择: 图片去背景处理")
                return "PNG_PROCESSOR"
            elif choice == "1":
                print("✅ 已选择: 图片合成工作流")
                return WorkflowMode.IMAGE_COMPOSITION
            elif choice == "2":
                print("✅ 已选择: 图生视频工作流")
                return WorkflowMode.IMAGE_TO_VIDEO
            elif choice == "3":
                print("✅ 已选择: 完整工作流")
                return "FULL_WORKFLOW"
            else:
                print("❌ 无效选择，请输入 0、1、2 或 3")
        except KeyboardInterrupt:
            print("\n❌ 用户取消选择")
            sys.exit(130)
        except Exception as e:
            print(f"❌ 输入错误: {str(e)}")


def process_png_images():
    """处理图片去背景功能"""
    try:
        print("\n" + "="*60)
        print("🖼️ 开始批量处理图片去背景")
        print("="*60)
        
        # 可选的模型列表
        available_models = [
            ('isnet-general-use', '高质量通用模型，推荐首选'),
            ('u2net', '经典模型，人像效果好'),
            ('u2netp', '轻量版本，速度快'),
            ('silueta', '人像专用模型')
        ]
        
        print("可用背景移除模型:")
        for i, (model, desc) in enumerate(available_models, 1):
            print(f"{i}. {model} - {desc}")
        
        # 选择模型
        try:
            choice = input("\n请选择模型 (1-4，默认1): ").strip()
            if not choice:
                choice = "1"
            
            model_index = int(choice) - 1
            if 0 <= model_index < len(available_models):
                selected_model = available_models[model_index][0]
                model_desc = available_models[model_index][1]
            else:
                print("无效选择，使用默认模型")
                selected_model = "isnet-general-use"
                model_desc = "高质量通用模型，推荐首选"
        except (ValueError, KeyboardInterrupt):
            print("使用默认模型")
            selected_model = "isnet-general-use"
            model_desc = "高质量通用模型，推荐首选"
        
        print(f"\n✅ 使用模型: {selected_model} - {model_desc}")
        
        # 使用本地WhiteBackgroundRemover进行批量背景移除
        remover = WhiteBackgroundRemover()
        
        print("\n" + "="*60)
        print(f"🎉 开始批量处理图片背景移除...")
        print(f"   - 输入目录: images/jpg")
        print(f"   - 输出目录: images/png")
        print(f"   - 使用模型: {selected_model} (注: 当前使用本地算法处理)")
        print("="*60)
        
        # 执行批量处理
        remover.process_batch(
            input_dir="images/jpg",
            output_dir="images/png"
        )
        
        print("\n" + "="*60)
        print(f"🎉 批量处理完成!")
        print(f"   - 输出目录: images/png")
        print(f"   - 详细信息请查看上方日志输出")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"❌ 图片处理过程中出错: {str(e)}")
        return False


def generate_workflow_report(results, workflow_name: str) -> str:
    """生成工作流处理报告"""
    total_rows = len(results)
    successful_rows = sum(1 for r in results if r.success)
    failed_rows = total_rows - successful_rows
    
    # 统计跳过的行（error包含"跳过"的成功结果）
    skipped_rows = [r for r in results if r.success and r.error and "跳过" in r.error]
    actual_processed_rows = successful_rows - len(skipped_rows)
    
    total_time = sum(r.processing_time or 0 for r in results)
    avg_time = total_time / total_rows if total_rows > 0 else 0
    
    report = f"""
{'='*60}
📊 {workflow_name} 处理报告
{'='*60}
📈 处理统计:
   - 总行数: {total_rows}
   - 成功: {actual_processed_rows}
   - 失败: {failed_rows}
   - 跳过: {len(skipped_rows)}
   - 成功率: {(successful_rows/total_rows*100):.1f}% (如果总行数 > 0)
   - 总耗时: {total_time:.2f} 秒
   - 平均耗时: {avg_time:.2f} 秒/行

"""
    
    if failed_rows > 0:
        report += "❌ 失败详情:\n"
        for result in results:
            if not result.success:
                report += f"   - 第 {result.row_number} 行: {result.error}\n"
        report += "\n"
    
    if len(skipped_rows) > 0:
        report += "⏭️ 跳过的行:\n"
        for result in skipped_rows:
            report += f"   - 第 {result.row_number} 行：跳过\n"
        report += "\n"
    
    if actual_processed_rows > 0:
        report += "✅ 成功处理的行:\n"
        for result in results:
            if result.success and not (result.error and "跳过" in result.error):
                time_info = f" ({result.processing_time:.2f}s)" if result.processing_time else ""
                files_info = f" - {len(result.output_files)} 个文件" if result.output_files else ""
                report += f"   - 第 {result.row_number} 行{time_info}{files_info}\n"
    
    report += f"\n{'='*60}\n"
    return report


def setup_logging(config):
    """设置日志配置"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"workflow_{timestamp}.log"
    
    # 配置日志
    # 创建自定义的StreamHandler，确保立即刷新
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    stream_handler.flush = lambda: sys.stdout.flush()
    
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            stream_handler
        ]
    )
    
    # 确保所有日志立即刷新
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'stream') and handler.stream == sys.stdout:
            handler.stream.reconfigure(line_buffering=True)
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")
    return logger


async def main_process(args, workflow_mode):
    """主处理流程"""
    # 加载配置
    config = load_config()
    
    # 设置日志
    logger = setup_logging(config)
    logger.info("=== 开始执行飞书表格数据处理工作流 ===")
    
    try:
        # 步骤1: 初始化工作流管理器
        logger.info("🔧 步骤1: 初始化工作流管理器")
        debug_mode = getattr(args, 'debug', False)
        if debug_mode:
            logger.info("🔧 启用调试模式，将跳过ComfyUI API调用")
        workflow_manager = WorkflowManager(config, debug_mode=debug_mode)
        
        # 步骤1.5: 任务恢复检查
        logger.info("🔄 步骤1.5: 检查未完成任务并尝试恢复")
        from task_recovery_manager import TaskRecoveryManager
        from data import DatabaseManager
        from feishu_client import FeishuClient
        from comfyui_client import ComfyUIClient
        
        # 初始化必要的客户端
        db_manager = DatabaseManager()
        feishu_client = FeishuClient(config.feishu)
        comfyui_client = ComfyUIClient(config.comfyui, debug_mode=debug_mode)
        
        # 初始化任务恢复管理器
        recovery_manager = TaskRecoveryManager(config, db_manager, comfyui_client, feishu_client)
        
        # 执行任务恢复
        recovery_results = await recovery_manager.check_and_recover_tasks()
        if recovery_results.get('total_recovered', 0) > 0:
            logger.info(f"   ✅ 恢复了 {recovery_results['total_recovered']} 个未完成任务")
            for workflow_type, count in recovery_results.get('by_type', {}).items():
                if count > 0:
                    logger.info(f"      - {workflow_type}: {count} 个任务")
        else:
            logger.info("   ℹ️ 没有发现需要恢复的任务")
        
        # 步骤2: 获取飞书数据
        logger.info("📊 步骤2: 获取飞书表格数据")
        # feishu_client 已在步骤1.5中初始化
        
        logger.info("   - 正在连接飞书API...")
        rows_data = await feishu_client.get_sheet_data()
        
        if not rows_data:
            logger.info("   ⚠️  没有找到数据")
            return 0
        
        logger.info(f"   ✅ 获取到 {len(rows_data)} 行数据")
        
        # 步骤3: 执行工作流处理
        if workflow_mode == "FULL_WORKFLOW":
            logger.info("🚀 步骤3: 执行完整工作流 (图片合成 + 图生视频)")
            
            # 先执行图片合成工作流
            logger.info("🎨 阶段1: 执行图片合成工作流")
            image_results = await workflow_manager.process_with_workflow(WorkflowMode.IMAGE_COMPOSITION, rows_data)
            
            # 生成图片合成报告
            image_report = generate_workflow_report(image_results, "图片合成工作流")
            logger.info(image_report)
            
            # 再执行图生视频工作流
            logger.info("🎬 阶段2: 执行图生视频工作流")
            # 重新获取数据以获取最新的合成图片信息
            updated_rows_data = await feishu_client.get_sheet_data()
            video_results = await workflow_manager.process_with_workflow(WorkflowMode.IMAGE_TO_VIDEO, updated_rows_data)
            
            # 合并结果
            results = image_results + video_results
            workflow_name = "完整工作流 (图片合成 + 图生视频)"
        else:
            # 单一工作流模式
            workflow_name = workflow_manager.get_workflow_name(workflow_mode)
            logger.info(f"🚀 步骤3: 执行 {workflow_name}")
            logger.info(f"   ✅ 工作流管理器初始化完成 - 模式: {workflow_name}")
            
            if args.retry:
                # 重试模式 - 暂时使用原有逻辑
                logger.info("🔄 执行重试模式")
                processor = WorkflowProcessor(config)
                results = await processor.retry_failed_rows(args.max_retries)
            else:
                # 使用工作流管理器处理
                results = await workflow_manager.process_with_workflow(workflow_mode, rows_data)
        
        # 步骤4: 生成处理报告
        logger.info("📋 步骤4: 生成处理报告")
        report = generate_workflow_report(results, workflow_name)
        logger.info(report)
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path("reports") / f"report_{timestamp}.txt"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"处理报告已保存到: {report_file}")
        
        # 返回成功状态
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        if total_count == 0:
            logger.info("没有数据需要处理")
            return 0
        elif success_count == total_count:
            logger.info("所有数据处理成功")
            return 0
        else:
            logger.warning(f"部分数据处理失败: {success_count}/{total_count}")
            return 1
            
    except Exception as e:
        logger.error(f"执行过程中发生异常: {str(e)}")
        return 1


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="飞书表格数据处理ComfyUI工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 处理所有未处理的行
  python main.py --retry            # 重试失败的行
  python main.py --retry --max-retries 5  # 重试失败的行，最多重试5次
  python main.py --dry-run          # 干运行模式，不实际执行
        """
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
        '--dry-run',
        action='store_true',
        help='干运行模式，只检查数据不实际执行'
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


async def dry_run_mode():
    """干运行模式 - 只检查数据不实际执行"""
    config = load_config()
    logger = setup_logging(config)
    
    logger.info("=== 干运行模式 - 数据检查 ===")
    
    try:
        from feishu_client import FeishuClient
        
        # 创建飞书客户端
        feishu_client = FeishuClient(config.feishu)
        
        # 获取表格数据
        logger.info("获取飞书表格数据...")
        rows_data = await feishu_client.get_sheet_data()
        
        if not rows_data:
            logger.info("没有找到数据")
            return 0
        
        logger.info(f"找到 {len(rows_data)} 行数据")
        
        # 检查数据完整性
        valid_rows = 0
        invalid_rows = 0
        
        for row_data in rows_data:
            issues = []
            
            # 检查提示词
            if not row_data.prompt or not row_data.prompt.strip():
                issues.append("提示词为空")
            
            # 检查产品图片
            if not row_data.product_image:
                issues.append("产品图片为空")
            elif isinstance(row_data.product_image, dict):
                if not row_data.product_image.get("fileToken"):
                    issues.append("产品图片fileToken为空")
            
            # 检查模特图片
            if not row_data.model_image:
                issues.append("模特图片为空")
            elif isinstance(row_data.model_image, dict):
                if not row_data.model_image.get("fileToken"):
                    issues.append("模特图片fileToken为空")
            
            if issues:
                invalid_rows += 1
                logger.warning(f"行 {row_data.row_number} 数据问题: {', '.join(issues)}")
            else:
                valid_rows += 1
                logger.info(f"行 {row_data.row_number} 数据完整")
        
        logger.info(f"数据检查完成: {valid_rows} 行有效, {invalid_rows} 行无效")
        
        return 0 if invalid_rows == 0 else 1
        
    except Exception as e:
        logger.error(f"干运行检查时发生异常: {str(e)}")
        return 1


def main():
    """主函数"""
    args = parse_arguments()
    
    try:
        print("="*60)
        print("🚀 开始执行飞书表格数据处理工作流")
        print("="*60)
        
        if args.dry_run:
            # 干运行模式
            print("📋 执行模式: 干运行检查")
            exit_code = asyncio.run(dry_run_mode())
        else:
            # 选择工作流模式
            workflow_mode = select_workflow_mode()
            if workflow_mode is None:
                print("程序已取消")
                return
            
            # 处理图片去白底模式
            if workflow_mode == "PNG_PROCESSOR":
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
                exit_code = asyncio.run(main_process(args, workflow_mode))
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 程序执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()