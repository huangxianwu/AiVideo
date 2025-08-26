# 飞书API使用说明

## 概述
本文档记录了项目中使用的飞书API接口和使用方法，供AI IDE开发过程参考。

## 认证配置

### 环境变量
```bash
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

### 获取访问令牌
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

## 表格操作API

### 1. 读取表格数据

**接口地址：**
```
GET https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range}
```

**请求头：**
```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

**参数说明：**
- `spreadsheet_token`: 表格的唯一标识
- `range`: 读取范围，格式如 "A2:H1000"

**响应示例：**
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "values": [
            ["产品图片", "模特图片", "产品描述", "状态", "生成图片", "产品名称", "颜色", "尺寸"]
        ]
    }
}
```

### 2. 写入表格数据

**接口地址：**
```
PUT https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values
```

**请求体：**
```json
{
    "valueRange": {
        "range": "E2:E2",
        "values": [[
            {
                "type": "image",
                "image": {
                    "file_token": "file_token_here",
                    "width": 200,
                    "height": 200
                }
            }
        ]]
    }
}
```

## 文件上传API

### 上传图片到飞书云空间

**接口地址：**
```
POST https://open.feishu.cn/open-apis/im/v1/files
```

**请求方式：** multipart/form-data

**参数：**
- `file_type`: "image"
- `file_name`: 文件名
- `file`: 文件二进制数据

**Python实现示例：**
```python
def upload_image_to_feishu(self, image_path: str) -> str:
    url = "https://open.feishu.cn/open-apis/im/v1/files"
    
    with open(image_path, 'rb') as f:
        files = {
            'file_type': (None, 'image'),
            'file_name': (None, os.path.basename(image_path)),
            'file': (os.path.basename(image_path), f, 'image/png')
        }
        
        headers = {
            "Authorization": f"Bearer {self.get_tenant_access_token()}"
        }
        
        response = requests.post(url, files=files, headers=headers)
        
    if response.status_code == 200:
        result = response.json()
        return result['data']['file_key']
    else:
        raise Exception(f"上传失败: {response.text}")
```

## 错误处理

### 常见错误码
- `99991663`: 应用权限不足
- `99991664`: 租户令牌无效
- `99991665`: 用户令牌无效
- `99991668`: 应用被封禁

### 重试机制
```python
def retry_request(func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))
```

## 注意事项

1. **令牌有效期**: tenant_access_token有效期为2小时，需要定期刷新
2. **请求频率限制**: 建议控制请求频率，避免触发限流
3. **文件大小限制**: 上传文件大小不能超过30MB
4. **图片格式**: 支持PNG、JPG、GIF等常见格式
5. **表格范围**: 使用A1标记法指定单元格范围

## 参考链接

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [表格API文档](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN)
- [文件上传API文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/file/create)