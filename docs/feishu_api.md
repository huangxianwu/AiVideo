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

### 电子表格图片上传专门流程

**重要说明：** 若需要在电子表格中添加图片，必须使用以下专门流程，不能使用普通的文件上传接口。

#### 步骤1：上传图片素材到飞书云空间

**接口地址：**
```
POST https://open.feishu.cn/open-apis/drive/v1/medias/upload_all
```

**请求方式：** multipart/form-data

**必需参数：**
- `file_name`: 要上传的素材的名称（如 "demo.jpeg"）
- `parent_type`: 上传点类型，电子表格图片必须设为 `"sheet_image"`
- `parent_node`: 电子表格的 `spreadsheet_token`
- `size`: 文件大小（字节）
- `file`: 文件的二进制内容

**可选参数：**
- `checksum`: 文件的 Adler-32 校验和
- `extra`: 特殊场景下的额外参数

**Python实现示例：**
```python
def upload_image_to_feishu(self, image_path: str) -> str:
    """上传图片素材到飞书云空间，用于电子表格"""
    import os
    from requests_toolbelt import MultipartEncoder
    
    file_size = os.path.getsize(image_path)
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    
    form = {
        'file_name': os.path.basename(image_path),
        'parent_type': 'sheet_image',
        'parent_node': self.config.spreadsheet_token,
        'size': str(file_size),
        'file': (open(image_path, 'rb'))
    }
    
    multi_form = MultipartEncoder(form)
    headers = {
        'Authorization': f'Bearer {self.get_tenant_access_token()}',
        'Content-Type': multi_form.content_type
    }
    
    response = requests.post(url, headers=headers, data=multi_form)
    
    if response.status_code == 200:
        result = response.json()
        return result['data']['file_token']
    else:
        raise Exception(f"上传失败: {response.text}")
```

#### 步骤2：写入图片到电子表格单元格

**接口地址：**
```
POST https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_image
```

**请求头：**
```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

**请求体参数：**
- `range`: 指定写入图片的单元格，格式为 `<sheetId>!<开始单元格>:<结束单元格>`
- `image`: 图片的二进制流数组
- `name`: 写入的图片名称（需加后缀名）

**Python实现示例：**
```python
def write_image_to_cell(self, image_path: str, sheet_id: str, cell: str) -> bool:
    """直接写入图片文件到电子表格单元格"""
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.config.spreadsheet_token}/values_image"
    
    # 读取图片二进制数据
    with open(image_path, 'rb') as f:
        image_data = list(f.read())
    
    payload = {
        "range": f"{sheet_id}!{cell}:{cell}",
        "image": image_data,
        "name": os.path.basename(image_path)
    }
    
    headers = {
        "Authorization": f"Bearer {self.get_tenant_access_token()}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return True
    else:
        print(f"写入图片失败: {response.text}")
        return False
```

### 普通文件上传（非电子表格）

**接口地址：**
```
POST https://open.feishu.cn/open-apis/im/v1/files
```

**请求方式：** multipart/form-data

**参数：**
- `file_type`: "image"
- `file_name`: 文件名
- `file`: 文件二进制数据

**注意：** 此接口仅用于聊天消息等场景，不适用于电子表格图片上传。

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
- [上传素材API文档](https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all)
- [写入图片到电子表格API文档](https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/write-images)
- [普通文件上传API文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/file/create)