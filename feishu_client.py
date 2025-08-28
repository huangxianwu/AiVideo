#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书API客户端 - 处理飞书认证、表格数据获取和图片下载
"""

import asyncio
import aiohttp
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from config import FeishuConfig


@dataclass
class RowData:
    """表格行数据"""
    row_number: int
    product_image: Union[str, Dict[str, Any]]  # B列：产品图
    model_image: Union[str, Dict[str, Any]]    # D列：模特图
    prompt: str                                # G列：提示词
    status: str                                # H列：图片是否已处理
    composite_image: str = ""                  # F列：产品模特合成图
    product_name: str = ""                     # C列：产品名
    model_name: str = ""                       # E列：模特名
    video_status: str = ""                     # I列：视频是否已实现
    original_data: List[Any] = None


class FeishuClient:
    """飞书API客户端"""
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
    async def get_access_token(self) -> str:
        """获取飞书访问令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        
        payload = {
            "app_id": self.config.app_id,
            "app_secret": self.config.app_secret
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"获取token失败: code={data.get('code')}, msg={data.get('msg')}")
                
                self.access_token = data.get("tenant_access_token")
                self.logger.info("Token获取成功")
                return self.access_token
    
    async def get_sheet_info(self) -> Dict[str, Any]:
        """获取工作表信息"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{self.config.spreadsheet_token}/sheets/query"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"获取工作表信息失败: {data.get('msg')}")
                
                sheets = data.get("data", {}).get("sheets", [])
                if not sheets:
                    raise Exception("表格中没有找到任何工作表")
                
                # 查找目标工作表
                target_sheet = None
                if self.config.sheet_name:
                    target_sheet = next((s for s in sheets if s.get("title") == self.config.sheet_name), None)
                
                if not target_sheet:
                    target_sheet = sheets[0]
                    self.logger.warning(f"未找到工作表 '{self.config.sheet_name}'，使用第一个工作表: {target_sheet.get('title')}")
                else:
                    # self.logger.info(f"找到目标工作表: {target_sheet.get('title')}")
                    pass
                
                return {
                    "sheet_id": target_sheet.get("sheet_id"),
                    "sheet_title": target_sheet.get("title"),
                    "all_sheets": [{"id": s.get("sheet_id"), "title": s.get("title")} for s in sheets]
                }
    
    async def get_sheet_data(self) -> List[RowData]:
        """获取表格数据"""
        try:
            # 获取工作表信息
            sheet_info = await self.get_sheet_info()
            sheet_id = sheet_info["sheet_id"]
            
            # 构建请求
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values/{sheet_id}!{self.config.range}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # 发送API请求
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    
                    if data.get("code") != 0:
                        self.logger.error(f"❌ API请求失败: {data.get('msg')}")
                        raise Exception(f"获取单元格数据失败: {data.get('msg')}")
                    
                    # 解析响应数据
                    value_range = data.get("data", {}).get("valueRange", {})
                    values = value_range.get("values", [])
                    
                    if not values:
                        self.logger.warning("⚠️ 表格数据为空")
                        return []
                    
                    # 解析表格数据
                    parsed_data = self._parse_sheet_data(values)
                    
                    return parsed_data
                    
        except Exception as e:
            self.logger.error(f"❌ 获取表格数据时发生错误: {str(e)}")
            raise
    
    def _parse_sheet_data(self, values: List[List[Any]]) -> List[RowData]:
        """解析表格数据"""
        processed_data = []
        
        # 检查是否有表头行
        header_row_index = -1
        column_mapping = {}
        
        if values and self._is_header_row(values[0]):
            header_row_index = 0
            header_row = values[0]
            # 建立列名到索引的映射
            for i, cell in enumerate(header_row):
                if cell:
                    cell_str = str(cell).strip().lower()
                    if self.config.product_image_column.lower() in cell_str:
                        column_mapping['product_image'] = i
                    elif self.config.model_image_column.lower() in cell_str:
                        column_mapping['model_image'] = i
                    elif self.config.prompt_column.lower() in cell_str:
                        column_mapping['prompt'] = i
                    elif self.config.status_column.lower() in cell_str:
                        column_mapping['status'] = i
                    elif self.config.composite_image_column.lower() in cell_str:
                        column_mapping['composite_image'] = i
                    elif self.config.product_name_column.lower() in cell_str:
                        column_mapping['product_name'] = i
                    elif self.config.model_name_column.lower() in cell_str:
                        column_mapping['model_name'] = i
                    elif self.config.video_status_column.lower() in cell_str:
                        column_mapping['video_status'] = i
        
        # 如果没有表头行，使用默认索引（根据用户纠正的列映射）
        if not column_mapping:
            column_mapping = {
                'product_image': 1,     # B列：产品图
                'model_image': 3,       # D列：模特图
                'prompt': 6,            # G列：提示词
                'status': 7,            # H列：图片是否已处理
                'composite_image': 5,   # F列：产品模特合成图
                'product_name': 2,      # C列：产品名
                'model_name': 4,        # E列：模特名
                'video_status': 8       # I列：视频是否已实现
            }

        
        self.logger.info(f"列映射: {column_mapping}")
        
        # 处理数据行
        data_start_index = header_row_index + 1 if header_row_index >= 0 else 0
        data_rows = values[data_start_index:]
        
        for i, row in enumerate(data_rows):
            if not self._has_content(row):
                continue
            
            # 使用列映射获取数据
            product_image_idx = column_mapping.get('product_image', 0)
            model_image_idx = column_mapping.get('model_image', 1)
            prompt_idx = column_mapping.get('prompt', 2)
            status_idx = column_mapping.get('status', 3)
            composite_image_idx = column_mapping.get('composite_image', 4)
            product_name_idx = column_mapping.get('product_name', 5)
            model_name_idx = column_mapping.get('model_name', 7)
            video_status_idx = column_mapping.get('video_status', 8)
            
            # 解析行数据
            
            row_data = RowData(
                row_number=data_start_index + i + 2,  # +2 因为表格行号从1开始，且要跳过表头
                product_image=self._parse_cell_data(row[product_image_idx] if len(row) > product_image_idx else None),
                model_image=self._parse_cell_data(row[model_image_idx] if len(row) > model_image_idx else None),
                prompt=str(row[prompt_idx]).strip() if len(row) > prompt_idx and row[prompt_idx] else "",
                status=str(row[status_idx]).strip() if len(row) > status_idx and row[status_idx] else "",
                composite_image=self._parse_cell_data(row[composite_image_idx] if len(row) > composite_image_idx else None),
                product_name=str(row[product_name_idx]).strip() if len(row) > product_name_idx and row[product_name_idx] else "",
                model_name=str(row[model_name_idx]).strip() if len(row) > model_name_idx and row[model_name_idx] else "",
                video_status=str(row[video_status_idx]).strip() if len(row) > video_status_idx and row[video_status_idx] else "",
                original_data=row
            )
            
            # 产品名解析完成
            
            processed_data.append(row_data)
        
        self.logger.info(f"处理了 {len(processed_data)} 行有效数据")
        return processed_data
    
    def _is_header_row(self, row: List[Any]) -> bool:
        """检查是否是表头行"""
        if not row:
            return False
        
        header_keywords = ['产品图', '模特图', '提示词', '是否已读取', 'product', 'model', 'prompt', 'read']
        return any(
            cell and isinstance(cell, str) and 
            any(keyword.lower() in cell.lower() for keyword in header_keywords)
            for cell in row
        )
    
    def _has_content(self, row: List[Any]) -> bool:
        """检查行是否有内容"""
        return any(cell and str(cell).strip() for cell in row)
    
    def _parse_cell_data(self, cell: Any) -> Union[str, Dict[str, Any]]:
        """解析单元格数据，处理嵌入式图片"""
        if not cell:
            return ""
        
        if isinstance(cell, str):
            return cell.strip()
        
        # 处理嵌入式图片
        if isinstance(cell, dict) and cell.get("type") == "embed-image" and cell.get("fileToken"):
            return {
                "type": "embed-image",
                "fileToken": cell["fileToken"]
            }
        
        return str(cell).strip()
    
    async def _get_column_letter_by_header(self, header_name: str) -> Optional[str]:
        """根据表头名称获取列字母"""
        try:
            # 获取原始表格数据
            sheet_info = await self.get_sheet_info()
            sheet_id = sheet_info["sheet_id"]
            
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values/{sheet_id}!A1:Z1"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self.logger.error(f"获取表头失败: HTTP {response.status}")
                        return None
                    
                    data = await response.json()
                    if data.get("code") != 0:
                        self.logger.error(f"获取表头失败: {data.get('msg')}")
                        return None
                    
                    # 调试信息：打印返回的数据结构
                    self.logger.debug(f"API返回数据: {data}")
                    
                    values = data.get("data", {}).get("values", [])
                    if not values:
                        # 尝试其他可能的数据结构
                        values = data.get("data", {}).get("valueRange", {}).get("values", [])
                    
                    if not values or not values[0]:
                        self.logger.error(f"未找到表头行，返回数据结构: {data}")
                        return None
                    
                    header_row = values[0]
                    for i, cell in enumerate(header_row):
                        if cell and header_name.lower() in str(cell).strip().lower():
                            # 将索引转换为列字母 (0->A, 1->B, 2->C, ...)
                            return chr(65 + i)  # 65是'A'的ASCII码
                    
                    self.logger.error(f"未找到包含'{header_name}'的列")
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取列字母异常: {str(e)}")
            return None
    
    async def download_image(self, file_token: str) -> bytes:
        """下载图片文件"""
        if not self.access_token:
            await self.get_access_token()
            
        url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_token}/download"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"下载图片失败: HTTP {response.status}")
                
                return await response.read()
    
    async def update_cell_status(self, row_number: int, status: str) -> bool:
        """更新单元格状态"""
        try:
            sheet_info = await self.get_sheet_info()
            sheet_id = sheet_info["sheet_id"]
            
            # 动态获取状态列位置
            status_column_letter = await self._get_column_letter_by_header(self.config.status_column)
            if not status_column_letter:
                self.logger.error(f"无法找到'{self.config.status_column}'列")
                return False
            
            cell_range = f"{sheet_id}!{status_column_letter}{row_number}:{status_column_letter}{row_number}"
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "valueRange": {
                    "range": cell_range,
                    "values": [[status]]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        self.logger.error(f"更新状态失败: HTTP {response.status}, 响应: {response_text}")
                        return False
                    
                    try:
                        data = await response.json()
                        if data.get("code") != 0:
                            self.logger.error(f"更新状态失败: {data.get('msg')}")
                            return False
                        
                        self.logger.info(f"行 {row_number} 状态更新为: {status}")
                        return True
                    except Exception as json_error:
                        response_text = await response.text()
                        self.logger.error(f"解析响应JSON失败: {json_error}, 响应内容: {response_text}")
                        return False
                    
        except Exception as e:
            self.logger.error(f"更新状态异常: {str(e)}")
            return False
    
    async def upload_image_to_feishu(self, image_path: str) -> Optional[str]:
        """上传图片到飞书云空间"""
        try:
            access_token = await self.get_access_token()
            url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # 准备文件数据
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            # 构建multipart/form-data
            data = aiohttp.FormData()
            data.add_field('file_name', os.path.basename(image_path))
            data.add_field('parent_type', 'sheet_image')
            data.add_field('parent_node', self.config.spreadsheet_token)
            data.add_field('size', str(len(file_data)))
            data.add_field('file', file_data, filename=os.path.basename(image_path), content_type='image/png')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    result = await response.json()
                    
                    if result.get("code") != 0:
                        self.logger.error(f"上传图片失败: {result.get('msg')}")
                        return None
                    
                    file_token = result.get("data", {}).get("file_token")
                    self.logger.info(f"图片上传成功，file_token: {file_token}")
                    return file_token
                    
        except Exception as e:
            self.logger.error(f"上传图片异常: {str(e)}")
            return None
    
    async def write_image_to_cell(self, row_number: int, image_path: str) -> bool:
        """将图片写入表格指定单元格"""
        try:
            access_token = await self.get_access_token()
            
            # 获取sheet_id
            sheet_info = await self.get_sheet_info()
            sheet_id = sheet_info.get("sheet_id")
            if not sheet_id:
                self.logger.error("无法获取sheet_id")
                return False
            
            # 动态获取合成图列位置
            composite_column_letter = await self._get_column_letter_by_header(self.config.composite_image_column)
            if not composite_column_letter:
                self.logger.error(f"无法找到'{self.config.composite_image_column}'列")
                return False
            
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values_image"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 使用动态获取的合成图列位置
            cell_range = f"{sheet_id}!{composite_column_letter}{row_number}:{composite_column_letter}{row_number}"
            
            # 读取图片二进制数据
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 将二进制数据转换为字节数组
            image_bytes = list(image_data)
            
            payload = {
                "range": cell_range,
                "image": image_bytes,
                "name": os.path.basename(image_path)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    
                    if data.get("code") != 0:
                        self.logger.error(f"写入图片失败: {data.get('msg')}")
                        return False
                    
                    self.logger.info("图片写入成功")
                    return True
                    
        except Exception as e:
            self.logger.error(f"写入图片异常: {str(e)}")
            return False
    
    async def update_video_status(self, row_number: int, video_status: str) -> bool:
        """更新视频状态到I列"""
        try:
            sheet_info = await self.get_sheet_info()
            sheet_id = sheet_info["sheet_id"]
            
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 构建单元格范围 (I列)
            cell_range = f"{sheet_id}!{self.config.video_status_column}{row_number}:{self.config.video_status_column}{row_number}"
            
            payload = {
                "valueRange": {
                    "range": cell_range,
                    "values": [[video_status]]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    
                    if data.get("code") != 0:
                        self.logger.error(f"更新视频状态失败: {data.get('msg')}")
                        return False
                    
                    self.logger.info(f"视频状态更新成功到单元格: {cell_range}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"更新视频状态异常: {str(e)}")
            return False