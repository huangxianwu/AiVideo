#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 管理飞书和ComfyUI的配置参数
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class FeishuConfig:
    """飞书配置"""
    app_id: str
    app_secret: str
    spreadsheet_token: str
    sheet_name: str
    range: str = "A2:I1000"  # 扩大范围到I列
    
    # 列映射配置 - 基于表头名称识别，不依赖固定位置
    product_image_column: str = "产品图"  # 产品图列表头关键词
    model_image_column: str = "模特图"    # 模特图列表头关键词
    prompt_column: str = "提示词"         # 提示词列表头关键词
    status_column: str = "图片是否已处理"  # 状态列表头关键词
    composite_image_column: str = "产品模特合成图"  # 合成图列表头关键词
    product_name_column: str = "产品名"   # 产品名列表头关键词
    model_name_column: str = "模特名"     # 模特名列表头关键词
    video_status_column: str = "视频是否已实现"   # 视频状态列表头关键词


@dataclass
class ComfyUIConfig:
    """ComfyUI配置"""
    api_key: str
    workflow_id: str
    base_url: str = "https://www.runninghub.cn"
    
    # 图片合成工作流节点ID映射 - 对应n8n工作流中的nodeInfoList
    product_image_node_id: str = "156"  # 产品图节点ID
    model_image_node_id: str = "145"    # 模特图节点ID
    prompt_node_id: str = "30"          # 提示词节点ID
    
    # 图生视频工作流配置
    video_workflow_enabled: bool = True  # 视频工作流开关
    video_workflow_id: str = "1959150471611101185"  # 图生视频工作流ID
    video_image_node_id: str = "293"     # 视频工作流图片节点ID
    video_prompt_node_id: str = "368"    # 视频工作流提示词节点ID
    
    # 任务队列管理配置
    task_check_interval: int = 120      # 任务状态检查间隔(秒) - 2分钟
    task_wait_interval: int = 30        # 任务等待间隔(秒) - 30秒
    task_max_wait_time: int = 1800      # 任务最大等待时间(秒) - 30分钟
    queue_enabled: bool = True          # 是否启用队列管理


@dataclass
class AppConfig:
    """应用配置"""
    feishu: FeishuConfig
    comfyui: ComfyUIConfig
    
    # 处理配置
    max_retries: int = 3
    retry_delay: int = 5  # 秒
    timeout: int = 300    # 秒
    
    # 文件配置
    temp_dir: str = "./temp"
    output_dir: str = "./output"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "workflow.log"


def load_config() -> AppConfig:
    """从环境变量或配置文件加载配置"""
    
    # 飞书配置
    feishu_config = FeishuConfig(
        app_id=os.getenv("FEISHU_APP_ID", "cli_a49bc51d84b9900e"),
        app_secret=os.getenv("FEISHU_APP_SECRET", "t0tVgm1aS0jnG5O6v7hUpextQqpVobD2"),
        spreadsheet_token=os.getenv("FEISHU_SPREADSHEET_TOKEN", "Og4isDZNPhhXQcteLJRcmdMPnjc"),
        sheet_name=os.getenv("FEISHU_SHEET_NAME", "prd_model_sheet"),
        range=os.getenv("FEISHU_RANGE", "A2:I1000")
    )
    
    # runninghub的ComfyUI配置
    comfyui_config = ComfyUIConfig(
        api_key=os.getenv("COMFYUI_API_KEY", "d4b17e6ea9474695965f3f3c9dd53c1d"),
        workflow_id=os.getenv("COMFYUI_WORKFLOW_ID", "1956307610033160194"),
        video_workflow_enabled=os.getenv("VIDEO_WORKFLOW_ENABLED", "true").lower() == "true",
        video_workflow_id=os.getenv("VIDEO_WORKFLOW_ID", "1959150471611101185"),
        video_image_node_id=os.getenv("VIDEO_IMAGE_NODE_ID", "293"),
        video_prompt_node_id=os.getenv("VIDEO_PROMPT_NODE_ID", "368")
    )
    
    return AppConfig(
        feishu=feishu_config,
        comfyui=comfyui_config,
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_delay=int(os.getenv("RETRY_DELAY", "5")),
        timeout=int(os.getenv("TIMEOUT", "300")),
        temp_dir=os.getenv("TEMP_DIR", "./temp"),
        output_dir=os.getenv("OUTPUT_DIR", "./output"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "workflow.log")
    )


# 全局配置实例
config = load_config()