# 工作流程说明

## 概述
本文档详细描述了图像处理工作流的完整流程，包括数据处理步骤、操作指南和故障排查，供AI IDE开发过程参考。

## 整体流程图

```
开始
  ↓
读取飞书表格数据 (A2:H1000)
  ↓
遍历每一行数据
  ↓
检查状态列 (D列) 是否为空
  ↓ (为空则处理)
下载产品图片 (A列URL)
  ↓
下载模特图片 (B列URL)
  ↓
上传图片到ComfyUI
  ↓
执行图像合成工作流
  ↓
等待工作流完成
  ↓
下载生成的图片
  ↓
保存到本地output目录
  ↓
上传图片到飞书云空间
  ↓
将图片写入表格E列
  ↓
更新状态列为"已完成"
  ↓
处理下一行数据
  ↓
生成处理报告
  ↓
结束
```

## 详细流程说明

### 1. 初始化阶段

#### 1.1 环境检查
- 验证环境变量配置
- 检查必要的目录结构
- 初始化日志系统

#### 1.2 客户端初始化
```python
# 初始化飞书客户端
feishu_client = FeishuClient()

# 初始化ComfyUI客户端
comfyui_client = ComfyUIClient()

# 初始化工作流处理器
processor = WorkflowProcessor(feishu_client, comfyui_client)
```

#### 1.3 工作流配置加载
- 读取 `My workflow python.json` 文件
- 验证工作流配置的完整性
- 准备节点参数模板

### 2. 数据读取阶段

#### 2.1 获取访问令牌
```python
access_token = feishu_client.get_tenant_access_token()
```

#### 2.2 读取表格数据
```python
data = feishu_client.read_spreadsheet_data(
    spreadsheet_token=SPREADSHEET_TOKEN,
    range="A2:H1000"
)
```

#### 2.3 数据解析和验证
- 解析每行数据为RowData对象
- 验证必要字段的完整性
- 过滤已处理的数据行

### 3. 图像处理阶段

#### 3.1 单行数据处理流程

**步骤1：状态检查**
```python
if row_data.status:  # D列不为空
    logger.info(f"跳过已处理的行 {row_index}")
    continue
```

**步骤2：图片下载**
```python
# 下载产品图片
product_image_path = processor.download_image(
    url=row_data.product_image_url,
    filename=f"product_{row_index}.png"
)

# 下载模特图片
model_image_path = processor.download_image(
    url=row_data.model_image_url,
    filename=f"model_{row_index}.png"
)
```

**步骤3：图片上传到ComfyUI**
```python
product_filename = comfyui_client.upload_image(product_image_path)
model_filename = comfyui_client.upload_image(model_image_path)
```

**步骤4：工作流执行**
```python
# 更新工作流配置
workflow_data = processor.update_workflow_config(
    product_filename=product_filename,
    model_filename=model_filename
)

# 执行工作流
result = comfyui_client.execute_workflow(workflow_data)
```

**步骤5：等待完成**
```python
final_result = comfyui_client.wait_for_completion(
    task_id=result.task_id,
    timeout=300
)
```

**步骤6：结果处理**
```python
if final_result.status == 'SUCCESS':
    # 下载输出图片
    output_filename = processor.generate_filename(
        product_name=row_data.product_name
    )
    
    success = comfyui_client.download_output(
        url=final_result.output_urls[-1],
        save_path=f"./output/{output_filename}"
    )
```

#### 3.2 结果写入飞书

**步骤1：上传到飞书云空间**
```python
file_token = feishu_client.upload_image_to_feishu(
    image_path=f"./output/{output_filename}"
)
```

**步骤2：写入表格E列**
```python
feishu_client.write_image_to_cell(
    spreadsheet_token=SPREADSHEET_TOKEN,
    cell_range=f"E{row_index}:E{row_index}",
    file_token=file_token
)
```

**步骤3：更新状态**
```python
feishu_client.update_cell_status(
    spreadsheet_token=SPREADSHEET_TOKEN,
    cell_range=f"D{row_index}:D{row_index}",
    status="已完成"
)
```

### 4. 错误处理和重试机制

#### 4.1 网络错误处理
```python
def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

#### 4.2 API错误处理
- **飞书API错误**：检查令牌有效性，重新获取访问令牌
- **ComfyUI API错误**：检查服务状态，重试或跳过当前任务
- **文件操作错误**：检查文件权限和磁盘空间

#### 4.3 数据错误处理
- **URL无效**：记录错误并跳过当前行
- **图片格式不支持**：尝试格式转换或跳过
- **工作流执行失败**：记录详细错误信息

### 5. 并发控制

#### 5.1 任务队列管理
```python
class TaskManager:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.running_tasks = []
        self.pending_tasks = []
    
    def submit_task(self, task):
        if len(self.running_tasks) < self.max_concurrent:
            self.running_tasks.append(task)
            task.start()
        else:
            self.pending_tasks.append(task)
```

#### 5.2 资源限制
- 最大并发任务数：3个
- 单个任务超时时间：300秒
- API请求频率限制：每秒不超过10次

### 6. 日志记录

#### 6.1 日志级别
- **DEBUG**：详细的调试信息
- **INFO**：一般信息，如处理进度
- **WARNING**：警告信息，如重试操作
- **ERROR**：错误信息，如API调用失败
- **CRITICAL**：严重错误，如系统崩溃

#### 6.2 日志格式
```
2025-08-26 15:30:45,123 - INFO - 开始处理第3行数据
2025-08-26 15:30:46,456 - DEBUG - 下载产品图片: https://example.com/product.jpg
2025-08-26 15:30:47,789 - INFO - 图片上传成功: product_3.png
2025-08-26 15:30:48,012 - WARNING - 工作流执行中，等待完成...
2025-08-26 15:31:15,345 - INFO - 工作流执行成功，开始下载结果
2025-08-26 15:31:16,678 - INFO - 第3行处理完成
```

### 7. 性能监控

#### 7.1 关键指标
- **处理速度**：每分钟处理的行数
- **成功率**：成功处理的行数占比
- **平均处理时间**：单行数据的平均处理时间
- **API响应时间**：各API接口的平均响应时间

#### 7.2 性能优化建议
- 合理设置并发数量
- 使用连接池复用连接
- 实现智能重试策略
- 定期清理临时文件

### 8. 故障排查指南

#### 8.1 常见问题

**问题1：飞书API调用失败**
- 检查APP_ID和APP_SECRET是否正确
- 验证应用权限配置
- 检查网络连接

**问题2：ComfyUI工作流执行失败**
- 检查ComfyUI服务状态
- 验证工作流配置文件
- 检查上传的图片格式

**问题3：图片下载失败**
- 验证图片URL的有效性
- 检查网络连接和防火墙设置
- 确认图片服务器的访问权限

#### 8.2 调试步骤

1. **查看日志文件**
   ```bash
   tail -f logs/workflow_YYYYMMDD_HHMMSS.log
   ```

2. **检查配置文件**
   ```bash
   cat .env
   ```

3. **测试API连接**
   ```bash
   python test/test_api.py
   ```

4. **验证工作流配置**
   ```bash
   python test/test_full_workflow.py
   ```

### 9. 运行指南

#### 9.1 环境准备
1. 安装Python依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入正确的配置
   ```

3. 创建必要目录
   ```bash
   mkdir -p output temp logs reports
   ```

#### 9.2 启动程序
```bash
python main.py
```

#### 9.3 监控运行状态
- 查看实时日志
- 检查output目录的文件生成
- 监控飞书表格的更新状态

### 10. 维护和更新

#### 10.1 定期维护
- 清理过期的日志文件
- 清理临时文件目录
- 检查磁盘空间使用情况
- 更新依赖包版本

#### 10.2 配置更新
- 工作流配置的版本管理
- API密钥的定期更换
- 性能参数的调优

#### 10.3 功能扩展
- 支持更多图片格式
- 增加批量处理模式
- 实现Web界面管理
- 添加邮件通知功能

## 总结

本工作流程实现了从飞书表格读取数据，通过ComfyUI进行图像处理，再将结果写回飞书表格的完整自动化流程。通过合理的错误处理、并发控制和日志记录，确保了系统的稳定性和可维护性。

关键成功因素：
1. **模块化设计**：各组件职责清晰，易于维护
2. **错误处理**：完善的异常处理和重试机制
3. **日志记录**：详细的日志便于问题排查
4. **配置管理**：灵活的配置支持不同环境
5. **性能优化**：合理的并发控制和资源管理