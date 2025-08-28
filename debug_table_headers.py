#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格表头和列映射调试工具
根据用户纠正的列映射重新分析表格结构
"""

import asyncio
from config import config
from feishu_client import FeishuClient

class TableHeaderDebugger:
    def __init__(self):
        self.config = config
        self.feishu_client = FeishuClient(self.config.feishu)
    
    async def debug_headers(self):
        print("\n" + "="*80)
        print("🔍 表格表头和列映射调试 - 根据用户纠正重新分析")
        print("="*80)
        
        try:
            # 获取表格数据
            print("正在获取表格数据...")
            rows_data = await self.feishu_client.get_sheet_data()
            print(f"获取到 {len(rows_data)} 行数据")
            
            if rows_data:
                print("\n📋 根据用户纠正的列映射分析前3行数据:")
                print("-"*80)
                print("用户纠正的列映射:")
                print("- A列: [未明确]")
                print("- B列: 产品图 (用于图片合成)")
                print("- C列: 产品名 (用于视频文件名)")
                print("- D列: 模特图 (用于图片合成)")
                print("- E列: 模特名 (用于视频文件名)")
                print("- F列: 产品模特合成图 (图片合成结果)")
                print("- G列: 提示词 (用于图生视频)")
                print("- H列: 图片是否已处理 (图片合成状态)")
                print("- I列: 视频是否已实现 (视频生成状态)")
                print()
                
                # 分析前3行数据
                for i, row in enumerate(rows_data[:3]):
                    print(f"\n第 {row.row_number} 行数据分析:")
                    print(f"  当前映射 -> 实际数据类型和内容")
                    print(f"  产品图 (当前映射到A): {type(row.product_image).__name__} - {str(row.product_image)[:80]}...")
                    print(f"  模特图 (当前映射到B): {type(row.model_image).__name__} - {str(row.model_image)[:80]}...")
                    print(f"  提示词 (当前映射到C): {type(row.prompt).__name__} - '{row.prompt}'")
                    print(f"  状态 (当前映射到D): {type(row.status).__name__} - {str(row.status)[:80]}...")
                    print(f"  合成图 (当前映射到E): {type(row.composite_image).__name__} - '{row.composite_image}'")
                    print(f"  产品名 (当前映射到F): {type(row.product_name).__name__} - {str(row.product_name)[:80]}...")
                    print(f"  模特名 (当前映射到H): {type(row.model_name).__name__} - '{row.model_name}'")
                    print(f"  视频状态 (当前映射到I): {type(row.video_status).__name__} - '{row.video_status}'")
                
                # 获取原始数据进行对比
                print("\n🔍 获取原始表格数据进行对比分析:")
                print("-"*50)
                
                access_token = await self.feishu_client.get_access_token()
                import aiohttp
                
                url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.feishu.spreadsheet_token}/values/{self.config.feishu.sheet_name}!A1:I5"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            values = data.get('data', {}).get('values', [])
                            
                            if values:
                                print(f"\n📋 原始表格数据（前5行，按列分析）:")
                                print("-"*80)
                                
                                # 分析每一列的数据
                                for col_idx in range(min(9, len(values[0]) if values else 0)):
                                    col_letter = chr(ord('A') + col_idx)
                                    print(f"\n{col_letter}列数据:")
                                    for row_idx, row in enumerate(values[:5]):
                                        if col_idx < len(row):
                                            cell_value = row[col_idx]
                                            cell_type = type(cell_value).__name__
                                            if isinstance(cell_value, dict):
                                                print(f"  第{row_idx+1}行: {cell_type} - {str(cell_value)[:60]}...")
                                            else:
                                                print(f"  第{row_idx+1}行: {cell_type} - '{cell_value}'")
                                        else:
                                            print(f"  第{row_idx+1}行: 空")
                                
                                print("\n🎯 列映射纠正建议:")
                                print("-"*50)
                                print("根据用户说明和实际数据，正确的列映射应该是:")
                                print("- A列: [需要确认具体内容]")
                                print("- B列: 产品图 (用于图片合成输入)")
                                print("- C列: 产品名 (用于视频文件名)")
                                print("- D列: 模特图 (用于图片合成输入)")
                                print("- E列: 模特名 (用于视频文件名)")
                                print("- F列: 产品模特合成图 (图片合成输出)")
                                print("- G列: 提示词 (用于图生视频输入)")
                                print("- H列: 图片是否已处理 (图片合成状态判断)")
                                print("- I列: 视频是否已实现 (视频生成状态判断)")
                                
                            else:
                                print("未获取到原始数据")
                        else:
                            print(f"API调用失败: {response.status}")
            else:
                print("❌ 没有获取到表格数据")
                
        except Exception as e:
            print(f"❌ 调试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("调试完成")
        print("="*80)

if __name__ == "__main__":
    debugger = TableHeaderDebugger()
    asyncio.run(debugger.debug_headers())