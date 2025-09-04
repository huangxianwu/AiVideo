from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import requests
from datetime import datetime
import re
import threading
import time
import asyncio
import json
import cv2
from csv_processor import CSVProcessor
from png_processor import WhiteBackgroundRemover
from feishu_client import FeishuClient
from config import FeishuConfig
from data.workflow_manager import WorkflowManager, NodeType


app = Flask(__name__, static_folder='static')

class ProductManager:
    def __init__(self):
        self.imgdb_file = "images/csvdb/imgdb.csv"
        self.download_dir = "images/jpg"
        self.data = []
        self.load_data()
        
    def load_data(self):
        """加载产品数据"""
        try:
            if os.path.exists(self.imgdb_file):
                df = pd.read_csv(self.imgdb_file)
                self.data = df.to_dict('records')
            else:
                self.data = []
        except Exception as e:
            print(f"加载数据失败: {e}")
            self.data = []
    
    def get_paginated_data(self, page=1, per_page=50):
        """获取分页数据"""
        start = (page - 1) * per_page
        end = start + per_page
        
        total = len(self.data)
        total_pages = (total - 1) // per_page + 1 if total > 0 else 0
        
        # 获取分页数据并确保product_id作为字符串返回，避免JavaScript大数字精度问题
        items = self.data[start:end]
        for item in items:
            item['product_id'] = str(item['product_id'])
        
        return {
            'data': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    
    def download_images(self, selected_ids):
        """下载选中的图片"""
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 根据product_id查找数据
        selected_data = []
        downloaded_product_ids = []
        
        for product_id in selected_ids:
            for item in self.data:
                if str(item['product_id']) == str(product_id):
                    selected_data.append(item)
                    break
        
        success_count = 0
        
        for item in selected_data:
            try:
                filename = self._generate_filename(item['product_name'])
                filepath = os.path.join(self.download_dir, filename)
                
                response = requests.get(item['main_image_url'], timeout=10)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                success_count += 1
                downloaded_product_ids.append(str(item['product_id']))
                
            except Exception as e:
                print(f"下载失败 {item['product_name']}: {e}")
        
        # 更新下载状态
        if downloaded_product_ids:
            self.update_download_status(downloaded_product_ids)
        
        return success_count, len(selected_data)
    
    def update_download_status(self, product_ids):
        """更新产品的下载状态"""
        try:
            df = pd.read_csv(self.imgdb_file)
            
            # 更新is_downloaded状态
            for product_id in product_ids:
                df.loc[df['product_id'] == int(product_id), 'is_downloaded'] = True
            
            # 保存回CSV文件
            df.to_csv(self.imgdb_file, index=False)
            
            # 重新加载数据
            self.load_data()
            
            print(f"已更新 {len(product_ids)} 个产品的下载状态")
            
        except Exception as e:
            print(f"更新下载状态失败: {e}")
    
    def get_downloaded_products(self):
        """获取已下载的产品"""
        downloaded_items = [item for item in self.data if item.get('is_downloaded', False)]
        # 确保product_id作为字符串返回
        for item in downloaded_items:
            item['product_id'] = str(item['product_id'])
        return downloaded_items
    
    def _generate_filename(self, product_name):
        """生成文件名：MMDD+产品名称前3个单词"""
        now = datetime.now()
        mmdd = now.strftime("%m%d")
        
        words = re.findall(r'\b\w+\b', product_name)
        first_three_words = '_'.join(words[:3]) if len(words) >= 3 else '_'.join(words)
        first_three_words = re.sub(r'[^\w\-_]', '', first_three_words)
        
        return f"{mmdd}_{first_three_words}.jpg"

# 全局产品管理器
product_manager = ProductManager()
workflow_manager = WorkflowManager()

@app.route('/')
def index():
    """主页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    data = product_manager.get_paginated_data(page, per_page)
    return render_template('index.html', **data)

@app.route('/erp')
def erp_index():
    """ERP系统主页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = product_manager.get_paginated_data(page, per_page)
    
    return render_template('erp_index.html', 
                           data=pagination['data'],
                           page=pagination['page'],
                           per_page=pagination['per_page'],
                           total=pagination['total'],
                           total_pages=pagination['total_pages'],
                           has_prev=pagination['has_prev'],
                           has_next=pagination['has_next'])

@app.route('/api/data')
def api_data():
    """API接口获取数据"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    data = product_manager.get_paginated_data(page, per_page)
    return jsonify(data)

@app.route('/api/download', methods=['POST'])
def api_download():
    """下载选中的图片"""
    try:
        selected_ids = request.json.get('product_ids', [])
        
        if not selected_ids:
            return jsonify({'success': False, 'message': '请选择要下载的图片'})
        
        # 在后台线程中下载
        def download_thread():
            return product_manager.download_images(selected_ids)
        
        success_count, total_count = download_thread()
        
        return jsonify({
            'success': True,
            'message': f'成功下载 {success_count}/{total_count} 张图片',
            'success_count': success_count,
            'total_count': total_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'})

@app.route('/api/refresh')
def api_refresh():
    """刷新数据"""
    product_manager.load_data()
    return jsonify({'success': True, 'message': '数据已刷新', 'total': len(product_manager.data)})

@app.route('/downloaded')
def downloaded_page():
    """已下载页面"""
    return render_template('downloaded.html')

@app.route('/erp/selected')
def erp_selected():
    """显示ERP系统中已选择的产品页面"""
    # 获取选中的产品ID
    selected_ids_param = request.args.get('selected_ids', '')
    if not selected_ids_param:
        return render_template('erp_selected.html', 
                               products=[],
                               total_products=0,
                               selected_count=0)
    
    # 解析选中的产品ID
    selected_ids = selected_ids_param.split(',')
    
    # 获取所有产品数据
    all_products = product_manager.data
    
    # 筛选出选中的产品
    selected_products = []
    for product in all_products:
        if product.get('product_id') in selected_ids:
            selected_products.append(product)
    
    return render_template('erp_selected.html', 
                           products=selected_products,
                           total_products=len(selected_products),
                           selected_count=len(selected_products))

@app.route('/api/downloaded')
def api_downloaded():
    """获取已下载的产品数据"""
    try:
        downloaded_products = product_manager.get_downloaded_products()
        return jsonify({
            'status': 'success',
            'data': downloaded_products,
            'total': len(downloaded_products)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/import-csv', methods=['POST'])
def import_csv():
    """导入CSV文件并处理"""
    try:
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'})
        
        # 确保CSV目录存在
        csv_dir = "images/csv"
        os.makedirs(csv_dir, exist_ok=True)
        
        # 保存上传的CSV文件
        file_path = os.path.join(csv_dir, csv_file.filename)
        csv_file.save(file_path)
        
        # 处理CSV文件
        processor = CSVProcessor()
        data = processor.read_csv_files()
        unique_data = processor.remove_duplicates(data)
        processor.save_to_imgdb(unique_data)
        
        # 重新加载产品数据
        product_manager.load_data()
        
        return jsonify({
            'success': True, 
            'message': f'成功导入 {len(unique_data)} 条产品数据',
            'count': len(unique_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'}), 500

@app.route('/api/convert_to_png', methods=['POST'])
def convert_to_png():
    """将选中的产品图片转换为PNG并上传到飞书"""
    try:
        data = request.json
        product_ids = data.get('product_ids', [])
        
        if not product_ids:
            return jsonify({'success': False, 'message': '请选择要转换的产品'})
        
        # 创建PNG输出目录
        png_dir = "images/png"
        os.makedirs(png_dir, exist_ok=True)
        
        # 初始化白底移除器和飞书客户端
        bg_remover = WhiteBackgroundRemover()
        from config import load_config
        from dataclasses import replace
        config = load_config()
        
        # 创建专门用于"产品PNG池"的飞书配置
        feishu_config = replace(config.feishu, sheet_name="产品PNG池")
        feishu_client = FeishuClient(feishu_config)
        
        # 获取选中的产品数据
        selected_products = []
        for product_id in product_ids:
            for item in product_manager.data:
                if str(item['product_id']) == str(product_id):
                    selected_products.append(item)
                    break
        
        # 处理每个产品图片
        success_count = 0
        failed_products = []
        processing_results = []  # 存储每个产品的详细处理结果
        
        for product in selected_products:
            product_name = product['product_name']
            product_id = product['product_id']
            
            # 初始化产品处理状态
            product_result = {
                'product_id': product_id,
                'product_name': product_name,
                'status': 'processing',
                'message': '正在处理...',
                'timestamp': datetime.now().isoformat()
            }
            processing_results.append(product_result)
            
            try:
                # 下载图片
                image_url = product['main_image_url']
                
                # 生成文件名
                filename = f"{product_id}_{product_manager._generate_filename(product_name)}"
                jpg_path = os.path.join("images/jpg", filename)
                png_path = os.path.join(png_dir, filename.replace('.jpg', '.png'))
                
                # 如果JPG不存在，先下载
                if not os.path.exists(jpg_path):
                    os.makedirs("images/jpg", exist_ok=True)
                    product_result['message'] = '正在下载原图...'
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    
                    with open(jpg_path, 'wb') as f:
                        f.write(response.content)
                
                # 使用WhiteBackgroundRemover处理图片
                product_result['message'] = '正在转换PNG格式...'
                success = bg_remover.process_single_image(jpg_path, png_path, enhance_edges=True)
                
                if not success:
                    product_result['status'] = 'failed'
                    product_result['message'] = 'PNG转换失败'
                    failed_products.append(f"{product_name} (ID: {product_id})")
                    continue
                
                # 异步上传到飞书
                product_result['message'] = '正在上传到飞书...'
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    print(f"[DEBUG] 开始处理产品: {product_name} (ID: {product_id})")
                    print(f"[DEBUG] 飞书配置 - App ID: {feishu_config.app_id[:10]}...")
                    print(f"[DEBUG] 飞书配置 - Sheet Name: {feishu_config.sheet_name}")
                    print(f"[DEBUG] 飞书配置 - Spreadsheet Token: {feishu_config.spreadsheet_token[:10]}...")
                    
                    # 获取access token
                    print(f"[DEBUG] 正在获取access token...")
                    access_token = loop.run_until_complete(feishu_client.get_access_token())
                    print(f"[DEBUG] Access token获取成功: {access_token[:20] if access_token else 'None'}...")
                    
                    # 获取工作表信息
                    print(f"[DEBUG] 正在获取工作表信息...")
                    sheet_info = loop.run_until_complete(feishu_client.get_sheet_info())
                    sheet_id = sheet_info.get("sheet_id")
                    print(f"[DEBUG] 工作表信息获取成功 - Sheet ID: {sheet_id}")
                    
                    # 获取现有数据行数，确定新行位置
                    print(f"[DEBUG] 正在获取现有数据行数...")
                    sheet_data = loop.run_until_complete(feishu_client.get_sheet_data())
                    next_row = len(sheet_data) + 2  # +2 因为第1行是表头，从第2行开始数据
                    print(f"[DEBUG] 现有数据行数: {len(sheet_data)}, 新行位置: {next_row}")
                    
                    # 获取列位置
                    print(f"[DEBUG] 正在获取列位置...")
                    product_image_col = loop.run_until_complete(feishu_client._get_column_letter_by_header("产品图"))
                    product_name_col = loop.run_until_complete(feishu_client._get_column_letter_by_header("产品名"))
                    print(f"[DEBUG] 列位置 - 产品图列: {product_image_col}, 产品名列: {product_name_col}")
                    
                    if product_image_col and product_name_col:
                        # 直接写入图片文件到产品图列
                        image_range = f"{sheet_id}!{product_image_col}{next_row}:{product_image_col}{next_row}"
                        print(f"[DEBUG] 正在写入图片到单元格: {image_range}")
                        image_success = loop.run_until_complete(feishu_client._write_image_file_to_cell(image_range, png_path))
                        print(f"[DEBUG] 图片写入结果: {image_success}")
                        
                        # 写入产品名到产品名列
                        name_range = f"{sheet_id}!{product_name_col}{next_row}:{product_name_col}{next_row}"
                        print(f"[DEBUG] 正在写入产品名到单元格: {name_range}, 值: {product_name}")
                        name_success = loop.run_until_complete(feishu_client.update_cell_value(name_range, product_name))
                        print(f"[DEBUG] 产品名写入结果: {name_success}")
                        
                        if image_success and name_success:
                            success_count += 1
                            product_result['status'] = 'success'
                            product_result['message'] = '处理完成'
                            print(f"[DEBUG] 产品 {product_name} 处理成功")
                        else:
                            product_result['status'] = 'failed'
                            product_result['message'] = '飞书写入失败'
                            failed_products.append(f"{product_name} (飞书写入失败)")
                            print(f"[DEBUG] 产品 {product_name} 飞书写入失败")
                    else:
                        product_result['status'] = 'failed'
                        product_result['message'] = '找不到目标列'
                        failed_products.append(f"{product_name} (找不到目标列)")
                        print(f"[DEBUG] 产品 {product_name} 找不到目标列")
                        
                finally:
                    loop.close()
                
            except Exception as e:
                product_result['status'] = 'failed'
                product_result['message'] = f'处理错误: {str(e)}'
                failed_products.append(f"{product.get('product_name', 'Unknown')} (错误: {str(e)})")
                continue
        
        # 构建返回消息
        message = f'成功处理 {success_count}/{len(selected_products)} 个产品图片'
        if failed_products:
            message += f'\n失败的产品: {"、".join(failed_products)}'
        
        return jsonify({
            'success': success_count > 0,
            'message': message,
            'success_count': success_count,
            'total_count': len(selected_products),
            'failed_products': failed_products,
            'processing_results': processing_results  # 添加详细的处理结果
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'转换失败: {str(e)}'}), 500


# ===== 工作流管理相关路由 =====

@app.route('/workflow')
@app.route('/workflow/list')
def workflow_list():
    """工作流列表页面"""
    return render_template('workflow_list.html')

@app.route('/workflow/create')
def workflow_create():
    """新建工作流页面"""
    return render_template('workflow_create.html')

@app.route('/workflow/edit/<workflow_id>')
def workflow_edit(workflow_id):
    """编辑工作流页面"""
    return render_template('workflow_edit.html', workflow_id=workflow_id)

@app.route('/workflow/execute/<workflow_id>')
def workflow_execute(workflow_id):
    """工作流执行页面"""
    return render_template('workflow_execute.html', workflow_id=workflow_id)

@app.route('/api/workflows', methods=['GET'])
def api_get_workflows():
    """获取工作流列表API"""
    try:
        workflows = workflow_manager.list_workflows()
        return jsonify({
            'success': True,
            'data': workflows
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取工作流列表失败: {str(e)}'
        }), 500

@app.route('/api/workflows', methods=['POST'])
def api_create_workflow():
    """创建工作流API"""
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        workflow_name = data.get('workflow_name')
        description = data.get('description', '')
        
        if not workflow_id or not workflow_name:
            return jsonify({
                'success': False,
                'message': '工作流ID和名称不能为空'
            }), 400
        
        # 创建工作流
        created_id = workflow_manager.create_workflow(workflow_id, description)
        
        return jsonify({
            'success': True,
            'data': {'workflow_id': created_id},
            'message': '工作流创建成功'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建工作流失败: {str(e)}'
        }), 500

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def api_get_workflow(workflow_id):
    """获取单个工作流详情API"""
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            return jsonify({
                'success': False,
                'message': '工作流不存在'
            }), 404
        
        nodes = workflow_manager.get_workflow_nodes(workflow_id)
        workflow['nodes'] = nodes
        
        return jsonify({
            'success': True,
            'data': workflow
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取工作流详情失败: {str(e)}'
        }), 500

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
def api_update_workflow(workflow_id):
    """更新工作流API"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        nodes = data.get('nodes', [])
        
        if not name:
            return jsonify({
                'success': False,
                'message': '工作流名称不能为空'
            }), 400
        
        # 更新工作流基本信息
        success = workflow_manager.update_workflow(workflow_id, name, description)
        if not success:
            return jsonify({
                'success': False,
                'message': '更新工作流失败'
            }), 400
        
        # 清空现有节点
        workflow_manager.clear_workflow_nodes(workflow_id)
        
        # 添加新节点
        for node in nodes:
            node_id = node.get('node_id')
            node_name = node.get('name')
            node_type = node.get('type')
            node_description = node.get('description', '')
            
            if node_id and node_name and node_type:
                try:
                    workflow_manager.add_node_with_id(
                        workflow_id=workflow_id,
                        node_id=node_id,
                        name=node_name,
                        node_type=node_type,
                        description=node_description
                    )
                except Exception as e:
                    print(f"添加节点失败: {e}")
        
        return jsonify({
            'success': True,
            'message': '工作流更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新工作流失败: {str(e)}'
        }), 500

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def api_delete_workflow(workflow_id):
    """删除工作流API"""
    try:
        success = workflow_manager.delete_workflow(workflow_id)
        if success:
            return jsonify({
                'success': True,
                'message': '工作流删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '工作流删除失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除工作流失败: {str(e)}'
        }), 500

@app.route('/api/workflows/<workflow_id>/nodes', methods=['POST'])
def api_add_node(workflow_id):
    """添加节点API"""
    try:
        data = request.get_json()
        node_name = data.get('node_name')
        node_id = data.get('node_id')
        node_type = data.get('node_type')
        
        if not all([node_name, node_id, node_type]):
            return jsonify({
                'success': False,
                'message': '节点名称、ID和类型不能为空'
            }), 400
        
        # 验证节点类型
        try:
            node_type_enum = NodeType(node_type)
        except ValueError:
            return jsonify({
                'success': False,
                'message': f'无效的节点类型: {node_type}'
            }), 400
        
        success = workflow_manager.add_node_with_id(workflow_id, node_id, node_name, node_type)
        if success:
            return jsonify({
                'success': True,
                'message': '节点添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '节点添加失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加节点失败: {str(e)}'
        }), 500

@app.route('/api/workflows/<workflow_id>/nodes/<node_id>', methods=['DELETE'])
def api_delete_node(workflow_id, node_id):
    """删除节点API"""
    try:
        success = workflow_manager.remove_node(workflow_id, node_id)
        if success:
            return jsonify({
                'success': True,
                'message': '节点删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '节点删除失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除节点失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)