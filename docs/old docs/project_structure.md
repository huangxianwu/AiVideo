# 项目结构说明

## 概述
本文档详细描述了工具包项目的文件组织结构和各模块的功能，供AI IDE开发过程参考。

## 项目目录结构

```
toolKit/
├── .env                          # 环境变量配置文件
├── .env.example                  # 环境变量配置模板
├── README.md                     # 项目说明文档
├── requirements.txt              # Python依赖包列表
├── main.py                       # 主程序入口
├── config.py                     # 配置管理模块
├── comfyui_client.py            # ComfyUI API客户端
├── feishu_client.py             # 飞书API客户端
├── workflow_processor.py        # 工作流处理器
├── My workflow python.json      # ComfyUI工作流配置文件
├── docs/                         # 文档目录
│   ├── feishu_api.md            # 飞书API使用说明
│   ├── comfyui_api.md           # ComfyUI API使用说明
│   ├── project_structure.md     # 项目结构说明（本文档）
│   └── workflow_guide.md        # 工作流程说明
├── web_app.py                   # Web应用主程序
├── white_background_remover.py  # 白底去除处理模块
├── templates/                    # Web模板目录
│   ├── index.html              # 主页模板
│   ├── selected.html           # 选择页面模板
│   ├── downloaded.html         # 下载完成页面模板
│   ├── error.html              # 错误页面模板
│   ├── workflow.html           # 工作流页面模板
│   ├── workflow_execute.html   # 工作流执行页面模板
│   ├── workflow_management.html # 工作流管理页面模板
│   ├── erp_index.html          # ERP主页模板
│   └── erp_selected.html       # ERP选择页面模板
├── output/                       # 生成图片输出目录
├── temp/                         # 临时文件目录
├── logs/                         # 日志文件目录
├── reports/                      # 处理报告目录
├── static/                       # 静态资源目录
└── __pycache__/                  # Python缓存目录
```

## 核心模块说明

### 1. main.py - 主程序入口
**功能：** 程序的主入口点，协调各个模块完成整体工作流程

**主要职责：**
- 初始化配置和客户端
- 启动工作流处理器
- 处理命令行参数
- 异常处理和日志记录

**关键代码结构：**
```python
def main():
    # 初始化配置
    # 创建客户端实例
    # 启动工作流处理
    # 生成处理报告
```

### 2. config.py - 配置管理
**功能：** 统一管理项目配置，包括API密钥、URL等

**配置项：**
- 飞书应用配置（APP_ID, APP_SECRET）
- ComfyUI服务配置（BASE_URL, API_KEY）
- 表格配置（SPREADSHEET_TOKEN, RANGE）
- 文件路径配置

### 3. feishu_client.py - 飞书API客户端
**功能：** 封装飞书开放平台API，提供表格操作和文件上传功能

**主要方法：**
- `get_tenant_access_token()`: 获取访问令牌
- `read_spreadsheet_data()`: 读取表格数据
- `upload_image_to_feishu()`: 上传图片到飞书云空间
- `write_image_to_cell()`: 将图片写入表格单元格
- `update_cell_status()`: 更新单元格状态

### 4. comfyui_client.py - ComfyUI API客户端
**功能：** 封装ComfyUI API，提供图像处理工作流执行功能

**主要方法：**
- `upload_image()`: 上传图片到ComfyUI
- `execute_workflow()`: 执行工作流
- `check_task_status()`: 检查任务状态
- `wait_for_completion()`: 等待任务完成
- `download_output()`: 下载输出文件

**数据模型：**
```python
@dataclass
class WorkflowResult:
    success: bool
    task_id: Optional[str]
    status: str
    output_urls: List[str]
    error: Optional[str]
```

### 5. workflow_processor.py - 工作流处理器
**功能：** 核心业务逻辑，协调各个客户端完成数据处理流程

### 6. web_app.py - Web应用主程序
**功能：** Flask Web应用，提供图形化界面和API接口

**主要路由：**
- `/`: 主页，显示工作流选择界面
- `/workflow/<workflow_name>`: 工作流执行页面
- `/erp`: ERP系统主页
- `/erp/convert_to_png`: PNG转换功能
- `/api/*`: RESTful API接口

### 7. white_background_remover.py - 白底去除处理模块
**功能：** 图像白色背景去除和PNG转换

**主要类：**
- `WhiteBackgroundRemover`: 白底去除处理器
- 支持批量处理和单张图片处理
- 自动检测和去除白色背景
- 输出透明背景PNG格式

**主要方法：**
- `process_all_rows()`: 处理所有数据行
- `process_single_row()`: 处理单行数据
- `download_image()`: 下载图片
- `generate_filename()`: 生成文件名
- `_wait_for_previous_task()`: 等待前一个任务完成

**数据模型：**
```python
@dataclass
class RowData:
    row_index: int
    product_image_url: str
    model_image_url: str
    product_description: str
    status: str
    generated_image: str
    product_name: str
    color: str
    size: str
```

## 配置文件说明

### .env 环境变量
```bash
# 飞书应用配置
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxx
FEISHU_SPREADSHEET_TOKEN=xxxxxxxxxx
FEISHU_RANGE=A2:H1000

# ComfyUI配置
COMFYUI_BASE_URL=https://your-comfyui-server.com
COMFYUI_API_KEY=your_api_key

# 其他配置
MAX_CONCURRENT_TASKS=3
TASK_TIMEOUT=300
```

### requirements.txt 依赖包
```
requests>=2.28.0
python-dotenv>=0.19.0
Pillow>=9.0.0
Flask>=2.0.0
numpy>=1.21.0
opencv-python>=4.5.0
scikit-image>=0.18.0
```

### My workflow python.json 工作流配置
ComfyUI工作流的JSON配置文件，定义了图像处理的节点和连接关系。

## 数据流程

### 1. 数据读取流程
```
飞书表格 → feishu_client.read_spreadsheet_data() → RowData对象列表
```

### 2. 图像处理流程
```
下载产品图片 → 下载模特图片 → 上传到ComfyUI → 执行工作流 → 下载结果
```

### 3. 结果写入流程
```
本地保存图片 → 上传到飞书云空间 → 写入表格E列 → 更新状态为"已完成"
```

## 日志和报告

### 日志文件
- **位置：** `logs/workflow_YYYYMMDD_HHMMSS.log`
- **内容：** 详细的处理过程、错误信息、性能数据
- **格式：** 时间戳 + 日志级别 + 消息内容

### 处理报告
- **位置：** `reports/report_YYYYMMDD_HHMMSS.txt`
- **内容：** 处理结果汇总、成功/失败统计、错误详情

## 错误处理机制

### 1. 网络错误
- 自动重试机制（最多3次）
- 指数退避策略
- 超时设置

### 2. API错误
- 错误码识别和分类处理
- 详细错误日志记录
- 用户友好的错误提示

### 3. 数据错误
- 数据格式验证
- 缺失数据处理
- 异常数据跳过机制

## 性能优化

### 1. 并发控制
- 限制同时处理的任务数量
- 避免API频率限制
- 资源合理分配

### 2. 缓存机制
- 访问令牌缓存
- 已上传图片缓存
- 工作流配置缓存

### 3. 资源管理
- 及时清理临时文件
- 连接池复用
- 内存使用优化

## 扩展性设计

### 1. 模块化设计
- 各模块职责清晰
- 接口标准化
- 易于单独测试和维护

### 2. 配置化
- 关键参数可配置
- 支持不同环境配置
- 工作流可定制

### 3. 插件化
- 支持自定义处理器
- 可扩展的客户端接口
- 灵活的数据模型

## 安全考虑

### 1. 敏感信息保护
- 环境变量存储密钥
- 日志中不记录敏感信息
- 安全的文件权限设置

### 2. 输入验证
- URL格式验证
- 文件类型检查
- 数据范围验证

### 3. 错误信息
- 避免泄露系统内部信息
- 用户友好的错误提示
- 详细的内部日志记录

## 维护指南

### 1. 日常维护
- 定期清理日志文件
- 监控API使用量
- 检查错误报告

### 2. 版本更新
- 依赖包更新
- API版本兼容性检查
- 配置文件迁移

### 3. 故障排查
- 查看日志文件
- 检查网络连接
- 验证API密钥
- 测试各模块功能