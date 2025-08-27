#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主工作流处理器 - 整合飞书和ComfyUI，实现完整的数据处理流程
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from config import AppConfig
from feishu_client import FeishuClient, RowData
from comfyui_client import ComfyUIClient, WorkflowResult


@dataclass
class ProcessResult:
    """处理结果"""
    success: bool
    row_number: int
    task_id: Optional[str] = None
    output_files: List[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class WorkflowProcessor:
    """主工作流处理器"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.feishu_client = FeishuClient(config.feishu)
        self.comfyui_client = ComfyUIClient(config.comfyui)
        self.logger = logging.getLogger(__name__)
        
        # 设置目录路径
        self.temp_dir = Path(config.temp_dir)
        self.output_dir = Path(config.output_dir)
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        # 创建img子目录
        img_dir = Path(self.config.output_dir) / "img"
        img_dir.mkdir(parents=True, exist_ok=True)
        # 创建video子目录
        video_dir = Path(self.config.output_dir) / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"创建目录: {self.config.temp_dir}, {self.config.output_dir}, {img_dir}, {video_dir}")
    
    async def process_all_rows(self) -> List[ProcessResult]:
        """处理所有行数据"""
        self.logger.info("🚀 开始工作流处理...")
        self.logger.info("="*50)
        
        try:
            # 步骤1: 获取表格数据
            self.logger.info("📊 步骤1: 获取飞书表格数据")
            self.logger.info("   - 正在连接飞书API...")
            rows_data = await self.feishu_client.get_sheet_data()
            
            if not rows_data:
                self.logger.warning("⚠️  没有找到需要处理的数据")
                return []
            
            self.logger.info(f"   ✅ 成功获取 {len(rows_data)} 行数据")
            
            # 步骤2: 数据预处理
            self.logger.info("🔍 步骤2: 数据预处理和筛选")
            valid_rows = []
            skipped_count = 0
            
            for row_data in rows_data:
                if self._is_already_processed(row_data):
                    skipped_count += 1
                    self.logger.info(f"   ⏭️  跳过已处理的行 {row_data.row_number}")
                    continue
                valid_rows.append(row_data)
            
            self.logger.info(f"   - 总行数: {len(rows_data)}")
            self.logger.info(f"   - 需要处理: {len(valid_rows)} 行")
            self.logger.info(f"   - 跳过行数: {skipped_count} 行")
            
            if not valid_rows:
                self.logger.info("✅ 所有数据都已处理完成")
                return []
            
            # 步骤3: 逐行处理数据（带队列管理）
            self.logger.info("⚙️  步骤3: 开始逐行处理数据")
            if self.config.comfyui.queue_enabled:
                self.logger.info(f"   🔄 队列管理已启用 - 检查间隔: {self.config.comfyui.task_check_interval}秒")
            
            results = []
            current_task_id = None
            
            for i, row_data in enumerate(valid_rows, 1):
                try:
                    self.logger.info(f"   📝 处理进度: {i}/{len(valid_rows)} - 行 {row_data.row_number}")
                    
                    # 如果启用队列管理且有前一个任务，等待其完成
                    if self.config.comfyui.queue_enabled and current_task_id:
                        await self._wait_for_previous_task(current_task_id, row_data.row_number)
                    
                    # 处理单行数据
                    result = await self.process_single_row(row_data)
                    results.append(result)
                    
                    # 更新当前任务ID
                    if result.success and result.task_id:
                        current_task_id = result.task_id
                    
                    # 更新处理状态
                    if result.success:
                        self.logger.info(f"   ✅ 行 {row_data.row_number} 处理成功")
                        await self.feishu_client.update_cell_status(row_data.row_number, "已处理")
                    else:
                        self.logger.error(f"   ❌ 行 {row_data.row_number} 处理失败: {result.error}")
                        await self.feishu_client.update_cell_status(row_data.row_number, f"处理失败: {result.error}")
                    
                    # 添加延迟，避免API限制（如果不是因为队列满而重试的情况）
                    if i < len(valid_rows) and not ("队列已满" in str(result.error)):
                        self.logger.info(f"   ⏱️  等待 2 秒避免API限制...")
                        await asyncio.sleep(2)
                    
                except Exception as e:
                    error_msg = f"处理行 {row_data.row_number} 时发生异常: {str(e)}"
                    self.logger.error(f"   ❌ {error_msg}")
                    results.append(ProcessResult(
                        success=False,
                        row_number=row_data.row_number,
                        error=error_msg
                    ))
            
            # 等待最后一个任务完成
            if self.config.comfyui.queue_enabled and current_task_id:
                self.logger.info("   🏁 等待最后一个任务完成...")
                await self._wait_for_previous_task(current_task_id, "最后任务")
            
            # 步骤4: 统计结果
            self.logger.info("📈 步骤4: 处理结果统计")
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            self.logger.info("="*50)
            self.logger.info(f"✅ 工作流处理完成")
            self.logger.info(f"   - 处理总数: {total_count} 行")
            self.logger.info(f"   - 成功数量: {success_count} 行")
            self.logger.info(f"   - 失败数量: {total_count - success_count} 行")
            self.logger.info(f"   - 成功率: {success_rate:.1f}%")
            self.logger.info("="*50)
            
            return results
            
        except Exception as e:
            error_msg = f"处理工作流时发生异常: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    async def process_single_row(self, row_data: RowData) -> ProcessResult:
        """处理单行数据"""
        start_time = asyncio.get_event_loop().time()
        
        # 获取产品名和提示词用于日志显示
        product_name = row_data.product_name or "未知产品"
        prompt_preview = (row_data.prompt[:30] + "...") if row_data.prompt and len(row_data.prompt) > 30 else (row_data.prompt or "无提示词")
        
        self.logger.info(f"🔄 处理第 {row_data.row_number} 行 | 产品: {product_name} | 提示词: {prompt_preview}")
        
        try:
            # 验证数据完整性
            validation_error = self._validate_row_data(row_data)
            if validation_error:
                self.logger.error(f"❌ 第 {row_data.row_number} 行数据验证失败: {validation_error}")
                return ProcessResult(
                    success=False,
                    row_number=row_data.row_number,
                    error=validation_error
                )
            
            # 下载图片
            product_image_data = await self._download_image(row_data.product_image)
            model_image_data = await self._download_image(row_data.model_image)
            
            # 执行ComfyUI工作流
            
            # 处理队列满的情况，最多重试3次
            max_retries = 3
            retry_count = 0
            
            while retry_count <= max_retries:
                workflow_result = await self.comfyui_client.process_workflow(
                    product_image_data,
                    model_image_data
                )
                
                if workflow_result.success:
                    break
                    
                # 检查是否是队列满的错误
                if "ComfyUI任务队列已满" in str(workflow_result.error):
                    retry_count += 1
                    if retry_count <= max_retries:
                        self.logger.warning(f"⚠️ 队列已满，等待重试 ({retry_count}/{max_retries})")
                        await asyncio.sleep(30)
                        continue
                    else:
                         error_msg = f"队列已满，重试{max_retries}次后仍然失败"
                         self.logger.error(f"❌ {error_msg}")
                         raise Exception(error_msg)
                else:
                    # 其他类型的错误，直接返回失败
                    self.logger.error(f"❌ 工作流执行失败: {workflow_result.error}")
                    return ProcessResult(
                        success=False,
                        row_number=row_data.row_number,
                        error=workflow_result.error
                    )
            
            # 下载并保存结果文件
            output_files = []
            if workflow_result.output_urls:
                # 只保存最后一个文件（如果有多个文件的话）
                url = workflow_result.output_urls[-1] if len(workflow_result.output_urls) >= 2 else workflow_result.output_urls[0]
                
                try:
                    file_data = await self.comfyui_client.download_result(url)
                    # 使用产品名+模特名+时间戳格式
                    product_name = row_data.product_name or f"row_{row_data.row_number}"
                    model_name = row_data.model_name or "unknown_model"
                    # 清理产品名和模特名中的特殊字符
                    safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_model_name = "".join(c for c in model_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    timestamp = datetime.now().strftime('%m/%d/%H:%M')
                    filename = f"{safe_product_name}_{safe_model_name}_{timestamp}.png".replace('/', '-').replace(':', '-')
                    # 保存到img子目录
                    img_dir = os.path.join(self.config.output_dir, "img")
                    filepath = os.path.join(img_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    output_files.append(filepath)
                    
                    # 写入图片到表格
                    try:
                        write_success = await self.feishu_client.write_image_to_cell(row_data.row_number, filepath)
                        
                        if write_success:
                            # 更新状态为已完成
                            try:
                                status_success = await self.feishu_client.update_cell_status(row_data.row_number, "已完成")
                                if not status_success:
                                    self.logger.error(f"❌ 状态更新失败")
                            except Exception as e:
                                self.logger.error(f"❌ 状态更新异常: {str(e)}")
                        else:
                            self.logger.error(f"❌ 图片写入表格失败")
                            
                    except Exception as e:
                        self.logger.error(f"❌ 写入图片到表格异常: {str(e)}")
                    
                except Exception as e:
                    self.logger.error(f"❌ 保存输出文件失败: {str(e)}")
            else:
                self.logger.warning(f"⚠️ 没有找到输出文件")
            
            # 检查是否需要生成视频
            if self.config.comfyui.video_workflow_enabled and row_data.video_status == "否":
                self.logger.info(f"🎬 开始图生视频处理")
                await self._process_video_generation(row_data, output_files)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            self.logger.info(f"✅ 第 {row_data.row_number} 行处理成功 | 产品: {product_name} | 耗时 {processing_time:.2f}s")
            
            return ProcessResult(
                success=True,
                row_number=row_data.row_number,
                task_id=workflow_result.task_id,
                output_files=output_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"处理第 {row_data.row_number} 行时发生异常: {str(e)}"
            self.logger.error(f"❌ 第 {row_data.row_number} 行处理失败 | 产品: {product_name} | 错误: {str(e)}")
            
            return ProcessResult(
                success=False,
                row_number=row_data.row_number,
                error=error_msg,
                processing_time=processing_time
            )
    
    async def _process_video_generation(self, row_data: RowData, output_files: List[str]) -> None:
        """处理图生视频生成"""
        try:
            # 检查是否有合成图片文件
            if not output_files:
                self.logger.warning(f"⚠️ 没有找到合成图片，跳过视频生成")
                return
            
            # 使用最新生成的合成图片
            composite_image_path = output_files[-1]
            prompt = row_data.prompt or "生成视频"
            
            # 调用图生视频工作流
            video_result = await self.comfyui_client.process_video_workflow(
                composite_image_path, 
                prompt
            )
            
            if video_result.success:
                # 下载并保存视频文件
                if video_result.output_urls:
                    for url in video_result.output_urls:
                        try:
                            video_data = await self.comfyui_client.download_result(url)
                            
                            # 生成视频文件名：产品名+模特名+时间戳.mp4
                            product_name = row_data.product_name or f"row_{row_data.row_number}"
                            model_name = row_data.model_name or "unknown_model"
                            safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
                            safe_model_name = "".join(c for c in model_name if c.isalnum() or c in (' ', '-', '_')).strip()
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            video_filename = f"{safe_product_name}+{safe_model_name}+{timestamp}.mp4"
                            
                            # 创建video子目录
                            video_dir = os.path.join(self.config.output_dir, "video")
                            os.makedirs(video_dir, exist_ok=True)
                            video_filepath = os.path.join(video_dir, video_filename)
                            
                            with open(video_filepath, 'wb') as f:
                                f.write(video_data)
                            
                            # 更新视频状态为"是"
                            try:
                                video_status_success = await self.feishu_client.update_video_status(row_data.row_number, "是")
                                if not video_status_success:
                                    self.logger.error(f"❌ 视频状态更新失败")
                            except Exception as e:
                                self.logger.error(f"❌ 视频状态更新异常: {str(e)}")
                            
                            break  # 只处理第一个视频文件
                            
                        except Exception as e:
                            self.logger.error(f"❌ 视频文件下载失败: {str(e)}")
                else:
                    self.logger.warning(f"⚠️ 没有找到视频输出文件")
            else:
                self.logger.error(f"❌ 视频生成失败: {video_result.error}")
                
        except Exception as e:
            self.logger.error(f"❌ 图生视频处理异常: {str(e)}")
    
    def _validate_row_data(self, row_data: RowData) -> Optional[str]:
        """验证行数据完整性"""
        if not row_data.prompt or not row_data.prompt.strip():
            return "提示词为空"
        
        if not self._is_valid_image_data(row_data.product_image):
            return "产品图片数据无效"
        
        if not self._is_valid_image_data(row_data.model_image):
            return "模特图片数据无效"
        
        return None
    
    def _is_valid_image_data(self, image_data) -> bool:
        """检查图片数据是否有效"""
        if isinstance(image_data, dict):
            return image_data.get("type") == "embed-image" and image_data.get("fileToken")
        elif isinstance(image_data, str):
            return bool(image_data.strip())
        return False
    
    async def _download_image(self, image_data) -> bytes:
        """下载图片数据"""
        if isinstance(image_data, dict) and image_data.get("type") == "embed-image":
            # 从飞书下载嵌入式图片
            file_token = image_data.get("fileToken")
            return await self.feishu_client.download_image(file_token)
        elif isinstance(image_data, str) and image_data.strip():
            # 如果是URL，直接下载
            if image_data.startswith("http"):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_data) as response:
                        if response.status == 200:
                            return await response.read()
                        else:
                            raise Exception(f"下载图片失败: HTTP {response.status}")
            else:
                raise Exception(f"不支持的图片数据格式: {image_data}")
        else:
            raise Exception("无效的图片数据")
    
    def _is_already_processed(self, row_data: RowData) -> bool:
        """检查是否已经处理过"""
        status = row_data.status.lower() if row_data.status else ""
        return "已处理" in status or "processed" in status
    
    async def _wait_for_previous_task(self, task_id: str, current_row: str) -> None:
        """等待前一个任务完成"""
        if not task_id:
            return
        
        self.logger.info(f"   ⏳ 等待前一个任务完成 (ID: {task_id}) - 当前处理: {current_row}")
        
        start_time = asyncio.get_event_loop().time()
        max_wait_time = self.config.comfyui.task_max_wait_time
        check_interval = self.config.comfyui.task_check_interval
        wait_interval = self.config.comfyui.task_wait_interval
        
        while True:
            try:
                # 检查任务状态
                status_result = await self.comfyui_client.check_task_status(task_id)
                
                if status_result.success and status_result.status == 'SUCCESS':
                    self.logger.info(f"   ✅ 前一个任务已完成 (ID: {task_id})")
                    break
                elif status_result.success and status_result.status == 'FAILED':
                    self.logger.warning(f"   ⚠️  前一个任务失败 (ID: {task_id})，继续处理下一个任务")
                    break
                elif not status_result.success:
                    self.logger.warning(f"   ⚠️  检查任务状态失败: {status_result.error}")
                    # 继续等待，不中断流程
                else:
                    # 任务仍在进行中
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    remaining_time = max_wait_time - elapsed_time
                    
                    if elapsed_time >= max_wait_time:
                        self.logger.error(f"   ❌ 前一个任务超时 (ID: {task_id})，已等待 {max_wait_time} 秒，停止所有任务")
                        raise Exception(f"任务 {task_id} 超时，已等待 {max_wait_time} 秒")
                    
                    self.logger.info(f"   ⏱️  任务进行中，等待 {wait_interval} 秒后重新检查 (剩余超时时间: {remaining_time:.0f}秒)")
                    await asyncio.sleep(wait_interval)
                    
            except Exception as e:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time >= max_wait_time:
                    self.logger.error(f"   ❌ 等待任务超时: {str(e)}")
                    raise
                else:
                    self.logger.warning(f"   ⚠️  检查任务状态时出错: {str(e)}，{check_interval}秒后重试")
                    await asyncio.sleep(check_interval)
    
    async def retry_failed_rows(self, max_retries: int = None) -> List[ProcessResult]:
        """重试失败的行"""
        if max_retries is None:
            max_retries = self.config.max_retries
        
        self.logger.info(f"开始重试失败的行，最大重试次数: {max_retries}")
        
        # 获取所有数据
        rows_data = await self.feishu_client.get_sheet_data()
        
        # 筛选出失败的行
        failed_rows = [
            row for row in rows_data 
            if row.status and ("失败" in row.status or "error" in row.status.lower())
        ]
        
        if not failed_rows:
            self.logger.info("没有找到需要重试的失败行")
            return []
        
        self.logger.info(f"找到 {len(failed_rows)} 行需要重试")
        
        results = []
        for row_data in failed_rows:
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"重试第 {row_data.row_number} 行，第 {attempt + 1} 次尝试")
                    
                    result = await self.process_single_row(row_data)
                    results.append(result)
                    
                    if result.success:
                        await self.feishu_client.update_cell_status(row_data.row_number, "已处理")
                        break
                    else:
                        if attempt == max_retries - 1:
                            await self.feishu_client.update_cell_status(
                                row_data.row_number, 
                                f"重试失败: {result.error}"
                            )
                        else:
                            # 等待后重试
                            await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    error_msg = f"重试第 {row_data.row_number} 行时发生异常: {str(e)}"
                    self.logger.error(error_msg)
                    
                    if attempt == max_retries - 1:
                        results.append(ProcessResult(
                            success=False,
                            row_number=row_data.row_number,
                            error=error_msg
                        ))
        
        return results
    
    def generate_report(self, results: List[ProcessResult]) -> str:
        """生成处理报告"""
        if not results:
            return "没有处理结果"
        
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        report = f"\n=== 工作流处理报告 ===\n"
        report += f"总处理行数: {total_count}\n"
        report += f"成功行数: {success_count}\n"
        report += f"失败行数: {total_count - success_count}\n"
        report += f"成功率: {success_count/total_count*100:.1f}%\n\n"
        
        # 成功的行
        successful_rows = [r for r in results if r.success]
        if successful_rows:
            report += "成功处理的行:\n"
            for result in successful_rows:
                report += f"  行 {result.row_number}: 任务ID {result.task_id}, 耗时 {result.processing_time:.2f}s\n"
            report += "\n"
        
        # 失败的行
        failed_rows = [r for r in results if not r.success]
        if failed_rows:
            report += "处理失败的行:\n"
            for result in failed_rows:
                report += f"  行 {result.row_number}: {result.error}\n"
            report += "\n"
        
        return report