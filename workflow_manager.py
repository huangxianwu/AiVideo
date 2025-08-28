#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理器 - 实现工作流模式选择和解耦设计
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass

from config import AppConfig
from feishu_client import FeishuClient, RowData
from comfyui_client import ComfyUIClient
from data import DatabaseManager, WorkflowStatus


class WorkflowMode(Enum):
    """工作流模式枚举"""
    IMAGE_COMPOSITION = "image_composition"  # 图片合成工作流
    IMAGE_TO_VIDEO = "image_to_video"        # 图生视频工作流


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    row_number: int
    task_id: Optional[str] = None
    output_files: List[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class BaseWorkflow(ABC):
    """工作流基类"""
    
    def __init__(self, config: AppConfig, feishu_client: FeishuClient, comfyui_client: ComfyUIClient, db_manager: DatabaseManager):
        self.config = config
        self.feishu_client = feishu_client
        self.comfyui_client = comfyui_client
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process_row(self, row_data: RowData) -> WorkflowResult:
        """处理单行数据"""
        pass
    
    @abstractmethod
    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        pass
    
    @abstractmethod
    def should_process_row(self, row_data: RowData) -> bool:
        """判断是否应该处理该行数据"""
        pass


class ImageCompositionWorkflow(BaseWorkflow):
    """图片合成工作流"""
    
    def get_workflow_name(self) -> str:
        return "图片合成工作流"
    
    def should_process_row(self, row_data: RowData) -> bool:
        """检查是否需要处理图片合成"""
        # 检查列D（status）是否为"否"，如果是则需要处理
        return row_data.status == "否"
    
    async def process_row(self, row_data: RowData) -> WorkflowResult:
        """处理图片合成"""
        start_time = asyncio.get_event_loop().time()
        
        # 生成任务ID
        product_name = getattr(row_data, 'product_name', '')
        task_id = self.db_manager.generate_task_id(row_data.row_number, product_name)
        
        try:
            # self.logger.info(f"🎨 开始处理图片合成 - 第 {row_data.row_number} 行，产品名：{product_name}，提示词：{row_data.prompt}")
            
            # 验证数据
            validation_error = self._validate_row_data(row_data)
            if validation_error:
                # 记录失败任务
                self.db_manager.start_image_generation(task_id, row_data.row_number, product_name)
                self.db_manager.mark_task_failed(task_id, validation_error)
                
                return WorkflowResult(
                    success=False,
                    row_number=row_data.row_number,
                    task_id=task_id,
                    error=validation_error
                )
            
            # 开始图片生成任务
            metadata = {
                'prompt': row_data.prompt,
                'workflow_type': 'image_composition'
            }
            self.db_manager.start_image_generation(task_id, row_data.row_number, product_name, metadata)
            
            # 下载图片
            product_image_data = await self._download_image(row_data.product_image)
            model_image_data = await self._download_image(row_data.model_image)
            
            # 执行ComfyUI工作流
            workflow_result = await self.comfyui_client.process_workflow(
                product_image_data,
                model_image_data
            )
            
            if not workflow_result.success:
                # 标记任务失败
                self.db_manager.mark_task_failed(task_id, workflow_result.error)
                
                return WorkflowResult(
                    success=False,
                    row_number=row_data.row_number,
                    task_id=task_id,
                    error=workflow_result.error
                )
            
            # 下载并保存结果
            output_files = await self._save_result_files(row_data, workflow_result)
            
            # 完成图片生成，准备视频生成
            if output_files:
                self.db_manager.complete_image_generation(task_id, output_files[0])
            
            # 更新表格状态
            await self._update_table_status(row_data, output_files)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return WorkflowResult(
                success=True,
                row_number=row_data.row_number,
                task_id=task_id,
                output_files=output_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"图片合成处理异常: {str(e)}"
            self.logger.error(f"        ❌ {error_msg}")
            
            # 标记任务失败
            self.db_manager.mark_task_failed(task_id, error_msg)
            
            return WorkflowResult(
                success=False,
                row_number=row_data.row_number,
                task_id=task_id,
                error=error_msg,
                processing_time=processing_time
            )
    
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
            file_token = image_data.get("fileToken")
            return await self.feishu_client.download_image(file_token)
        elif isinstance(image_data, str) and image_data.strip():
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
    
    async def _save_result_files(self, row_data: RowData, workflow_result) -> List[str]:
        """保存结果文件"""
        import os
        from datetime import datetime
        from date_utils import create_date_organized_filepath
        
        output_files = []
        if workflow_result.output_urls:
            # 只保存最后一个文件
            url = workflow_result.output_urls[-1] if len(workflow_result.output_urls) >= 2 else workflow_result.output_urls[0]
            
            # 在调试模式下跳过实际下载
            if self.comfyui_client.debug_mode:
                # 创建模拟文件数据
                file_data = b"debug_image_data"
                self.logger.info(f"🔧 [调试模式] 跳过文件下载，使用模拟数据: {url}")
            else:
                file_data = await self.comfyui_client.download_result(url)
            
            # 生成文件名
            product_name = row_data.product_name or f"row_{row_data.row_number}"
            model_name = row_data.model_name or "unknown_model"
            safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_model_name = "".join(c for c in model_name if c.isalnum() or c in (' ', '-', '_')).strip()
            timestamp = datetime.now().strftime('%m/%d/%H:%M')
            filename = f"{safe_product_name}_{safe_model_name}_{timestamp}.png".replace('/', '-').replace(':', '-')
            
            # 使用日期组织的文件路径
            filepath = create_date_organized_filepath(self.config.output_dir, "img", filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            output_files.append(filepath)
            self.logger.info(f"        ✅ 文件保存成功: {filepath}")
        
        return output_files
    
    async def _update_table_status(self, row_data: RowData, output_files: List[str]):
        """更新表格状态"""
        if output_files:
            # 写入图片到表格
            write_success = await self.feishu_client.write_image_to_cell(row_data.row_number, output_files[0])
            if write_success:
                # 更新状态为已完成
                await self.feishu_client.update_cell_status(row_data.row_number, "已完成")


class ImageToVideoWorkflow(BaseWorkflow):
    """图生视频工作流"""
    
    def get_workflow_name(self) -> str:
        return "图生视频工作流"
    
    def should_process_row(self, row_data: RowData) -> bool:
        """检查是否需要处理图生视频"""
        # 检查视频工作流是否启用
        if not self.config.comfyui.video_workflow_enabled:
            return False
        
        # 检查视频状态是否为"否"
        if row_data.video_status != "否":
            return False
        
        # 检查产品模特合成图是否存在
        has_composite_image = (
            hasattr(row_data, 'composite_image') and 
            row_data.composite_image and 
            (
                (isinstance(row_data.composite_image, str) and bool(row_data.composite_image.strip())) or
                (isinstance(row_data.composite_image, dict) and bool(row_data.composite_image.get('fileToken')))
            )
        )
        
        # 检查提示词是否存在
        has_prompt = (
            hasattr(row_data, 'prompt') and 
            row_data.prompt and 
            bool(row_data.prompt.strip())
        )
        
        # 添加调试信息
        self.logger.info(f"      🔍 第 {row_data.row_number} 行图生视频判断条件:")
        self.logger.info(f"         - video_workflow_enabled: {self.config.comfyui.video_workflow_enabled}")
        self.logger.info(f"         - video_status: '{row_data.video_status}'")
        self.logger.info(f"         - composite_image: {getattr(row_data, 'composite_image', 'N/A')}")
        self.logger.info(f"         - has_composite_image: {has_composite_image}")
        self.logger.info(f"         - prompt: '{getattr(row_data, 'prompt', 'N/A')[:50]}...'")
        self.logger.info(f"         - has_prompt: {has_prompt}")
        self.logger.info(f"         - 最终判断结果: {has_composite_image and has_prompt}")
        
        # 只有当产品模特合成图和提示词都不为空时才执行
        return has_composite_image and has_prompt
    
    async def process_row(self, row_data: RowData) -> WorkflowResult:
        """处理图生视频"""
        start_time = asyncio.get_event_loop().time()
        
        # 生成任务ID或查找现有任务
        product_name = getattr(row_data, 'product_name', '')
        existing_task = self.db_manager.get_task_by_row_index(row_data.row_number)
        
        if existing_task:
            task_id = existing_task['task_id']
            # 更新状态为视频生成中
            self.db_manager.start_video_generation(task_id)
        else:
            # 创建新任务（如果之前没有图片生成任务）
            task_id = self.db_manager.generate_task_id(row_data.row_number, product_name)
            metadata = {
                'prompt': row_data.prompt or "生成视频",
                'workflow_type': 'image_to_video'
            }
            # 开始图片生成任务（即使跳过图片生成步骤，也需要创建任务记录）
            self.db_manager.start_image_generation(task_id, row_data.row_number, product_name, metadata)
            # 直接转到视频生成状态
            self.db_manager.start_video_generation(task_id)
        
        try:
            self.logger.info(f"🎬 开始处理图生视频 - 第 {row_data.row_number} 行")
            
            # 检查是否有合成图片（从E列获取）
            if not row_data.composite_image:
                error_msg = "没有找到合成图片，请先完成图片合成"
                self.db_manager.mark_task_failed(task_id, error_msg)
                
                return WorkflowResult(
                    success=False,
                    row_number=row_data.row_number,
                    task_id=task_id,
                    error=error_msg
                )
            
            # 下载合成图片
            composite_image_data = await self._download_image(row_data.composite_image)
            
            # 保存为临时文件
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(composite_image_data)
                temp_image_path = temp_file.name
            
            try:
                # 获取提示词
                prompt = row_data.prompt or "生成视频"
                
                # 调用图生视频工作流
                video_result = await self.comfyui_client.process_video_workflow(
                    temp_image_path, 
                    prompt
                )
            finally:
                # 清理临时文件
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
            
            if not video_result.success:
                # 标记任务失败
                self.db_manager.mark_task_failed(task_id, video_result.error)
                
                return WorkflowResult(
                    success=False,
                    row_number=row_data.row_number,
                    task_id=task_id,
                    error=video_result.error
                )
            
            # 下载并保存视频文件
            output_files = await self._save_video_files(row_data, video_result)
            
            # 完成视频生成
            if output_files:
                self.db_manager.complete_video_generation(task_id, output_files[0])
            
            # 更新视频状态
            await self._update_video_status(row_data)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return WorkflowResult(
                success=True,
                row_number=row_data.row_number,
                task_id=task_id,
                output_files=output_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"图生视频处理异常: {str(e)}"
            self.logger.error(f"        ❌ {error_msg}")
            
            # 标记任务失败
            self.db_manager.mark_task_failed(task_id, error_msg)
            
            return WorkflowResult(
                success=False,
                row_number=row_data.row_number,
                task_id=task_id,
                error=error_msg,
                processing_time=processing_time
            )
    
    async def _download_image(self, image_data) -> bytes:
        """下载图片数据"""
        if isinstance(image_data, dict) and image_data.get("type") == "embed-image":
            file_token = image_data.get("fileToken")
            return await self.feishu_client.download_image(file_token)
        elif isinstance(image_data, str) and image_data.startswith("http"):
            # 如果是URL，直接下载
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_data) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        raise Exception(f"下载图片失败: HTTP {response.status}")
        else:
            raise Exception(f"无效的图片数据: {type(image_data)} - {image_data}")
    
    async def _save_video_files(self, row_data: RowData, video_result) -> List[str]:
        """保存视频文件"""
        import os
        from datetime import datetime
        from date_utils import create_date_organized_filepath
        
        output_files = []
        if video_result.output_urls:
            for url in video_result.output_urls:
                # 在调试模式下跳过实际下载
                if self.comfyui_client.debug_mode:
                    # 创建模拟视频文件数据
                    video_data = b"debug_video_data"
                    self.logger.info(f"🔧 [调试模式] 跳过视频文件下载，使用模拟数据: {url}")
                else:
                    video_data = await self.comfyui_client.download_result(url)
                
                # 生成视频文件名
                product_name = row_data.product_name or f"row_{row_data.row_number}"
                model_name = row_data.model_name or "unknown_model"
                safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_model_name = "".join(c for c in model_name if c.isalnum() or c in (' ', '-', '_')).strip()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                video_filename = f"{safe_product_name}_{safe_model_name}_{timestamp}.mp4"
                
                # 使用日期组织的文件路径
                video_filepath = create_date_organized_filepath(self.config.output_dir, "video", video_filename)
                
                with open(video_filepath, 'wb') as f:
                    f.write(video_data)
                
                output_files.append(video_filepath)
                self.logger.info(f"        ✅ 视频文件保存成功: {video_filepath}")
                break  # 只处理第一个视频文件
        
        return output_files
    
    async def _update_video_status(self, row_data: RowData):
        """更新视频状态"""
        await self.feishu_client.update_video_status(row_data.row_number, "已完成")


class WorkflowManager:
    """工作流管理器 - 负责协调不同的工作流"""
    
    def __init__(self, config: AppConfig, debug_mode: bool = False):
        self.config = config
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(self.__class__.__name__)
        self.workflows = {}
        if debug_mode:
            self.logger.info("🔧 工作流管理器运行在调试模式")
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """初始化工作流"""
        from feishu_client import FeishuClient
        from comfyui_client import ComfyUIClient
        from data import DatabaseManager
        
        feishu_client = FeishuClient(self.config.feishu)
        comfyui_client = ComfyUIClient(self.config.comfyui, debug_mode=self.debug_mode)
        self.db_manager = DatabaseManager()  # 保存为实例属性
        
        self.workflows[WorkflowMode.IMAGE_COMPOSITION] = ImageCompositionWorkflow(
            self.config, feishu_client, comfyui_client, self.db_manager
        )
        self.workflows[WorkflowMode.IMAGE_TO_VIDEO] = ImageToVideoWorkflow(
            self.config, feishu_client, comfyui_client, self.db_manager
        )
    
    def get_workflow(self, mode: WorkflowMode) -> BaseWorkflow:
        """获取指定模式的工作流"""
        return self.workflows[mode]
    
    def get_available_workflows(self) -> List[WorkflowMode]:
        """获取可用的工作流模式"""
        return list(self.workflows.keys())
    
    def get_workflow_name(self, mode: WorkflowMode) -> str:
        """获取工作流名称"""
        return self.workflows[mode].get_workflow_name()
    
    async def process_with_workflow(self, mode: WorkflowMode, rows_data: List[RowData]) -> List[WorkflowResult]:
        """使用指定工作流处理数据"""
        workflow = self.workflows[mode]
        results = []
        
        self.logger.info(f"🚀 开始执行 {workflow.get_workflow_name()}")
        self.logger.info(f"📊 总共需要处理 {len(rows_data)} 行数据")
        
        for i, row_data in enumerate(rows_data, 1):
            # 获取产品名和提示词用于日志显示
            product_name = row_data.product_name or "未知产品"
            prompt_preview = (row_data.prompt[:30] + "...") if row_data.prompt and len(row_data.prompt) > 30 else (row_data.prompt or "无提示词")
            
            # 检查是否需要处理该行
            if not workflow.should_process_row(row_data):
                self.logger.info(f"📝 处理进度: {i}/{len(rows_data)} - 第 {row_data.row_number} 行，跳过")
                # 跳过不需要处理的行
                results.append(WorkflowResult(
                    success=True,
                    row_number=row_data.row_number,
                    task_id=None,
                    output_files=[],
                    error="跳过 - 不满足处理条件",
                    processing_time=0.0
                ))
                continue
            
            self.logger.info(f"📝 处理进度: {i:>2}/{len(rows_data):<2} - 第 {row_data.row_number:>2} 行 | 产品: {product_name:<15} | 提示词: {prompt_preview}")
            
            # 处理该行数据
            result = await workflow.process_row(row_data)
            results.append(result)
            
            if result.success:
                self.logger.info(f"     ✅ 第 {row_data.row_number} 行处理成功 | 产品: {product_name} | 提示词: {prompt_preview}")
            else:
                self.logger.error(f"     ❌ 第 {row_data.row_number} 行处理失败 | 产品: {product_name} | 提示词: {prompt_preview} | 错误: {result.error}")
        
        return results