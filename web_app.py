from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import requests
from datetime import datetime
import re
import threading
import time

app = Flask(__name__)

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

@app.route('/')
def index():
    """主页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    data = product_manager.get_paginated_data(page, per_page)
    return render_template('index.html', **data)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)