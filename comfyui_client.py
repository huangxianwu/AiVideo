#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI API客户端 - 处理图片上传、工作流执行和状态监控
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config import ComfyUIConfig


@dataclass
class UploadResult:
    """上传结果"""
    success: bool
    file_name: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    task_id: Optional[str] = None
    status: Optional[str] = None
    output_urls: List[str] = None
    error: Optional[str] = None


class ComfyUIClient:
    """ComfyUI API客户端"""
    
    def __init__(self, config: ComfyUIConfig, debug_mode: bool = False):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        if debug_mode:
            self.logger.info("🔧 ComfyUI客户端运行在调试模式，将跳过实际API调用")
        
    async def upload_image(self, image_data: bytes, filename: str = "image.png") -> UploadResult:
        """上传图片到ComfyUI"""
        if self.debug_mode:
            # 调试模式：模拟上传成功
            mock_filename = f"debug_{filename}"
            self.logger.info(f"🔧 [调试模式] 模拟上传图片: {mock_filename}")
            await asyncio.sleep(0.1)  # 模拟短暂延迟
            return UploadResult(success=True, file_name=mock_filename)
        
        url = f"{self.config.base_url}/task/openapi/upload"
        
        headers = {
            "Host": "www.runninghub.cn",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        # 构建multipart/form-data
        data = aiohttp.FormData()
        data.add_field('file', image_data, filename=filename, content_type='image/png')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            file_name = result.get('data', {}).get('fileName')
                            return UploadResult(
                                success=True,
                                file_name=file_name
                            )
                        else:
                            error_msg = result.get('message', '未知错误')
                            self.logger.error(f"图片上传失败: {error_msg}")
                            return UploadResult(success=False, error=error_msg)
                    else:
                        error_msg = f"HTTP错误: {response.status}"
                        self.logger.error(f"图片上传失败: {error_msg}")
                        return UploadResult(success=False, error=error_msg)
                        
        except Exception as e:
            error_msg = f"图片上传异常: {str(e)}"
            self.logger.error(error_msg)
            return UploadResult(success=False, error=error_msg)
    
    async def create_workflow(self, product_image_name: str, model_image_name: str) -> WorkflowResult:
        """创建工作流"""
        if self.debug_mode:
            # 调试模式：模拟工作流创建成功
            mock_task_id = f"debug_task_{asyncio.get_event_loop().time():.0f}"
            self.logger.info(f"🔧 [调试模式] 模拟创建工作流，任务ID: {mock_task_id}")
            await asyncio.sleep(0.1)  # 模拟短暂延迟
            return WorkflowResult(success=True, task_id=mock_task_id)
        
        url = f"{self.config.base_url}/task/openapi/create"
        
        headers = {
            "Host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        
        # 构建节点信息列表
        node_info_list = [
            {
                "nodeId": self.config.product_image_node_id,
                "fieldName": "image",
                "fieldValue": product_image_name
            },
            {
                "nodeId": self.config.model_image_node_id,
                "fieldName": "image", 
                "fieldValue": model_image_name
            }
        ]
        
        payload = {
            "apiKey": self.config.api_key,
            "workflowId": self.config.workflow_id,
            "nodeInfoList": node_info_list
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    try:
                        result = await response.json()
                    except Exception as json_error:
                        self.logger.error(f"解析响应JSON失败: {json_error}")
                        return WorkflowResult(success=False, error=f"响应解析失败: {json_error}")
                    
                    # 检查响应是否为空
                    if result is None:
                        self.logger.error("收到空响应")
                        return WorkflowResult(success=False, error="收到空响应")
                    
                    # 检查API响应码
                    api_code = result.get("code")
                    if api_code == 0:
                        # 成功响应，提取任务ID
                        data = result.get("data") or {}
                        task_id = (
                            data.get("taskId") if isinstance(data, dict) else None or
                            data.get("task_id") if isinstance(data, dict) else None or
                            result.get("taskId") or
                            result.get("task_id")
                        )
                        if task_id:
                            return WorkflowResult(success=True, task_id=task_id)
                        else:
                            error_msg = "响应中未找到任务ID"
                            self.logger.error(f"创建工作流失败: {error_msg}")
                            return WorkflowResult(success=False, error=error_msg)
                    elif api_code == 421:
                        # 任务队列已满
                        error_msg = "ComfyUI任务队列已满，请稍后重试"
                        return WorkflowResult(success=False, error=error_msg)
                    else:
                        # 其他API错误
                        error_msg = result.get("message", f"API错误，代码: {api_code}")
                        self.logger.error(f"创建工作流失败: {error_msg}")
                        return WorkflowResult(success=False, error=error_msg)
                        
        except Exception as e:
            error_msg = f"创建工作流时发生异常: {str(e)}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, error=error_msg)
    
    async def create_video_workflow(self, image_file_name: str, prompt: str) -> WorkflowResult:
        """创建图生视频工作流"""
        if self.debug_mode:
            # 调试模式：模拟视频工作流创建成功
            mock_task_id = f"debug_video_task_{asyncio.get_event_loop().time():.0f}"
            self.logger.info(f"🔧 [调试模式] 模拟创建视频工作流，任务ID: {mock_task_id}")
            await asyncio.sleep(0.1)  # 模拟短暂延迟
            return WorkflowResult(success=True, task_id=mock_task_id)
        
        url = f"{self.config.base_url}/task/openapi/create"
        
        headers = {
            "host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        
        # 构建节点信息列表
        node_info_list = [
            {
                "nodeId": self.config.video_image_node_id,
                "fieldName": "image",
                "fieldValue": image_file_name
            },
            {
                "nodeId": self.config.video_prompt_node_id,
                "fieldName": "text",
                "fieldValue": prompt
            }
        ]
        
        payload = {
            "apiKey": self.config.api_key,
            "workflowId": self.config.video_workflow_id,
            "nodeInfoList": node_info_list
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            task_id = result.get('data', {}).get('taskId')
                            self.logger.info(f"图生视频工作流创建成功，任务ID: {task_id}")
                            return WorkflowResult(success=True, task_id=task_id)
                        else:
                            error_msg = result.get('message', '未知错误')
                            self.logger.error(f"图生视频工作流创建失败: {error_msg}")
                            return WorkflowResult(success=False, error=error_msg)
                    else:
                        error_msg = f"HTTP错误: {response.status}"
                        self.logger.error(f"图生视频工作流创建失败: {error_msg}")
                        return WorkflowResult(success=False, error=error_msg)
                        
        except Exception as e:
            error_msg = f"图生视频工作流创建异常: {str(e)}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, error=error_msg)
    
    async def process_video_workflow(self, image_file_path: str, prompt: str) -> WorkflowResult:
        """处理图生视频完整工作流"""
        if self.debug_mode:
            # 调试模式：模拟完整视频工作流处理
            self.logger.info(f"🔧 [调试模式] 模拟处理视频工作流: {image_file_path}")
            await asyncio.sleep(1)  # 模拟处理时间
            mock_task_id = f"debug_video_complete_{asyncio.get_event_loop().time():.0f}"
            mock_output_urls = [f"https://mock-video-url.com/{mock_task_id}_result.mp4"]
            return WorkflowResult(
                success=True,
                task_id=mock_task_id,
                status="SUCCESS",
                output_urls=mock_output_urls
            )
        
        try:
            # 1. 上传图片
            self.logger.info("开始上传图片用于视频生成...")
            with open(image_file_path, 'rb') as f:
                image_data = f.read()
            
            upload_result = await self.upload_image(image_data, f"video_input_{image_file_path.split('/')[-1]}")
            if not upload_result.success:
                return WorkflowResult(success=False, error=f"图片上传失败: {upload_result.error}")
            
            self.logger.info(f"图片上传成功: {upload_result.file_name}")
            
            # 2. 创建视频工作流
            self.logger.info("创建图生视频工作流...")
            workflow_result = await self.create_video_workflow(upload_result.file_name, prompt)
            if not workflow_result.success:
                return workflow_result
            
            # 3. 等待5秒后开始检查状态
            self.logger.info("等待5秒后开始检查任务状态")
            await asyncio.sleep(5)
            
            # 4. 等待完成
            self.logger.info("开始检查视频生成状态")
            final_result = await self.wait_for_completion(workflow_result.task_id, max_wait_time=600, check_interval=30)
            
            return final_result
            
        except Exception as e:
            error_msg = f"图生视频工作流处理异常: {str(e)}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, error=error_msg)
    
    async def check_task_status(self, task_id: str) -> WorkflowResult:
        """检查任务状态"""
        url = f"{self.config.base_url}/task/openapi/status"
        
        headers = {
            "Host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        
        payload = {
            "apiKey": self.config.api_key,
            "taskId": task_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            data = result.get('data')
                            # data可能是字符串（直接的状态值）或对象（包含status字段）
                            if isinstance(data, str):
                                status = data
                            elif isinstance(data, dict):
                                status = data.get('status')
                            else:
                                status = None
                            return WorkflowResult(success=True, task_id=task_id, status=status)
                        else:
                            # 处理API返回的错误信息，优先使用msg字段
                            error_msg = result.get('msg', result.get('message', '未知错误'))
                            self.logger.error(f"检查任务状态失败 - API返回码: {result.get('code')}, 错误信息: {error_msg}")
                            return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                    else:
                        error_msg = f"HTTP错误: {response.status}"
                        self.logger.error(f"检查任务状态失败: {error_msg}")
                        return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                        
        except Exception as e:
            error_msg = f"检查任务状态异常: {str(e)}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, task_id=task_id, error=error_msg)
    
    async def get_task_outputs(self, task_id: str) -> WorkflowResult:
        """获取任务输出结果"""
        url = f"{self.config.base_url}/task/openapi/outputs"
        
        headers = {
            "Host": "www.runninghub.cn",
            "Content-Type": "application/json"
        }
        
        payload = {
            "apiKey": self.config.api_key,
            "taskId": task_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            data = result.get('data', {})
                            # 处理data可能是字典或列表的情况
                            if isinstance(data, dict):
                                outputs = data.get('outputs', [])
                            elif isinstance(data, list):
                                outputs = data
                            else:
                                outputs = []
                            
                            output_urls = []
                            for output in outputs:
                                if isinstance(output, dict):
                                    # 检查不同的URL字段名
                                    if 'fileUrl' in output:
                                        output_urls.append(output['fileUrl'])
                                    elif 'url' in output:
                                        output_urls.append(output['url'])
                                elif isinstance(output, str):
                                    output_urls.append(output)
                            
                            return WorkflowResult(success=True, task_id=task_id, output_urls=output_urls)
                        else:
                            # 处理API返回的错误信息，优先使用msg字段
                            error_msg = result.get('msg', result.get('message', '未知错误'))
                            self.logger.error(f"获取任务输出失败 - API返回码: {result.get('code')}, 错误信息: {error_msg}")
                            return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                    else:
                        error_msg = f"HTTP错误: {response.status}"
                        self.logger.error(f"获取任务输出失败: {error_msg}")
                        return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                        
        except Exception as e:
            error_msg = f"获取任务输出异常: {str(e)}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, task_id=task_id, error=error_msg)
    
    async def download_result(self, file_url: str) -> bytes:
        """下载结果文件"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        file_data = await response.read()
                        # 结果文件下载成功
                        return file_data
                    else:
                        raise Exception(f"下载失败，HTTP状态码: {response.status}")
        except Exception as e:
            self.logger.error(f"下载结果文件失败: {str(e)}")
            raise
    
    async def wait_for_completion(self, task_id: str, max_wait_time: int = 300, check_interval: int = 30) -> WorkflowResult:
        """等待任务完成"""
        if self.debug_mode:
            # 调试模式：模拟任务完成
            self.logger.info(f"🔧 [调试模式] 模拟等待任务完成: {task_id}")
            await asyncio.sleep(1)  # 模拟短暂处理时间
            mock_output_urls = [f"https://mock-output-url.com/{task_id}_result.png"]
            return WorkflowResult(
                success=True,
                task_id=task_id,
                status="SUCCESS",
                output_urls=mock_output_urls
            )
        
        start_time = asyncio.get_event_loop().time()
        consecutive_failures = 0
        max_consecutive_failures = 3
        retry_interval = 10
        

        
        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed_time = current_time - start_time
            
            # 检查是否超时
            if elapsed_time > max_wait_time:
                error_msg = f"等待任务完成超时 ({max_wait_time}秒)"
                self.logger.error(f"           ❌ {error_msg}")
                return WorkflowResult(success=False, task_id=task_id, error=error_msg)
            
            # 检查任务状态
            status_result = await self.check_task_status(task_id)
            
            # 如果状态检查失败，记录连续失败次数
            if not status_result.success:
                consecutive_failures += 1
                
                # 如果连续失败次数达到上限，返回错误
                if consecutive_failures >= max_consecutive_failures:
                    error_msg = f"状态检查连续失败 {max_consecutive_failures} 次: {status_result.error}"
                    self.logger.error(f"❌ {error_msg}")
                    return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                
                # 等待重试间隔后继续
                await asyncio.sleep(retry_interval)
                continue
            
            # 状态检查成功，重置连续失败计数
            consecutive_failures = 0
            
            status = status_result.status
            
            if status == "SUCCESS":
                # 任务成功完成，获取输出
                output_result = await self.get_task_outputs(task_id)
                if output_result.success:
                    return WorkflowResult(
                        success=True,
                        task_id=task_id,
                        status=status,
                        output_urls=output_result.output_urls
                    )
                else:
                    self.logger.error(f"❌ 获取输出文件失败: {output_result.error}")
                    return WorkflowResult(success=False, task_id=task_id, error=f"获取输出失败: {output_result.error}")
                    
            elif status == "FAILED":
                error_msg = "任务执行失败"
                self.logger.error(f"❌ {error_msg}")
                return WorkflowResult(success=False, task_id=task_id, error=error_msg)
                
            elif status in ["QUEUED", "RUNNING"]:
                # 任务仍在进行中，显示已等待时间并继续等待
                elapsed_minutes = int(elapsed_time // 60)
                elapsed_seconds = int(elapsed_time % 60)
                self.logger.info(f"        🔸 子步骤4: 等待工作流执行完成 (已等待 {elapsed_minutes}分{elapsed_seconds}秒)")
                await asyncio.sleep(check_interval)
                continue
                
            else:
                # 未知状态
                await asyncio.sleep(check_interval)
                continue
    
    async def process_workflow(self, product_image_data: bytes, model_image_data: bytes, prompt: str = None) -> WorkflowResult:
        """处理完整工作流"""
        try:
            # 1. 上传产品图片
            self.logger.info("        - 上传产品图片...")
            product_upload = await self.upload_image(product_image_data, "product.png")
            if not product_upload.success:
                return WorkflowResult(success=False, error=f"产品图片上传失败: {product_upload.error}")
            
            self.logger.info("        ✅ 产品图片上传成功")
            
            # 2. 上传模特图片
            self.logger.info("        - 上传模特图片...")
            model_upload = await self.upload_image(model_image_data, "model.png")
            if not model_upload.success:
                return WorkflowResult(success=False, error=f"模特图片上传失败: {model_upload.error}")
            
            self.logger.info("        ✅ 模特图片上传成功")
            
            # 3. 创建工作流
            self.logger.info("        - 创建ComfyUI工作流...")
            workflow_result = await self.create_workflow(product_upload.file_name, model_upload.file_name)
            if not workflow_result.success:
                return workflow_result
            
            self.logger.info(f"        ✅ 工作流创建成功，任务ID: {workflow_result.task_id}")
            
            # 4. 等待完成
            self.logger.info("        🔸 子步骤4: 等待工作流执行完成")
            final_result = await self.wait_for_completion(workflow_result.task_id, 
                                                         max_wait_time=self.config.task_check_interval * 5,
                                                         check_interval=self.config.task_check_interval)
            
            return final_result
            
        except Exception as e:
            error_msg = f"处理工作流时发生异常: {str(e)}"
            self.logger.error(f"        ❌ {error_msg}")
            return WorkflowResult(success=False, error=error_msg)