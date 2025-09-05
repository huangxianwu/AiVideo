# ComfyUI API使用说明

## 概述
本文档记录了项目中使用的ComfyUI API接口和工作流配置，供AI IDE开发过程参考。

## 基础配置

### 环境变量
```bash
COMFYUI_BASE_URL=https://your-comfyui-server.com
COMFYUI_API_KEY=your_api_key
```

### 客户端初始化
```python
class ComfyUIClient:
    def __init__(self):
        self.base_url = os.getenv('COMFYUI_BASE_URL')
        self.api_key = os.getenv('COMFYUI_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
```

## 核心API接口

### 1. 上传图片

**接口地址：**
```
POST {base_url}/upload/image
```

**请求方式：** multipart/form-data

**参数：**
- `image`: 图片文件
- `type`: 图片类型 ("input" 或 "temp")
- `subfolder`: 子文件夹名称（可选）

**Python实现：**
```python
def upload_image(self, image_path: str, image_type: str = "input") -> str:
    url = f"{self.base_url}/upload/image"
    
    with open(image_path, 'rb') as f:
        files = {
            'image': (os.path.basename(image_path), f, 'image/png'),
            'type': (None, image_type)
        }
        
        response = self.session.post(url, files=files)
        
    if response.status_code == 200:
        return response.json()['name']
    else:
        raise Exception(f"上传失败: {response.text}")
```

### 2. 执行工作流

**接口地址：**
```
POST {base_url}/prompt
```

**请求体结构：**
```json
{
    "prompt": {
        "1": {
            "inputs": {
                "image": "product_image.png",
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {
                "title": "Load Product Image"
            }
        },
        "2": {
            "inputs": {
                "image": "model_image.png",
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {
                "title": "Load Model Image"
            }
        }
    }
}
```

**Python实现：**
```python
def execute_workflow(self, workflow_data: dict) -> WorkflowResult:
    url = f"{self.base_url}/prompt"
    
    response = self.session.post(url, json={"prompt": workflow_data})
    
    if response.status_code == 200:
        result = response.json()
        return WorkflowResult(
            success=True,
            task_id=result['prompt_id'],
            status='QUEUED',
            output_urls=[],
            error=None
        )
    else:
        return WorkflowResult(
            success=False,
            task_id=None,
            status='FAILED',
            output_urls=[],
            error=response.text
        )
```

### 3. 检查任务状态

**接口地址：**
```
GET {base_url}/history/{prompt_id}
```

**响应示例：**
```json
{
    "prompt_id": {
        "prompt": [...],
        "outputs": {
            "9": {
                "images": [
                    {
                        "filename": "output_image.png",
                        "subfolder": "",
                        "type": "output"
                    }
                ]
            }
        },
        "status": {
            "status_str": "success",
            "completed": true,
            "messages": []
        }
    }
}
```

**Python实现：**
```python
def check_task_status(self, task_id: str) -> WorkflowResult:
    url = f"{self.base_url}/history/{task_id}"
    
    response = self.session.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if task_id in data:
            task_data = data[task_id]
            status = task_data.get('status', {})
            
            if status.get('completed', False):
                # 提取输出文件
                output_urls = []
                outputs = task_data.get('outputs', {})
                
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for image in node_output['images']:
                            filename = image['filename']
                            output_urls.append(f"{self.base_url}/view?filename={filename}")
                
                return WorkflowResult(
                    success=True,
                    task_id=task_id,
                    status='SUCCESS',
                    output_urls=output_urls,
                    error=None
                )
            else:
                return WorkflowResult(
                    success=True,
                    task_id=task_id,
                    status='RUNNING',
                    output_urls=[],
                    error=None
                )
    
    return WorkflowResult(
        success=False,
        task_id=task_id,
        status='FAILED',
        output_urls=[],
        error="无法获取任务状态"
    )
```

### 4. 下载输出文件

**接口地址：**
```
GET {base_url}/view?filename={filename}&type=output
```

**Python实现：**
```python
def download_output(self, filename: str, save_path: str) -> bool:
    url = f"{self.base_url}/view"
    params = {
        'filename': filename,
        'type': 'output'
    }
    
    response = self.session.get(url, params=params)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False
```

## 工作流配置

### 标准工作流结构
项目使用的工作流包含以下主要节点：

1. **LoadImage (节点1)**: 加载产品图片
2. **LoadImage (节点2)**: 加载模特图片
3. **图像处理节点**: 进行图像合成和处理
4. **SaveImage (节点9)**: 保存输出图片

### 工作流文件
工作流配置保存在 `My workflow python.json` 文件中，包含完整的节点定义和连接关系。

## 数据模型

### WorkflowResult
```python
@dataclass
class WorkflowResult:
    success: bool
    task_id: Optional[str]
    status: str  # QUEUED, RUNNING, SUCCESS, FAILED
    output_urls: List[str]
    error: Optional[str]
```

## 错误处理

### 常见错误
1. **上传失败**: 检查文件路径和格式
2. **工作流执行失败**: 检查节点配置和输入参数
3. **任务超时**: 实现重试机制和超时处理

### 重试机制
```python
def wait_for_completion(self, task_id: str, timeout: int = 300) -> WorkflowResult:
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = self.check_task_status(task_id)
        
        if result.status in ['SUCCESS', 'FAILED']:
            return result
        
        time.sleep(30)  # 等待30秒后重新检查
    
    return WorkflowResult(
        success=False,
        task_id=task_id,
        status='TIMEOUT',
        output_urls=[],
        error='任务执行超时'
    )
```

## 性能优化

1. **并发控制**: 限制同时执行的工作流数量
2. **缓存机制**: 缓存已上传的图片
3. **连接池**: 使用requests.Session复用连接
4. **超时设置**: 合理设置请求超时时间

## 注意事项

1. **文件格式**: 支持PNG、JPG等常见图片格式
2. **文件大小**: 建议控制在10MB以内
3. **并发限制**: 避免同时提交过多任务
4. **错误重试**: 实现合理的重试策略
5. **资源清理**: 及时清理临时文件

## 参考链接

- [ComfyUI官方文档](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI API参考](https://github.com/comfyanonymous/ComfyUI/wiki/API-Reference)