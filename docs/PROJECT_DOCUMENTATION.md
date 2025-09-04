# 飞书表格数据处理与ERP系统 - 完整项目文档

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 功能特性](#2-功能特性)
- [3. 系统架构](#3-系统架构)
- [4. 安装与配置](#4-安装与配置)
- [5. 用户指南](#5-用户指南)
- [6. API文档](#6-api文档)
- [7. 开发指南](#7-开发指南)
- [8. 部署与运维](#8-部署与运维)
- [9. 故障排查](#9-故障排查)
- [10. 更新日志](#10-更新日志)

---

## 1. 项目概述

### 1.1 项目简介

本项目是一个集成的数据处理与ERP管理系统，主要功能包括：
- 飞书表格数据自动化处理
- ComfyUI AI工作流执行
- 图像处理与白底去除
- Web界面产品管理
- ERP系统功能模块

### 1.2 技术栈

- **后端**: Python 3.8+, Flask
- **前端**: HTML5, CSS3, JavaScript, Bootstrap
- **数据处理**: Pandas, OpenCV
- **API集成**: 飞书开放平台API, ComfyUI API
- **图像处理**: PIL, OpenCV, 自定义白底去除算法

### 1.3 系统要求

- Python 3.8 或更高版本
- 网络连接（访问飞书API和ComfyUI服务）
- 至少 2GB 可用磁盘空间
- 推荐 4GB+ 内存

---

## 2. 功能特性

### 2.1 核心功能模块

#### 🔐 飞书集成
- 自动获取访问令牌
- 表格数据读取与写入
- 图片上传到飞书云空间
- 单元格状态更新

#### 🖼️ 图像处理
- 自动下载网络图片
- 白底去除算法
- PNG格式转换
- 批量图像处理

#### 🤖 AI工作流
- ComfyUI工作流执行
- 任务状态监控
- 异步处理支持
- 失败重试机制

#### 🌐 Web界面
- 产品数据管理
- 分页浏览与搜索
- 批量操作支持
- 实时状态更新

#### 📊 ERP系统
- 产品选择与管理
- CSV数据导入
- 已选商品管理
- PNG转换状态控制

### 2.2 Web应用路由

| 路由 | 方法 | 功能描述 |
|------|------|----------|
| `/` | GET | 主页 - 产品数据浏览 |
| `/erp` | GET | ERP系统主页 |
| `/erp/selected` | GET | 已选商品管理页面 |
| `/downloaded` | GET | 已下载商品页面 |
| `/api/data` | GET | 获取分页产品数据 |
| `/api/download` | POST | 批量下载图片 |
| `/api/downloaded` | GET | 获取已下载商品数据 |
| `/api/refresh` | GET | 刷新产品数据 |
| `/import-csv` | POST | 导入CSV数据 |
| `/api/convert_to_png` | POST | PNG转换与飞书上传 |

---

## 3. 系统架构

### 3.1 项目结构

```
toolKit/
├── 📁 配置文件
│   ├── .env                     # 环境变量配置
│   ├── .env.example             # 配置模板
│   ├── config.py                # 配置管理模块
│   └── requirements.txt         # 依赖包列表
├── 📁 核心模块
│   ├── main.py                  # 主程序入口
│   ├── web_app.py               # Web应用主程序
│   ├── feishu_client.py         # 飞书API客户端
│   ├── comfyui_client.py        # ComfyUI API客户端
│   ├── workflow_processor.py    # 工作流处理器
│   ├── csv_processor.py         # CSV数据处理
│   └── png_processor.py         # PNG图像处理
├── 📁 Web界面
│   ├── templates/               # HTML模板
│   │   ├── index.html          # 主页模板
│   │   ├── erp_index.html      # ERP主页
│   │   ├── erp_selected.html   # 已选商品页面
│   │   └── ...                 # 其他模板
│   └── static/                  # 静态资源
├── 📁 数据目录
│   ├── images/                  # 图片存储
│   │   ├── jpg/                # 原始图片
│   │   ├── png/                # 处理后图片
│   │   └── csvdb/              # CSV数据库
│   ├── output/                  # 生成图片输出
│   ├── temp/                    # 临时文件
│   ├── logs/                    # 日志文件
│   └── reports/                 # 处理报告
└── 📁 文档
    └── docs/                    # 项目文档
```

### 3.2 核心类设计

#### ProductManager 类
```python
class ProductManager:
    def __init__(self):
        self.imgdb_file = "images/csvdb/imgdb.csv"
        self.download_dir = "images/jpg"
        self.data = []
    
    def load_data(self)                    # 加载产品数据
    def get_paginated_data(self, page, per_page)  # 获取分页数据
    def download_images(self, selected_ids)       # 批量下载图片
    def update_download_status(self, product_ids) # 更新下载状态
    def get_downloaded_products(self)             # 获取已下载商品
```

#### FeishuClient 类
```python
class FeishuClient:
    def get_tenant_access_token(self)             # 获取访问令牌
    def read_spreadsheet_data(self, token, range) # 读取表格数据
    def upload_image_to_feishu(self, image_path)  # 上传图片
    def write_image_to_cell(self, token, range, image_token) # 写入图片到单元格
    def update_cell_status(self, token, range, status)       # 更新状态
```

#### WhiteBackgroundRemover 类
```python
class WhiteBackgroundRemover:
    def remove_white_background(self, input_path, output_path) # 去除白底
    def process_image(self, image)                            # 图像处理
    def save_as_png(self, image, output_path)                # 保存PNG格式
```

---

## 4. 安装与配置

### 4.1 环境准备

#### 克隆项目
```bash
git clone <repository_url>
cd toolKit
```

#### 创建虚拟环境
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

### 4.2 配置文件设置

#### 复制配置模板
```bash
cp .env.example .env
```

#### 编辑环境变量
```env
# 飞书应用配置
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxx
FEISHU_SPREADSHEET_TOKEN=xxxxxxxxxx
FEISHU_SHEET_NAME=Sheet1
FEISHU_RANGE=A1:Z1000

# ComfyUI配置
COMFYUI_API_KEY=your_api_key
COMFYUI_WORKFLOW_ID=your_workflow_id
COMFYUI_BASE_URL=http://localhost:8188

# 列映射配置
FEISHU_PRODUCT_IMAGE_COLUMN=A
FEISHU_MODEL_IMAGE_COLUMN=B
FEISHU_PROMPT_COLUMN=C
FEISHU_STATUS_COLUMN=D
FEISHU_OUTPUT_COLUMN=E
```

### 4.3 飞书应用配置

#### 创建飞书应用
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 配置应用权限：
   - `sheets:spreadsheet:readonly` - 查看电子表格
   - `sheets:spreadsheet:write` - 编辑电子表格
   - `drive:drive:readonly` - 查看云空间文件
   - `drive:drive:write` - 编辑云空间文件

#### 获取表格Token
1. 打开目标飞书表格
2. 从URL中提取spreadsheet_token
   ```
   https://example.feishu.cn/sheets/shtcnxxxxxxxxxxxxxxx
   ```
   其中 `shtcnxxxxxxxxxxxxxxx` 就是spreadsheet_token

### 4.4 ComfyUI配置

#### 安装ComfyUI
```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

#### 启动ComfyUI服务
```bash
python main.py --listen 0.0.0.0 --port 8188
```

#### 配置工作流
1. 在ComfyUI界面中创建工作流
2. 导出为JSON格式
3. 保存为 `My workflow python.json`

---

## 5. 用户指南

### 5.1 启动应用

#### 启动Web应用
```bash
python web_app.py
```

访问地址：`http://localhost:8080`

#### 启动命令行工具
```bash
python main.py
```

### 5.2 Web界面使用

#### 主页功能
- **产品浏览**: 分页查看所有产品数据
- **搜索过滤**: 根据产品名称或ID搜索
- **批量选择**: 支持单选和多选操作
- **数据刷新**: 重新加载最新数据

#### ERP系统使用

**进入ERP系统**
1. 访问 `/erp` 路径
2. 查看产品选择界面

**导入CSV数据**
1. 点击"导入CSV"按钮
2. 选择CSV文件
3. 系统自动解析并导入数据

**管理已选商品**
1. 在产品列表中选择商品
2. 点击"已选择"统计卡片
3. 进入已选商品管理页面

**PNG转换功能**
1. 在已选商品页面
2. 点击"转换选择的商品为PNG"按钮
3. 查看实时处理状态
4. 等待处理完成

### 5.3 状态控制面板

#### 功能特性
- **实时进度**: 显示整体处理进度
- **详细状态**: 每个商品的处理状态
- **错误信息**: 失败商品的错误详情
- **可折叠界面**: 节省屏幕空间

#### 状态说明
- `等待处理...`: 商品已加入队列，等待开始处理
- `正在下载图片...`: 正在从网络下载商品图片
- `正在转换PNG...`: 正在进行白底去除和PNG转换
- `正在上传到飞书...`: 正在将处理后的图片上传到飞书
- `处理完成`: 商品处理成功完成
- `处理失败`: 商品处理过程中出现错误

---

## 6. API文档

### 6.1 Web API接口

#### 获取产品数据
```http
GET /api/data?page=1&per_page=50
```

**响应格式:**
```json
{
  "data": [
    {
      "product_id": "123456789",
      "product_name": "商品名称",
      "image_url": "https://example.com/image.jpg",
      "downloaded": false
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "total_pages": 20
  }
}
```

#### 批量下载图片
```http
POST /api/download
Content-Type: application/json

{
  "selected_ids": ["123456789", "987654321"]
}
```

**响应格式:**
```json
{
  "success": true,
  "message": "下载完成",
  "downloaded_count": 2,
  "failed_count": 0
}
```

#### PNG转换接口
```http
POST /api/convert_to_png
Content-Type: application/json

{
  "selected_ids": ["123456789", "987654321"]
}
```

**响应格式:**
```json
{
  "success": true,
  "message": "PNG转换完成",
  "success_count": 2,
  "total_count": 2,
  "failed_products": [],
  "processing_results": [
    {
      "product_id": "123456789",
      "product_name": "商品名称",
      "status": "success",
      "message": "处理完成",
      "timestamp": "2024-01-01 12:00:00"
    }
  ]
}
```

### 6.2 飞书API集成

#### 获取访问令牌
```python
def get_tenant_access_token(self):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": self.app_id,
        "app_secret": self.app_secret
    }
    response = requests.post(url, json=payload)
    return response.json().get('tenant_access_token')
```

#### 读取表格数据
```python
def read_spreadsheet_data(self, spreadsheet_token, range_str):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}"
    headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.json()
```

### 6.3 ComfyUI API集成

#### 上传图片
```python
def upload_image(self, image_path):
    url = f"{self.base_url}/upload/image"
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(url, files=files)
    return response.json()
```

#### 执行工作流
```python
def execute_workflow(self, workflow_data):
    url = f"{self.base_url}/prompt"
    response = requests.post(url, json={"prompt": workflow_data})
    return response.json()
```

---

## 7. 开发指南

### 7.1 代码规范

#### Python代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 添加详细的文档字符串
- 异常处理要具体明确

#### 示例代码
```python
from typing import List, Optional, Dict, Any

def process_products(product_ids: List[str]) -> Dict[str, Any]:
    """
    处理产品列表
    
    Args:
        product_ids: 产品ID列表
        
    Returns:
        处理结果字典，包含成功和失败的统计信息
        
    Raises:
        ValueError: 当产品ID列表为空时
        ProcessingError: 当处理过程中出现错误时
    """
    if not product_ids:
        raise ValueError("产品ID列表不能为空")
    
    results = {
        "success_count": 0,
        "failed_count": 0,
        "errors": []
    }
    
    for product_id in product_ids:
        try:
            # 处理逻辑
            process_single_product(product_id)
            results["success_count"] += 1
        except Exception as e:
            results["failed_count"] += 1
            results["errors"].append({
                "product_id": product_id,
                "error": str(e)
            })
    
    return results
```

### 7.2 添加新功能

#### 添加新的API端点
1. 在 `web_app.py` 中添加路由
2. 实现处理函数
3. 添加错误处理
4. 更新API文档

```python
@app.route('/api/new_feature', methods=['POST'])
def new_feature():
    try:
        data = request.get_json()
        # 处理逻辑
        result = process_new_feature(data)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

#### 添加新的HTML页面
1. 在 `templates/` 目录创建HTML文件
2. 使用Bootstrap样式保持一致性
3. 添加JavaScript交互逻辑
4. 在 `web_app.py` 中添加对应路由

### 7.3 测试指南

#### 单元测试
```python
import unittest
from unittest.mock import patch, MagicMock

class TestProductManager(unittest.TestCase):
    def setUp(self):
        self.manager = ProductManager()
    
    def test_load_data_success(self):
        # 测试数据加载成功的情况
        with patch('pandas.read_csv') as mock_read:
            mock_read.return_value.to_dict.return_value = [{'id': '1'}]
            self.manager.load_data()
            self.assertEqual(len(self.manager.data), 1)
    
    def test_load_data_file_not_found(self):
        # 测试文件不存在的情况
        with patch('os.path.exists', return_value=False):
            self.manager.load_data()
            self.assertEqual(self.manager.data, [])
```

#### 集成测试
```python
def test_full_workflow():
    # 测试完整的工作流程
    client = app.test_client()
    
    # 测试数据获取
    response = client.get('/api/data')
    assert response.status_code == 200
    
    # 测试图片下载
    response = client.post('/api/download', 
                          json={'selected_ids': ['123']})
    assert response.status_code == 200
```

---

## 8. 部署与运维

### 8.1 生产环境部署

#### 使用Gunicorn部署
```bash
# 安装Gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:8080 web_app:app
```

#### 使用Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "web_app:app"]
```

#### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 8.2 监控与日志

#### 日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# 文件日志
file_handler = RotatingFileHandler(
    'logs/app.log', 
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
))
app.logger.addHandler(file_handler)
```

#### 性能监控
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        app.logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper
```

### 8.3 备份策略

#### 数据备份
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/toolkit_$DATE"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据文件
cp -r images/csvdb $BACKUP_DIR/
cp -r logs $BACKUP_DIR/
cp -r reports $BACKUP_DIR/

# 压缩备份
tar -czf "$BACKUP_DIR.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "备份完成: $BACKUP_DIR.tar.gz"
```

#### 定时备份
```bash
# 添加到crontab
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup.sh
```

---

## 9. 故障排查

### 9.1 常见问题

#### 飞书API相关

**问题**: 获取访问令牌失败
```
错误信息: {"code": 99991663, "msg": "app not found"}
```
**解决方案**:
1. 检查 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否正确
2. 确认应用状态是否为"已启用"
3. 检查应用权限配置

**问题**: 表格读取失败
```
错误信息: {"code": 1254006, "msg": "no permission"}
```
**解决方案**:
1. 确认应用有表格读取权限
2. 检查 `FEISHU_SPREADSHEET_TOKEN` 是否正确
3. 确认表格已共享给应用

#### 图像处理相关

**问题**: 白底去除效果不佳
**解决方案**:
1. 调整白色容差参数
2. 检查输入图片质量
3. 尝试不同的处理算法

**问题**: PNG转换失败
```
错误信息: PIL.UnidentifiedImageError: cannot identify image file
```
**解决方案**:
1. 检查图片文件是否损坏
2. 确认图片格式是否支持
3. 检查文件路径是否正确

#### ComfyUI相关

**问题**: 连接ComfyUI失败
```
错误信息: requests.exceptions.ConnectionError
```
**解决方案**:
1. 确认ComfyUI服务是否启动
2. 检查 `COMFYUI_BASE_URL` 配置
3. 确认网络连接正常

**问题**: 工作流执行失败
**解决方案**:
1. 检查工作流JSON格式是否正确
2. 确认所需模型文件是否存在
3. 查看ComfyUI服务端日志

### 9.2 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 使用调试模式
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
```

#### 网络请求调试
```python
import requests
import logging

# 启用requests调试
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").propagate = True
```

### 9.3 性能优化

#### 数据库查询优化
```python
# 使用pandas的高效操作
df = pd.read_csv(file_path, usecols=['product_id', 'product_name'])
filtered_df = df[df['product_id'].isin(selected_ids)]
```

#### 图像处理优化
```python
# 使用多线程处理
from concurrent.futures import ThreadPoolExecutor

def process_images_parallel(image_paths):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_image, path) for path in image_paths]
        results = [future.result() for future in futures]
    return results
```

#### 内存使用优化
```python
# 及时释放大对象
import gc

def process_large_data(data):
    result = heavy_processing(data)
    del data  # 显式删除
    gc.collect()  # 强制垃圾回收
    return result
```

---

## 10. 更新日志

### v2.1.0 (2024-01-15)
#### 新增功能
- ✨ 添加PNG转换状态控制面板
- ✨ 实时处理进度显示
- ✨ 详细的错误信息展示
- ✨ 可折叠的状态界面

#### 改进
- 🔧 优化图像处理性能
- 🔧 改进错误处理机制
- 🔧 增强用户体验

#### 修复
- 🐛 修复大数字精度问题
- 🐛 修复并发处理时的状态同步问题

### v2.0.0 (2024-01-01)
#### 新增功能
- ✨ 完整的ERP系统界面
- ✨ CSV数据导入功能
- ✨ 已选商品管理
- ✨ 批量PNG转换
- ✨ 飞书表格集成

#### 重大变更
- 🔄 重构Web应用架构
- 🔄 统一API接口设计
- 🔄 改进数据存储结构

### v1.5.0 (2023-12-01)
#### 新增功能
- ✨ Web界面产品管理
- ✨ 分页浏览功能
- ✨ 批量图片下载
- ✨ 下载状态跟踪

### v1.0.0 (2023-11-01)
#### 初始版本
- ✨ 飞书API集成
- ✨ ComfyUI工作流执行
- ✨ 基础图像处理
- ✨ 命令行工具

---

## 📞 技术支持

如果您在使用过程中遇到问题，请：

1. 查阅本文档的故障排查部分
2. 检查日志文件获取详细错误信息
3. 确认配置文件设置正确
4. 联系技术支持团队

---

**文档版本**: v2.1.0  
**最后更新**: 2024-01-15  
**维护者**: 开发团队

---

*本文档涵盖了项目的所有核心功能和技术细节，为开发者和用户提供完整的参考指南。*