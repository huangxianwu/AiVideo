#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试模式测试脚本
用于快速测试工作流功能而不调用实际的ComfyUI API
"""

import subprocess
import sys
from datetime import datetime

def run_test(test_name, command):
    """运行测试并记录结果"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {test_name}")
    print(f"📝 命令: {command}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️  执行时间: {duration:.2f} 秒")
        print(f"🔄 退出码: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ 测试成功")
        else:
            print("❌ 测试失败")
            print(f"错误输出: {result.stderr}")
            
        return result.returncode == 0, duration
        
    except subprocess.TimeoutExpired:
        print("⏰ 测试超时 (60秒)")
        return False, 60.0
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False, 0.0

def main():
    """主测试函数"""
    print("🚀 开始调试模式测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("图片合成工作流 (调试模式)", "echo '1' | python main.py --debug"),
        ("图生视频工作流 (调试模式)", "echo '2' | python main.py --debug"),
        ("完整工作流 (调试模式)", "echo '3' | python main.py --debug"),
    ]
    
    results = []
    total_time = 0
    
    for test_name, command in tests:
        success, duration = run_test(test_name, command)
        results.append((test_name, success, duration))
        total_time += duration
    
    # 生成测试报告
    print(f"\n\n{'='*80}")
    print("📊 调试模式测试报告")
    print(f"{'='*80}")
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"📈 总体统计:")
    print(f"   - 总测试数: {total_count}")
    print(f"   - 成功: {success_count}")
    print(f"   - 失败: {total_count - success_count}")
    print(f"   - 成功率: {success_count/total_count*100:.1f}%")
    print(f"   - 总耗时: {total_time:.2f} 秒")
    print(f"   - 平均耗时: {total_time/total_count:.2f} 秒/测试")
    
    print(f"\n📋 详细结果:")
    for test_name, success, duration in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   - {test_name}: {status} ({duration:.2f}s)")
    
    print(f"\n💡 调试模式优势:")
    print(f"   - 跳过耗时的ComfyUI API调用")
    print(f"   - 快速验证工作流逻辑")
    print(f"   - 适合功能开发和调试")
    print(f"   - 生成模拟结果文件")
    
    if success_count == total_count:
        print(f"\n🎉 所有测试通过！调试模式工作正常。")
        return 0
    else:
        print(f"\n⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())