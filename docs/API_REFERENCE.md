# API参考文档

## 📋 目录

- [1. Web API接口](#1-web-api接口)
- [2. 飞书API集成](#2-飞书api集成)
- [3. ComfyUI API集成](#3-comfyui-api集成)
- [4. 错误处理](#4-错误处理)
- [5. 认证与授权](#5-认证与授权)
- [6. 限流与配额](#6-限流与配额)

---

## 1. Web API接口

### 1.1 产品数据管理

#### 获取产品列表
```http
GET /api/data
```

**查询参数:**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| per_page | integer | 否 | 50 | 每页数量 |

**响应示例:**
```json
{
  "data": [
    {
      "product_id": "123456789",
      "product_name": "测试商品",
      "image_url": "https://example.com/image.jpg",
      "downloaded": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "total_pages": 20,
    "has_next": true,
    "has_prev": false
  }
}
```

#### 刷新产品数据
```http
GET /api/refresh
```

**响应示例:**
```json
{
  "success": true,
  "message": "数据刷新成功",
  "total_count": 1000
}
```

### 1.2 图片下载管理

#### 批量下载图片
```http
POST /api/download
Content-Type: application/json
```

**请求体:**
```json
{
  "selected_ids": ["123456789", "987654321"]
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "下载完成",
  "downloaded_count": 2,
  "failed_count": 0,
  "failed_products": [],
  "download_details": [
    {
      "product_id": "123456789",
      "status": "success",
      "file_path": "images/jpg/123456789.jpg"
    }
  ]
}
```

#### 获取已下载商品
```http
GET /api/downloaded
```

**响应示例:**
```json
{
  "data": [
    {
      "product_id": "123456789",
      "product_name": "测试商品",
      "image_url": "https://example.com/image.jpg",
      "local_path": "images/jpg/123456789.jpg",
      "downloaded_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 100
}
```

### 1.3 PNG转换与处理

#### PNG转换接口
```http
POST /api/convert_to_png
Content-Type: application/json
```

**请求体:**
```json
{
  "selected_ids": ["123456789", "987654321"]
}
```

**响应示例:**
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
      "product_name": "测试商品",
      "status": "success",
      "message": "处理完成",
      "timestamp": "2024-01-01T12:00:00Z",
      "output_path": "images/png/123456789.png"
    },
    {
      "product_id": "987654321",
      "product_name": "测试商品2",
      "status": "failed",
      "message": "图片下载失败",
      "timestamp": "2024-01-01T12:01:00Z",
      "error_code": "DOWNLOAD_ERROR"
    }
  ]
}
```

### 1.4 CSV数据导入

#### 导入CSV文件
```http
POST /import-csv
Content-Type: multipart/form-data
```

**请求参数:**
- `file`: CSV文件 (multipart/form-data)

**响应示例:**
```json
{
  "success": true,
  "message": "CSV导入成功",
  "imported_count": 500,
  "skipped_count": 10,
  "error_count": 2,
  "errors": [
    {
      "row": 15,
      "error": "缺少必填字段: product_name"
    }
  ]
}
```

---

## 2. 飞书API集成

### 2.1 认证管理

#### 获取租户访问令牌
```python
def get_tenant_access_token(self) -> str:
    """
    获取飞书租户访问令牌
    
    Returns:
        str: 访问令牌
        
    Raises:
        AuthenticationError: 认证失败时抛出
    """
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": self.app_id,
        "app_secret": self.app_secret
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get('code') != 0:
        raise AuthenticationError(f"获取访问令牌失败: {data.get('msg')}")
    
    return data.get('tenant_access_token')
```

#### API请求头设置
```python
def _get_headers(self) -> Dict[str, str]:
    """
    获取API请求头
    
    Returns:
        Dict[str, str]: 请求头字典
    """
    return {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
```

### 2.2 表格操作

#### 读取表格数据
```python
def read_spreadsheet_data(self, spreadsheet_token: str, range_str: str) -> Dict[str, Any]:
    """
    读取飞书表格数据
    
    Args:
        spreadsheet_token: 表格token
        range_str: 数据范围，如 "Sheet1!A1:Z1000"
        
    Returns:
        Dict[str, Any]: 表格数据
        
    Raises:
        APIError: API调用失败时抛出
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}"
    
    response = requests.get(url, headers=self._get_headers())
    data = response.json()
    
    if data.get('code') != 0:
        raise APIError(f"读取表格失败: {data.get('msg')}")
    
    return data.get('data', {})
```

#### 写入表格数据
```python
def write_spreadsheet_data(self, spreadsheet_token: str, range_str: str, values: List[List[Any]]) -> bool:
    """
    写入数据到飞书表格
    
    Args:
        spreadsheet_token: 表格token
        range_str: 写入范围
        values: 要写入的数据
        
    Returns:
        bool: 写入是否成功
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
    
    payload = {
        "valueRange": {
            "range": range_str,
            "values": values
        }
    }
    
    response = requests.put(url, json=payload, headers=self._get_headers())
    data = response.json()
    
    return data.get('code') == 0
```

### 2.3 文件上传

#### 上传图片到飞书云空间
```python
def upload_image_to_feishu(self, image_path: str) -> Optional[str]:
    """
    上传图片到飞书云空间
    
    Args:
        image_path: 本地图片路径
        
    Returns:
        Optional[str]: 图片token，失败时返回None
    """
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    
    with open(image_path, 'rb') as f:
        files = {
            'image': (os.path.basename(image_path), f, 'image/png')
        }
        data = {
            'image_type': 'message'
        }
        
        response = requests.post(
            url, 
            files=files, 
            data=data, 
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
    
    result = response.json()
    
    if result.get('code') == 0:
        return result.get('data', {}).get('image_key')
    else:
        logger.error(f"图片上传失败: {result.get('msg')}")
        return None
```

#### 将图片写入表格单元格
```python
def write_image_to_cell(self, spreadsheet_token: str, range_str: str, image_token: str) -> bool:
    """
    将图片写入表格单元格
    
    Args:
        spreadsheet_token: 表格token
        range_str: 单元格范围
        image_token: 图片token
        
    Returns:
        bool: 写入是否成功
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
    
    # 构造图片对象
    image_object = {
        "image": {
            "image_key": image_token
        }
    }
    
    payload = {
        "valueRange": {
            "range": range_str,
            "values": [[image_object]]
        }
    }
    
    response = requests.put(url, json=payload, headers=self._get_headers())
    data = response.json()
    
    return data.get('code') == 0
```

### 2.4 表格信息获取

#### 获取表格元信息
```python
def get_spreadsheet_info(self, spreadsheet_token: str) -> Dict[str, Any]:
    """
    获取表格基本信息
    
    Args:
        spreadsheet_token: 表格token
        
    Returns:
        Dict[str, Any]: 表格信息
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}"
    
    response = requests.get(url, headers=self._get_headers())
    data = response.json()
    
    if data.get('code') == 0:
        return data.get('data', {})
    else:
        raise APIError(f"获取表格信息失败: {data.get('msg')}")
```

#### 获取工作表列表
```python
def get_sheets_list(self, spreadsheet_token: str) -> List[Dict[str, Any]]:
    """
    获取表格中的所有工作表
    
    Args:
        spreadsheet_token: 表格token
        
    Returns:
        List[Dict[str, Any]]: 工作表列表
    """
    spreadsheet_info = self.get_spreadsheet_info(spreadsheet_token)
    return spreadsheet_info.get('sheets', [])
```

---

## 3. ComfyUI API集成

### 3.1 基础连接

#### 初始化客户端
```python
class ComfyUIClient:
    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 响应对象
            
        Raises:
            ConnectionError: 连接失败时抛出
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"ComfyUI API请求失败: {str(e)}")
```

#### 检查服务状态
```python
def check_status(self) -> bool:
    """
    检查ComfyUI服务是否可用
    
    Returns:
        bool: 服务是否可用
    """
    try:
        response = self._make_request('GET', '/system_stats')
        return response.status_code == 200
    except:
        return False
```

### 3.2 图片上传

#### 上传图片文件
```python
def upload_image(self, image_path: str, subfolder: str = "", overwrite: bool = False) -> Dict[str, Any]:
    """
    上传图片到ComfyUI
    
    Args:
        image_path: 本地图片路径
        subfolder: 子文件夹名称
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        Dict[str, Any]: 上传结果
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
        UploadError: 上传失败时抛出
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {
            'image': (os.path.basename(image_path), f, 'image/jpeg')
        }
        data = {
            'subfolder': subfolder,
            'overwrite': str(overwrite).lower()
        }
        
        response = self._make_request('POST', '/upload/image', files=files, data=data)
        result = response.json()
        
        if 'name' not in result:
            raise UploadError(f"图片上传失败: {result}")
        
        return result
```

#### 获取上传的图片
```python
def get_image(self, filename: str, subfolder: str = "", folder_type: str = "input") -> bytes:
    """
    获取上传的图片数据
    
    Args:
        filename: 文件名
        subfolder: 子文件夹
        folder_type: 文件夹类型 (input/output/temp)
        
    Returns:
        bytes: 图片二进制数据
    """
    params = {
        'filename': filename,
        'subfolder': subfolder,
        'type': folder_type
    }
    
    response = self._make_request('GET', '/view', params=params)
    return response.content
```

### 3.3 工作流执行

#### 提交工作流任务
```python
def execute_workflow(self, workflow_data: Dict[str, Any], client_id: Optional[str] = None) -> str:
    """
    执行ComfyUI工作流
    
    Args:
        workflow_data: 工作流配置数据
        client_id: 客户端ID，用于WebSocket连接
        
    Returns:
        str: 任务ID
        
    Raises:
        WorkflowError: 工作流执行失败时抛出
    """
    payload = {
        "prompt": workflow_data
    }
    
    if client_id:
        payload["client_id"] = client_id
    
    response = self._make_request('POST', '/prompt', json=payload)
    result = response.json()
    
    if 'prompt_id' not in result:
        raise WorkflowError(f"工作流提交失败: {result}")
    
    return result['prompt_id']
```

#### 检查任务状态
```python
def check_task_status(self, task_id: str) -> Dict[str, Any]:
    """
    检查任务执行状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict[str, Any]: 任务状态信息
    """
    response = self._make_request('GET', f'/history/{task_id}')
    history = response.json()
    
    if task_id not in history:
        return {
            'status': 'pending',
            'progress': 0,
            'message': '任务排队中'
        }
    
    task_info = history[task_id]
    
    if 'outputs' in task_info:
        return {
            'status': 'completed',
            'progress': 100,
            'message': '任务完成',
            'outputs': task_info['outputs']
        }
    elif 'status' in task_info and task_info['status'].get('completed', False):
        return {
            'status': 'completed',
            'progress': 100,
            'message': '任务完成'
        }
    else:
        return {
            'status': 'running',
            'progress': 50,
            'message': '任务执行中'
        }
```

#### 等待任务完成
```python
def wait_for_completion(self, task_id: str, timeout: int = 300, poll_interval: int = 2) -> Dict[str, Any]:
    """
    等待任务完成
    
    Args:
        task_id: 任务ID
        timeout: 超时时间（秒）
        poll_interval: 轮询间隔（秒）
        
    Returns:
        Dict[str, Any]: 最终任务状态
        
    Raises:
        TimeoutError: 超时时抛出
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = self.check_task_status(task_id)
        
        if status['status'] in ['completed', 'failed']:
            return status
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"任务 {task_id} 执行超时")
```

### 3.4 输出文件管理

#### 下载输出文件
```python
def download_output(self, task_id: str, output_dir: str) -> List[str]:
    """
    下载任务输出文件
    
    Args:
        task_id: 任务ID
        output_dir: 输出目录
        
    Returns:
        List[str]: 下载的文件路径列表
    """
    status = self.check_task_status(task_id)
    
    if status['status'] != 'completed' or 'outputs' not in status:
        raise ValueError(f"任务 {task_id} 未完成或无输出")
    
    downloaded_files = []
    outputs = status['outputs']
    
    for node_id, node_output in outputs.items():
        if 'images' in node_output:
            for image_info in node_output['images']:
                filename = image_info['filename']
                subfolder = image_info.get('subfolder', '')
                
                # 下载图片
                image_data = self.get_image(filename, subfolder, 'output')
                
                # 保存到本地
                local_path = os.path.join(output_dir, filename)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                
                downloaded_files.append(local_path)
    
    return downloaded_files
```

#### 清理临时文件
```python
def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
    """
    清理临时文件
    
    Args:
        older_than_hours: 清理多少小时前的文件
        
    Returns:
        int: 清理的文件数量
    """
    response = self._make_request('POST', '/free', json={
        'unload_models': False,
        'free_memory': True
    })
    
    # 这里可以添加更多清理逻辑
    return 0
```

---

## 4. 错误处理

### 4.1 自定义异常类

```python
class APIError(Exception):
    """API调用异常"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AuthenticationError(APIError):
    """认证失败异常"""
    pass

class UploadError(APIError):
    """文件上传异常"""
    pass

class WorkflowError(APIError):
    """工作流执行异常"""
    pass

class ProcessingError(Exception):
    """数据处理异常"""
    pass
```

### 4.2 错误码定义

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| AUTH_001 | 访问令牌无效 | 重新获取令牌 |
| AUTH_002 | 应用权限不足 | 检查应用权限配置 |
| API_001 | 请求参数错误 | 检查请求参数格式 |
| API_002 | 资源不存在 | 确认资源ID正确 |
| API_003 | 请求频率超限 | 降低请求频率 |
| UPLOAD_001 | 文件格式不支持 | 检查文件格式 |
| UPLOAD_002 | 文件大小超限 | 压缩文件大小 |
| WORKFLOW_001 | 工作流配置错误 | 检查工作流JSON |
| WORKFLOW_002 | 模型文件缺失 | 确认模型文件存在 |
| PROCESS_001 | 图像处理失败 | 检查图像文件 |
| PROCESS_002 | 数据格式错误 | 检查数据格式 |

### 4.3 统一错误处理

```python
def handle_api_error(func):
    """
    API错误处理装饰器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            raise APIError("网络连接失败", "NETWORK_001")
        except requests.exceptions.Timeout:
            raise APIError("请求超时", "NETWORK_002")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("认证失败", "AUTH_001")
            elif e.response.status_code == 403:
                raise AuthenticationError("权限不足", "AUTH_002")
            elif e.response.status_code == 429:
                raise APIError("请求频率超限", "API_003")
            else:
                raise APIError(f"HTTP错误: {e.response.status_code}", "HTTP_ERROR")
        except Exception as e:
            logger.exception(f"未知错误: {str(e)}")
            raise APIError("系统内部错误", "SYSTEM_001")
    
    return wrapper
```

---

## 5. 认证与授权

### 5.1 飞书应用认证

#### 应用权限配置
```python
REQUIRED_SCOPES = [
    "sheets:spreadsheet:readonly",    # 查看电子表格
    "sheets:spreadsheet:write",       # 编辑电子表格
    "drive:drive:readonly",           # 查看云空间文件
    "drive:drive:write",              # 编辑云空间文件
]

def verify_permissions(self) -> bool:
    """
    验证应用权限
    
    Returns:
        bool: 权限是否足够
    """
    # 这里可以添加权限验证逻辑
    return True
```

#### 令牌刷新机制
```python
class TokenManager:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = None
        self.token_expires_at = None
    
    def get_valid_token(self) -> str:
        """
        获取有效的访问令牌
        
        Returns:
            str: 访问令牌
        """
        if self.token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.token
        
        # 刷新令牌
        self.refresh_token()
        return self.token
    
    def refresh_token(self):
        """
        刷新访问令牌
        """
        # 实现令牌刷新逻辑
        pass
```

### 5.2 API密钥管理

#### 安全存储
```python
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.key)
    
    def encrypt_secret(self, secret: str) -> str:
        """
        加密敏感信息
        
        Args:
            secret: 要加密的字符串
            
        Returns:
            str: 加密后的字符串
        """
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        解密敏感信息
        
        Args:
            encrypted_secret: 加密的字符串
            
        Returns:
            str: 解密后的字符串
        """
        return self.cipher.decrypt(encrypted_secret.encode()).decode()
```

---

## 6. 限流与配额

### 6.1 请求限流

#### 令牌桶算法
```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = Lock()
    
    def is_allowed(self) -> bool:
        """
        检查是否允许请求
        
        Returns:
            bool: 是否允许
        """
        with self.lock:
            now = time.time()
            
            # 清理过期请求
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                return False
            
            # 记录当前请求
            self.requests.append(now)
            return True
    
    def wait_time(self) -> float:
        """
        获取需要等待的时间
        
        Returns:
            float: 等待时间（秒）
        """
        if not self.requests:
            return 0
        
        oldest_request = min(self.requests)
        return max(0, self.time_window - (time.time() - oldest_request))
```

#### 使用限流器
```python
# 创建限流器：每分钟最多100个请求
feishu_limiter = RateLimiter(max_requests=100, time_window=60)
comfyui_limiter = RateLimiter(max_requests=50, time_window=60)

@handle_api_error
def rate_limited_request(limiter: RateLimiter, func, *args, **kwargs):
    """
    带限流的请求
    """
    if not limiter.is_allowed():
        wait_time = limiter.wait_time()
        raise APIError(f"请求频率超限，请等待 {wait_time:.1f} 秒", "RATE_LIMIT")
    
    return func(*args, **kwargs)
```

### 6.2 配额管理

#### 每日配额跟踪
```python
class QuotaManager:
    def __init__(self):
        self.daily_limits = {
            'feishu_api_calls': 10000,
            'comfyui_workflows': 1000,
            'image_uploads': 5000
        }
        self.usage = {}
        self.reset_date = None
    
    def check_quota(self, resource: str, amount: int = 1) -> bool:
        """
        检查配额是否足够
        
        Args:
            resource: 资源类型
            amount: 使用数量
            
        Returns:
            bool: 配额是否足够
        """
        self._reset_if_new_day()
        
        current_usage = self.usage.get(resource, 0)
        limit = self.daily_limits.get(resource, 0)
        
        return current_usage + amount <= limit
    
    def consume_quota(self, resource: str, amount: int = 1) -> bool:
        """
        消费配额
        
        Args:
            resource: 资源类型
            amount: 消费数量
            
        Returns:
            bool: 是否成功消费
        """
        if not self.check_quota(resource, amount):
            return False
        
        self.usage[resource] = self.usage.get(resource, 0) + amount
        return True
    
    def _reset_if_new_day(self):
        """
        如果是新的一天，重置配额
        """
        today = time.strftime('%Y-%m-%d')
        if self.reset_date != today:
            self.usage = {}
            self.reset_date = today
```

---

**文档版本**: v1.0.0  
**最后更新**: 2024-01-15  
**维护者**: 开发团队

---

*本API参考文档提供了完整的接口说明和使用示例，帮助开发者快速集成和使用系统功能。*