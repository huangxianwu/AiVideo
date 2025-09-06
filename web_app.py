from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, Response
from werkzeug.utils import secure_filename
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
import aiohttp
from csv_processor import CSVProcessor
from png_processor import WhiteBackgroundRemover
from feishu_client import FeishuClient
from config import FeishuConfig
from data.workflow_manager import WorkflowManager, NodeType
from data.database_manager import DatabaseManager
import subprocess
import uuid
import queue
from queue import Queue
import mimetypes


app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量用于管理工作流任务
running_tasks = {}
task_logs = {}

# 全局日志队列，用于实时日志推送
log_queues = {}
log_lock = threading.Lock()

# 日志推送函数
def push_log(session_id, message, log_type='info'):
    """推送日志到指定会话"""
    with log_lock:
        if session_id in log_queues:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'message': message,
                'type': log_type
            }
            try:
                log_queues[session_id].put_nowait(log_entry)
            except:
                pass  # 队列满时忽略

@app.route('/api/logs/<session_id>')
def stream_logs(session_id):
    """Server-Sent Events端点，用于实时推送日志"""
    def generate():
        # 为当前会话创建日志队列
        with log_lock:
            if session_id not in log_queues:
                log_queues[session_id] = queue.Queue(maxsize=100)
        
        log_queue = log_queues[session_id]
        
        try:
            while True:
                try:
                    # 等待日志消息
                    log_entry = log_queue.get(timeout=30)
                    yield f"data: {json.dumps(log_entry)}\n\n"
                except queue.Empty:
                    # 发送心跳
                    yield f"data: {{\"type\": \"heartbeat\"}}\n\n"
                except:
                    break
        finally:
            # 清理队列
            with log_lock:
                if session_id in log_queues:
                    del log_queues[session_id]
    
    return Response(generate(), mimetype='text/event-stream')

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
database_manager = DatabaseManager()

@app.route('/')
def index():
    """主页 - 重定向到ERP页面"""
    from flask import redirect, url_for
    return redirect(url_for('erp_index'))

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
        name = data.get('name') or data.get('workflow_name')  # 兼容两种参数名
        description = data.get('description', '')
        nodes = data.get('nodes', [])
        
        if not workflow_id or not name:
            return jsonify({
                'success': False,
                'message': '工作流ID和名称不能为空'
            }), 400
        
        # 创建工作流
        created_id = workflow_manager.create_workflow_with_name(workflow_id, name, description)
        
        # 添加节点
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


# POD工作流相关路由
@app.route('/pod-workflow')
def pod_workflow():
    """POD工作流页面"""
    return render_template('pod_workflow.html')

@app.route('/api/workflow/execute', methods=['POST'])
def api_execute_workflow():
    """执行POD工作流"""
    try:
        data = request.get_json()
        workflow_type = data.get('workflow_type')
        
        if not workflow_type:
            return jsonify({'success': False, 'error': '缺少工作流类型参数'})
        
        # 映射工作流类型到main.py的参数
        workflow_mapping = {
            'image_composition': '图片合成工作流',
            'image_to_video': '图生视频工作流', 
            'full_workflow': '完整工作流'
        }
        
        if workflow_type not in workflow_mapping:
            return jsonify({'success': False, 'error': '不支持的工作流类型'})
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务日志
        task_logs[task_id] = Queue()
        
        # 构建命令 - 使用workflow_runner.py来避免交互式输入
        cmd = ['python3', 'workflow_runner.py', '--workflow', workflow_type]
        
        # 启动子进程
        def run_workflow():
            try:
                # 添加开始日志
                timestamp = datetime.now().strftime('%H:%M:%S')
                start_message = f"[{timestamp}] 🚀 开始执行{workflow_mapping[workflow_type]}"
                task_logs[task_id].put({'type': 'log', 'message': start_message})
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    cwd=os.getcwd()  # 确保在正确的工作目录中执行
                )
                
                running_tasks[task_id] = process
                
                # 实时读取输出
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # 保持原始日志格式，不添加额外的时间戳
                        log_message = line.strip()
                        if log_message:  # 只记录非空行
                            task_logs[task_id].put({'type': 'log', 'message': log_message})
                
                # 等待进程结束
                process.wait()
                
                # 发送完成信号
                timestamp = datetime.now().strftime('%H:%M:%S')
                if process.returncode == 0:
                    complete_message = f"[{timestamp}] ✅ 工作流执行成功"
                    task_logs[task_id].put({'type': 'log', 'message': complete_message})
                    task_logs[task_id].put({'type': 'complete', 'message': '工作流执行完成'})
                else:
                    error_message = f"[{timestamp}] ❌ 工作流执行失败，退出码: {process.returncode}"
                    task_logs[task_id].put({'type': 'log', 'message': error_message})
                    task_logs[task_id].put({'type': 'error', 'message': f'工作流执行失败，退出码: {process.returncode}'})
                
                # 清理任务
                if task_id in running_tasks:
                    del running_tasks[task_id]
                    
            except Exception as e:
                timestamp = datetime.now().strftime('%H:%M:%S')
                error_message = f"[{timestamp}] ❌ 执行异常: {str(e)}"
                task_logs[task_id].put({'type': 'log', 'message': error_message})
                task_logs[task_id].put({'type': 'error', 'message': f'执行异常: {str(e)}'})
                if task_id in running_tasks:
                    del running_tasks[task_id]
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'task_id': task_id,
            'message': f'工作流 {workflow_mapping[workflow_type]} 已启动'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/workflow/logs/<task_id>')
def api_workflow_logs(task_id):
    """获取工作流实时日志 (Server-Sent Events)"""
    def generate_logs():
        if task_id not in task_logs:
            yield f"data: {json.dumps({'type': 'error', 'message': '任务不存在'})}\n\n"
            return
        
        log_queue = task_logs[task_id]
        
        while True:
            try:
                # 等待日志消息，超时时间为1秒
                if not log_queue.empty():
                    log_data = log_queue.get_nowait()
                    yield f"data: {json.dumps(log_data)}\n\n"
                    
                    # 如果是完成或错误消息，结束流
                    if log_data['type'] in ['complete', 'error']:
                        # 清理日志队列
                        if task_id in task_logs:
                            del task_logs[task_id]
                        break
                else:
                    # 发送心跳
                    time.sleep(0.5)
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'日志流异常: {str(e)}'})}\n\n"
                break
    
    return Response(
        generate_logs(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/api/workflow/stop/<task_id>', methods=['POST'])
def api_stop_workflow(task_id):
    """停止运行中的工作流"""
    try:
        if task_id in running_tasks:
            process = running_tasks[task_id]
            process.terminate()
            del running_tasks[task_id]
            
            # 发送停止消息
            if task_id in task_logs:
                task_logs[task_id].put({'type': 'error', 'message': '工作流已被用户停止'})
            
            return jsonify({'success': True, 'message': '工作流已停止'})
        else:
            return jsonify({'success': False, 'error': '任务不存在或已结束'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 历史记录相关路由
@app.route('/history')
def history_page():
    """历史记录页面"""
    return render_template('history.html')

@app.route('/api/files/search')
def api_search_files():
    """搜索文件API"""
    try:
        # 获取查询参数
        query = request.args.get('query', '')
        file_type = request.args.get('file_type', '')
        workflow_type = request.args.get('workflow_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort_by = request.args.get('sort_by', 'created_at_desc')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 构建搜索条件（只传递DatabaseManager支持的参数）
        search_params = {
            'query': query,
            'file_type': file_type,
            'workflow_type': workflow_type,
            'date_from': date_from,
            'date_to': date_to,
            'limit': page_size
        }
        
        # 调用数据库管理器的搜索方法
        results = database_manager.search_files(**search_params)
        
        return jsonify({
            'success': True,
            'files': results['files'],
            'total': results['total'],
            'page': page,
            'page_size': page_size,
            'total_pages': (results['total'] - 1) // page_size + 1 if results['total'] > 0 else 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'files': [],
            'total': 0
        })

@app.route('/api/files/serve/<path:file_path>')
def api_serve_file(file_path):
    """文件服务API"""
    try:
        # 解码文件路径
        import urllib.parse
        file_path = urllib.parse.unquote(file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件是否在允许的目录中（安全检查）
        allowed_dirs = ['output', 'images']
        is_allowed = False
        for allowed_dir in allowed_dirs:
            if os.path.abspath(file_path).startswith(os.path.abspath(allowed_dir)):
                is_allowed = True
                break
        
        if not is_allowed:
            return jsonify({'error': '访问被拒绝'}), 403
        
        # 获取文件的MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        return send_file(file_path, mimetype=mime_type)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/statistics')
def api_file_statistics():
    """获取文件统计信息API"""
    try:
        stats = database_manager.get_file_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/files/recent')
def api_recent_files():
    """获取最近文件API"""
    try:
        limit = int(request.args.get('limit', 10))
        files = database_manager.get_recent_files(limit)
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'files': []
        })

@app.route('/api/files/by-date')
def api_files_by_date():
    """按日期获取文件API"""
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({
                'success': False,
                'error': '缺少日期参数'
            })
        
        files = database_manager.get_files_by_date(date)
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'files': []
        })

@app.route('/api/workflow/files/<task_id>')
def api_workflow_files(task_id):
    """获取指定工作流任务的生成文件"""
    try:
        # 从数据库管理器获取任务相关文件
        files = database_manager.search_files(task_id=task_id)
        
        return jsonify({
            'success': True,
            'files': files['files']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'files': []
        })

# ===== RunningHub API相关路由 =====

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    """文件上传到RunningHub服务器API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['file']
        node_id = request.form.get('nodeId', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        # 检查文件大小限制 (30MB)
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头
        
        if file_size > 30 * 1024 * 1024:  # 30MB
            return jsonify({'success': False, 'error': '文件大小超过30MB限制'}), 400
        
        # 检查文件类型
        allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv'],
            'audio': ['.mp3', '.wav', '.flac'],
            'zip': ['.zip']
        }
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        is_valid_file = False
        for file_type, extensions in allowed_extensions.items():
            if file_ext in extensions:
                is_valid_file = True
                break
        
        if not is_valid_file:
            return jsonify({'success': False, 'error': f'不支持的文件格式: {file_ext}'}), 400
        
        # 上传到RunningHub服务器
        runninghub_url = "https://www.runninghub.cn/task/openapi/upload"
        api_key = os.getenv("COMFYUI_API_KEY")
        
        print(f"[DEBUG] 开始上传文件: {file.filename}")
        print(f"[DEBUG] 文件大小: {file_size / 1024 / 1024:.1f}MB")
        print(f"[DEBUG] API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
        
        # 准备上传数据和头部
        files = {'file': (file.filename, file.stream, file.content_type)}
        data = {'apiKey': api_key}  # 添加apiKey作为表单字段
        headers = {
            'Host': 'www.runninghub.cn',
            'Authorization': f'Bearer {api_key}'
        }
        
        # 发送请求到RunningHub
        print(f"[DEBUG] 发送请求到: {runninghub_url}")
        try:
            response = requests.post(runninghub_url, files=files, data=data, headers=headers, timeout=60)
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            print(f"[DEBUG] 响应内容: {response.text[:500]}...")
        except requests.exceptions.Timeout as e:
            print(f"[DEBUG] 请求超时: {str(e)}")
            return jsonify({'success': False, 'error': f'请求超时: {str(e)}'}), 500
        except requests.exceptions.ConnectionError as e:
            print(f"[DEBUG] 连接错误: {str(e)}")
            return jsonify({'success': False, 'error': f'连接错误: {str(e)}'}), 500
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] 请求异常: {str(e)}")
            return jsonify({'success': False, 'error': f'请求异常: {str(e)}'}), 500
        
        if response.status_code != 200:
            return jsonify({
                'success': False, 
                'error': f'RunningHub上传失败: HTTP {response.status_code}'
            }), 500
        
        result = response.json()
        
        if result.get('code') != 0:
            return jsonify({
                'success': False,
                'error': f'RunningHub上传失败: {result.get("msg", "未知错误")}'
            }), 500
        
        # 返回RunningHub的fileName
        return jsonify({
            'success': True,
            'filename': result['data']['fileName'],
            'fileType': result['data']['fileType']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/runninghub/create-task', methods=['POST'])
def api_create_runninghub_task():
    """创建RunningHub任务"""
    try:
        data = request.get_json()
        workflow_id = data.get('workflowId')
        node_info_list = data.get('nodeInfoList', [])
        session_id = data.get('sessionId', str(uuid.uuid4()))
        
        print("[LOG] 开始创建RunningHub任务")
        push_log(session_id, "开始创建RunningHub任务", "info")
        
        print(f"[LOG] 工作流ID: {workflow_id}")
        print(f"[LOG] 节点信息列表: {node_info_list}")
        push_log(session_id, f"工作流ID: {workflow_id}", "info")
        push_log(session_id, f"收到 {len(node_info_list)} 个节点的信息", "info")
        
        # 使用ComfyUI客户端创建任务
        from comfyui_client import ComfyUIClient
        from config import load_config
        
        print("[LOG] 加载配置文件")
        push_log(session_id, "正在加载配置文件", "info")
        config = load_config()
        client = ComfyUIClient(config.comfyui)
        
        # 构建API调用参数
        api_payload = {
            "apiKey": config.comfyui.api_key,
            "workflowId": workflow_id,
            "nodeInfoList": node_info_list
        }
        
        print(f"[LOG] API调用参数: {api_payload}")
        print(f"[LOG] RunningHub基础URL: {config.comfyui.base_url}")
        push_log(session_id, f"准备调用RunningHub API: {config.comfyui.base_url}", "info")
        
        # 调用RunningHub API
        import aiohttp
        import asyncio
        
        async def create_task():
              url = f"{config.comfyui.base_url}/task/openapi/create"
              headers = {
                  "Host": "www.runninghub.cn",
                  "Content-Type": "application/json"
              }
              
              print(f"[LOG] 请求URL: {url}")
              print(f"[LOG] 请求头: {headers}")
              push_log(session_id, f"正在连接到: {url}", "info")
              
              # 创建SSL上下文，跳过证书验证
              import ssl
              ssl_context = ssl.create_default_context()
              ssl_context.check_hostname = False
              ssl_context.verify_mode = ssl.CERT_NONE
              
              connector = aiohttp.TCPConnector(ssl=ssl_context)
              async with aiohttp.ClientSession(connector=connector) as session:
                  print("[LOG] 发送HTTP请求到RunningHub")
                  push_log(session_id, "正在发送HTTP请求到RunningHub", "info")
                  async with session.post(url, headers=headers, json=api_payload) as response:
                     print(f"[LOG] HTTP响应状态: {response.status}")
                     response_text = await response.text()
                     print(f"[LOG] HTTP响应内容: {response_text}")
                     push_log(session_id, f"收到HTTP响应，状态码: {response.status}", "info")
                     
                     if response.status == 200:
                         result = await response.json()
                         print(f"[LOG] 解析后的响应: {result}")
                         if result.get('code') == 0:
                             data = result.get('data', {})
                             task_id = data.get('taskId') or data.get('task_id')
                             print(f"[LOG] 任务创建成功，任务ID: {task_id}")
                             return {'success': True, 'taskId': task_id}
                         else:
                             error_msg = result.get('message', '创建任务失败')
                             print(f"[LOG] 任务创建失败: {error_msg}")
                             return {'success': False, 'error': error_msg}
                     else:
                         error_msg = f'HTTP错误: {response.status}'
                         print(f"[LOG] HTTP请求失败: {error_msg}")
                         return {'success': False, 'error': error_msg}
        
        # 运行异步任务
        print("[LOG] 开始执行异步任务")
        result = asyncio.run(create_task())
        
        print(f"[LOG] 任务执行结果: {result}")
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"[LOG] 创建任务异常: {str(e)}")
        print(f"[LOG] 异常类型: {type(e).__name__}")
        import traceback
        print(f"[LOG] 异常堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/runninghub/check-status', methods=['POST'])
def api_check_runninghub_status():
    """检查RunningHub任务状态"""
    try:
        data = request.get_json()
        task_id = data.get('taskId')
        
        if not task_id:
            return jsonify({'success': False, 'error': '缺少任务ID'}), 400
        
        # 使用ComfyUI客户端检查状态
        from config import load_config
        import aiohttp
        import asyncio
        
        config = load_config()
        
        async def check_status():
             url = f"{config.comfyui.base_url}/task/openapi/status"
             headers = {
                 "Host": "www.runninghub.cn",
                 "Content-Type": "application/json"
             }
             
             payload = {
                 "apiKey": config.comfyui.api_key,
                 "taskId": task_id
             }
             
             # 创建SSL上下文，跳过证书验证
             import ssl
             ssl_context = ssl.create_default_context()
             ssl_context.check_hostname = False
             ssl_context.verify_mode = ssl.CERT_NONE
             
             connector = aiohttp.TCPConnector(ssl=ssl_context)
             async with aiohttp.ClientSession(connector=connector) as session:
                 async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            data = result.get('data')
                            status = data if isinstance(data, str) else data.get('status') if isinstance(data, dict) else 'UNKNOWN'
                            return {'success': True, 'status': status, 'message': f'任务状态: {status}'}
                        else:
                            return {'success': False, 'error': result.get('message', '查询状态失败')}
                    else:
                        return {'success': False, 'error': f'HTTP错误: {response.status}'}
        
        result = asyncio.run(check_status())
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/runninghub/get-results', methods=['POST'])
def api_get_runninghub_results():
    """获取RunningHub任务结果"""
    try:
        data = request.get_json()
        task_id = data.get('taskId')
        
        if not task_id:
            return jsonify({'success': False, 'error': '缺少任务ID'}), 400
        
        from config import load_config
        import aiohttp
        import asyncio
        import os
        from datetime import datetime
        
        config = load_config()
        
        async def get_results():
             url = f"{config.comfyui.base_url}/task/openapi/outputs"
             headers = {
                 "Host": "www.runninghub.cn",
                 "Content-Type": "application/json"
             }
             
             payload = {
                 "apiKey": config.comfyui.api_key,
                 "taskId": task_id
             }
             
             # 创建SSL上下文，跳过证书验证
             import ssl
             ssl_context = ssl.create_default_context()
             ssl_context.check_hostname = False
             ssl_context.verify_mode = ssl.CERT_NONE
             
             connector = aiohttp.TCPConnector(ssl=ssl_context)
             async with aiohttp.ClientSession(connector=connector) as session:
                 async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            data = result.get('data', {})
                            
                            # 创建输出目录
                            today = datetime.now().strftime('%m%d')
                            output_dir = os.path.join('output', today)
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # 处理输出文件
                            files = []
                            downloaded_files = []
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if isinstance(value, list):
                                        for item in value:
                                            if isinstance(item, dict) and 'url' in item:
                                                file_info = {
                                                    'name': item.get('filename', f'{key}_{len(files)}.png'),
                                                    'url': item['url']
                                                }
                                                files.append(file_info)
                                                
                                                # 下载文件到本地
                                                try:
                                                    file_url = item['url']
                                                    filename = file_info['name']
                                                    local_path = os.path.join(output_dir, filename)
                                                    
                                                    async with session.get(file_url) as file_response:
                                                        if file_response.status == 200:
                                                            with open(local_path, 'wb') as f:
                                                                f.write(await file_response.read())
                                                            downloaded_files.append({
                                                                'name': filename,
                                                                'path': local_path,
                                                                'url': file_url
                                                            })
                                                            print(f"[DEBUG] 文件已保存到: {local_path}")
                                                        else:
                                                            print(f"[DEBUG] 下载文件失败: {file_url}, 状态码: {file_response.status}")
                                                except Exception as download_error:
                                                    print(f"[DEBUG] 下载文件异常: {str(download_error)}")
                            
                            return {
                                'success': True, 
                                'outputPath': output_dir,
                                'files': files,
                                'downloadedFiles': downloaded_files,
                                'data': data
                            }
                        else:
                            return {'success': False, 'error': result.get('message', '获取结果失败')}
                    else:
                        return {'success': False, 'error': f'HTTP错误: {response.status}'}
        
        result = asyncio.run(get_results())
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)