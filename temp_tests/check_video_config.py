#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频工作流配置检查工具
用于快速诊断 video_workflow_enabled 配置问题
"""

import os
from config import config

def check_video_config():
    """检查视频工作流配置状态"""
    print("🔍 视频工作流配置检查")
    print("=" * 50)
    
    # 检查环境变量
    print("📋 环境变量检查:")
    video_env = os.getenv("VIDEO_WORKFLOW_ENABLED")
    comfyui_video_env = os.getenv("COMFYUI_VIDEO_WORKFLOW_ENABLED")
    
    print(f"   VIDEO_WORKFLOW_ENABLED = '{video_env}'")
    print(f"   COMFYUI_VIDEO_WORKFLOW_ENABLED = '{comfyui_video_env}'")
    
    # 分析环境变量状态
    if video_env is None:
        print("   ✅ VIDEO_WORKFLOW_ENABLED 未设置，将使用默认值 'true'")
    elif video_env.lower() == "true":
        print("   ✅ VIDEO_WORKFLOW_ENABLED 正确设置为 'true'")
    else:
        print(f"   ❌ VIDEO_WORKFLOW_ENABLED 设置为 '{video_env}'，这会禁用视频工作流！")
        print("   💡 解决方案: export VIDEO_WORKFLOW_ENABLED=true")
    
    if comfyui_video_env is not None:
        print(f"   ⚠️  发现 COMFYUI_VIDEO_WORKFLOW_ENABLED='{comfyui_video_env}'")
        print("   💡 注意: 这个环境变量不会被使用，请使用 VIDEO_WORKFLOW_ENABLED")
    
    print()
    
    # 检查最终配置值
    print("⚙️ 最终配置值:")
    print(f"   config.comfyui.video_workflow_enabled = {config.comfyui.video_workflow_enabled}")
    print(f"   config.comfyui.video_workflow_id = {config.comfyui.video_workflow_id}")
    print(f"   config.comfyui.video_image_node_id = {config.comfyui.video_image_node_id}")
    print(f"   config.comfyui.video_prompt_node_id = {config.comfyui.video_prompt_node_id}")
    
    print()
    
    # 给出诊断结果
    print("🏥 诊断结果:")
    if config.comfyui.video_workflow_enabled:
        print("   ✅ 视频工作流已启用")
        print("   💡 如果图生视频仍被跳过，请检查:")
        print("      - 视频状态是否为 '否'")
        print("      - 是否有产品模特合成图")
        print("      - 是否有提示词")
    else:
        print("   ❌ 视频工作流被禁用！")
        print("   💡 解决方案:")
        print("      1. 设置环境变量: export VIDEO_WORKFLOW_ENABLED=true")
        print("      2. 或者在 .env 文件中添加: VIDEO_WORKFLOW_ENABLED=true")
        print("      3. 重新运行程序")
    
    print()
    print("📝 环境变量设置示例:")
    print("   # 在终端中设置")
    print("   export VIDEO_WORKFLOW_ENABLED=true")
    print()
    print("   # 或在 .env 文件中添加")
    print("   VIDEO_WORKFLOW_ENABLED=true")
    print()
    print("=" * 50)

if __name__ == "__main__":
    check_video_config()