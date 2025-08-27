# 飞书表格数据处理ComfyUI工作流

这是一个Python工具包，用于从飞书表格获取数据，处理图片，并通过ComfyUI执行AI工作流，最终将生成的图片写回飞书表格。该项目提供了完整的自动化图像处理解决方案。

## 📚 文档目录

- [项目结构说明](docs/project_structure.md) - 详细的项目文件组织和模块功能说明
- [飞书API使用说明](docs/feishu_api.md) - 飞书开放平台API的使用方法和示例
- [ComfyUI API使用说明](docs/comfyui_api.md) - ComfyUI工作流API的使用方法和配置
- [工作流程说明](docs/workflow_guide.md) - 完整的处理流程和操作指南

## 功能特性

- 🔐 飞书API认证和表格数据获取
- 📊 智能解析表格数据和嵌入式图片
- 🖼️ 自动下载和处理图片文件
- 🤖 ComfyUI工作流执行和状态监控
- 📝 详细的日志记录和错误处理
- 🔄 失败重试机制
- 📋 处理结果报告生成

## 系统要求

- Python 3.8+
- 网络连接（访问飞书API和ComfyUI服务）

## 安装步骤

### 1. 克隆或下载代码

```bash
git clone <repository_url>
cd toolKit
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量模板文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置信息：

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
```

## 配置说明

### 飞书配置

1. **获取飞书应用凭证**：
   - 访问 [飞书开放平台](https://open.feishu.cn/)
   - 创建应用并获取 App ID 和 App Secret
   - 确保应用有表格读写权限

2. **表格配置**：
   - `FEISHU_SPREADSHEET_TOKEN`：表格的唯一标识符
   - `FEISHU_SHEET_NAME`：工作表名称
   - `FEISHU_RANGE`：数据范围，如 "A1:Z1000"

3. **列映射配置**：
   - `FEISHU_PRODUCT_IMAGE_COLUMN`：产品图片列名
   - `FEISHU_MODEL_IMAGE_COLUMN`：模特图片列名
   - `FEISHU_PROMPT_COLUMN`：提示词列名
   - `FEISHU_STATUS_COLUMN`：状态列名

### ComfyUI配置

1. **API配置**：
   - `COMFYUI_API_KEY`：ComfyUI API密钥
   - `COMFYUI_WORKFLOW_ID`：工作流ID
   - `COMFYUI_BASE_URL`：API基础URL

2. **节点ID配置**：
   - 根据你的ComfyUI工作流配置相应的节点ID

## 📁 项目结构

```
toolKit/
├── docs/                    # 📚 文档目录
│   ├── feishu_api.md       # 飞书API使用说明
│   ├── comfyui_api.md      # ComfyUI API使用说明
│   ├── project_structure.md # 项目结构说明
│   └── workflow_guide.md   # 工作流程说明
├── test/                   # 🧪 测试文件目录
│   ├── test_api.py         # API接口测试
│   ├── test_full_workflow.py # 完整工作流测试
│   └── test_*.py           # 其他测试文件
├── output/                 # 📁 生成图片输出目录
├── logs/                   # 📋 日志文件目录
├── reports/                # 📊 处理报告目录
├── main.py                 # 🚀 主程序入口
├── config.py               # ⚙️ 配置管理
├── feishu_client.py        # 📊 飞书API客户端
├── comfyui_client.py       # 🤖 ComfyUI API客户端
├── workflow_processor.py   # 🔄 工作流处理器
└── requirements.txt        # 📦 依赖包列表
```

## 🧪 测试

项目提供了完整的测试套件，位于 `test/` 目录：

```bash
# 测试API连接
python test/test_api.py

# 测试完整工作流
python test/test_full_workflow.py

# 测试图片写入功能
python test/test_image_write.py

# 快速调试模式测试
python test_debug_mode.py
```

### 🐛 调试模式

调试模式是专为开发和测试设计的特殊运行模式，可以显著加快测试速度：

#### 功能特点

- **跳过ComfyUI API调用**：使用模拟数据代替实际的AI处理
- **快速执行**：整个工作流在几十秒内完成，而非数小时
- **完整流程测试**：保留所有业务逻辑，只跳过耗时的API调用
- **模拟结果生成**：创建模拟的输出文件和报告

#### 使用场景

- **功能开发**：快速验证新功能的逻辑正确性
- **代码调试**：定位和修复业务逻辑问题
- **集成测试**：验证各模块间的协作
- **性能测试**：测试除AI处理外的系统性能

#### 使用方法

```bash
# 启动调试模式，选择工作流类型
python main.py --debug

# 运行自动化测试脚本
python test_debug_mode.py
```

#### 调试模式 vs 正常模式

| 特性 | 正常模式 | 调试模式 |
|------|----------|----------|
| ComfyUI API调用 | ✅ 实际调用 | ❌ 跳过（模拟） |
| 执行时间 | 数小时 | 几十秒 |
| 业务逻辑 | ✅ 完整执行 | ✅ 完整执行 |
| 文件操作 | ✅ 真实文件 | ✅ 模拟文件 |
| 报告生成 | ✅ 真实数据 | ✅ 模拟数据 |
| 适用场景 | 生产环境 | 开发测试 |

## 使用方法

### 基本使用

```bash
# 处理所有未处理的数据
python main.py

# 重试失败的数据
python main.py --retry

# 设置最大重试次数
python main.py --retry --max-retries 5

# 干运行模式（只检查数据，不实际执行）
python main.py --dry-run

# 调试模式（跳过ComfyUI API调用，快速测试）
python main.py --debug

# 设置日志级别
python main.py --log-level DEBUG
```

### 命令行参数

- `--retry`：重试失败的行
- `--max-retries N`：设置最大重试次数（默认3次）
- `--dry-run`：干运行模式，只检查数据完整性
- `--debug`：调试模式，跳过ComfyUI API调用，使用模拟数据快速测试
- `--log-level LEVEL`：设置日志级别（DEBUG/INFO/WARNING/ERROR）

## 数据格式要求

### 飞书表格格式

表格应包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| product_image | 图片/URL | 产品图片（嵌入式图片或URL） |
| model_image | 图片/URL | 模特图片（嵌入式图片或URL） |
| prompt | 文本 | AI生成提示词 |
| is_read | 文本 | 处理状态（空=未处理，其他=已处理） |

### 图片格式支持

- **嵌入式图片**：飞书表格中直接插入的图片
- **URL链接**：指向图片文件的HTTP/HTTPS链接
- **支持格式**：PNG, JPG, JPEG, GIF, BMP

## 输出文件

### 目录结构

```
.
├── temp/           # 临时文件目录
├── output/          # 输出文件目录
├── logs/            # 日志文件目录
└── reports/         # 处理报告目录
```

### 日志文件

- 位置：`logs/workflow_YYYYMMDD_HHMMSS.log`
- 包含详细的执行过程和错误信息

### 处理报告

- 位置：`reports/report_YYYYMMDD_HHMMSS.txt`
- 包含处理结果统计和详细信息

## 错误处理

### 常见错误及解决方案

1. **飞书API认证失败**
   - 检查 App ID 和 App Secret 是否正确
   - 确认应用权限配置

2. **表格访问失败**
   - 检查表格Token是否正确
   - 确认应用有表格访问权限

3. **ComfyUI API调用失败**
   - 检查API密钥和工作流ID
   - 确认网络连接正常

4. **图片下载失败**
   - 检查图片URL是否有效
   - 确认网络连接稳定

### 重试机制

- 自动重试网络请求失败
- 支持手动重试失败的数据行
- 可配置重试次数和延迟时间

## 性能优化

### 配置建议

- `REQUEST_TIMEOUT`：根据网络情况调整请求超时时间
- `RETRY_DELAY`：设置合适的重试延迟避免API限制
- `COMFYUI_POLL_INTERVAL`：调整ComfyUI状态检查间隔

### 批处理

- 脚本支持处理大量数据
- 自动管理临时文件和内存使用
- 支持断点续传（跳过已处理的数据）

## 开发说明

### 项目结构

```
.
├── main.py                 # 主程序入口
├── config.py               # 配置管理
├── feishu_client.py        # 飞书API客户端
├── comfyui_client.py       # ComfyUI API客户端
├── workflow_processor.py   # 工作流处理器
├── requirements.txt        # 依赖包列表
├── .env.example           # 环境变量模板
└── README.md              # 说明文档
```

### 扩展开发

- 所有模块都采用异步设计，支持高并发处理
- 使用类型提示，便于IDE支持和代码维护
- 模块化设计，便于功能扩展和测试

## 许可证

本项目采用 MIT 许可证。

## 支持

如有问题或建议，请提交 Issue 或联系开发团队。