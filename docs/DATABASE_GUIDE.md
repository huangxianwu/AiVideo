# 数据库功能使用指南

## 概述

本项目集成了基于JSON文件的轻量级数据库系统，用于记录和跟踪工作流执行状态。该系统支持工作流状态管理、任务恢复、统计分析等功能。

## 文件结构

```
data/
├── __init__.py                 # 数据包初始化文件
├── workflow_database.py        # 核心数据库类
├── database_manager.py         # 数据库管理器
└── workflow_db.json           # JSON数据库文件（自动创建）
```

## 核心组件

### 1. WorkflowStatus 枚举

定义了工作流的所有可能状态：

```python
from data import WorkflowStatus

# 可用状态
WorkflowStatus.PENDING           # 等待中
WorkflowStatus.IMAGE_GENERATING  # 图片生成中
WorkflowStatus.VIDEO_GENERATING  # 视频生成中
WorkflowStatus.COMPLETED         # 已完成
WorkflowStatus.FAILED           # 失败
```

### 2. DatabaseManager 类

提供高级数据库操作接口：

```python
from data import DatabaseManager

# 初始化数据库管理器
db_manager = DatabaseManager()
```

## 主要功能

### 任务管理

#### 开始图片生成
```python
# 开始图片生成任务
task_id = db_manager.generate_task_id(row_index=1, product_name="产品名称")
metadata = {
    'prompt': '生成图片的提示词',
    'workflow_type': 'image_composition'
}
success = db_manager.start_image_generation(task_id, 1, "产品名称", metadata)
```

#### 完成图片生成
```python
# 完成图片生成，准备视频生成
image_path = "./output/0828/img/product_image.png"
db_manager.complete_image_generation(task_id, image_path)
```

#### 开始视频生成
```python
# 开始视频生成
db_manager.start_video_generation(task_id)
```

#### 完成视频生成
```python
# 完成视频生成
video_path = "./output/0828/video/product_video.mp4"
db_manager.complete_video_generation(task_id, video_path)
```

#### 标记任务失败
```python
# 标记任务失败
error_message = "ComfyUI连接失败"
db_manager.mark_task_failed(task_id, error_message)
```

### 任务查询

#### 根据状态查询任务
```python
# 获取不同状态的任务
pending_tasks = db_manager.get_pending_tasks()
image_generating_tasks = db_manager.get_image_generating_tasks()
video_generating_tasks = db_manager.get_video_generating_tasks()
completed_tasks = db_manager.get_completed_tasks()
failed_tasks = db_manager.get_failed_tasks()
```

#### 根据行索引查询任务
```python
# 根据表格行索引查询任务
task_info = db_manager.get_task_by_row_index(row_index=1)
if task_info:
    print(f"任务ID: {task_info['task_id']}")
    print(f"状态: {task_info['status']}")
    print(f"产品名称: {task_info['product_name']}")
```

#### 获取任务详细信息
```python
# 获取特定任务的详细信息
task_info = db_manager.get_task_info(task_id)
if task_info:
    print(f"创建时间: {task_info['created_at']}")
    print(f"更新时间: {task_info['updated_at']}")
    print(f"图片路径: {task_info['image_path']}")
    print(f"视频路径: {task_info['video_path']}")
```

### 统计分析

#### 获取仪表板统计
```python
# 获取统计信息
stats = db_manager.get_dashboard_stats()
print(f"总任务数: {stats['total_tasks']}")
print(f"已完成: {stats['completed']}")
print(f"完成率: {stats['completion_rate']}%")
print(f"进行中: {stats['in_progress']}")
print(f"失败: {stats['failed']}")
```

### 任务恢复

#### 获取需要恢复的任务
```python
# 程序中断后，获取需要恢复的任务
recovery_tasks = db_manager.get_recovery_tasks()
for task in recovery_tasks:
    print(f"需要恢复的任务: {task['task_id']}, 状态: {task['status']}")
```

### 数据维护

#### 清理旧任务
```python
# 清理7天前的已完成任务
cleaned_count = db_manager.cleanup_old_completed_tasks(days=7)
print(f"清理了 {cleaned_count} 个旧任务")
```

#### 导出任务数据
```python
# 导出任务到CSV文件
success = db_manager.export_tasks_to_csv("tasks_backup.csv")
if success:
    print("任务数据导出成功")
```

#### 备份数据库
```python
# 备份数据库
backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
success = db_manager.backup_database(backup_path)
if success:
    print(f"数据库备份成功: {backup_path}")
```

## 工作流集成

数据库功能已自动集成到工作流管理器中，无需手动调用。工作流执行时会自动：

1. **生成任务ID** - 基于行索引和产品名称
2. **记录任务开始** - 标记为相应的生成状态
3. **更新任务进度** - 从图片生成到视频生成
4. **记录完成状态** - 保存输出文件路径
5. **记录失败信息** - 保存错误信息用于调试

### 在工作流中的使用示例

```python
from workflow_manager import WorkflowManager, WorkflowMode
from config import AppConfig

# 初始化工作流管理器（已自动集成数据库）
config = AppConfig()
workflow_manager = WorkflowManager(config, debug_mode=True)

# 执行工作流（数据库操作自动进行）
results = await workflow_manager.process_with_workflow(
    WorkflowMode.IMAGE_COMPOSITION, 
    rows_data
)

# 检查结果中的任务ID
for result in results:
    if result.success:
        print(f"任务 {result.task_id} 完成")
    else:
        print(f"任务 {result.task_id} 失败: {result.error}")
```

## 数据库文件格式

数据库文件 `data/workflow_db.json` 的结构：

```json
{
  "workflows": {
    "task_1_产品名_20250828_173518": {
      "task_id": "task_1_产品名_20250828_173518",
      "status": "已完成",
      "created_at": "2025-08-28T17:35:18.555005",
      "updated_at": "2025-08-28T17:35:18.556702",
      "row_index": 1,
      "product_name": "产品名",
      "image_path": "./output/0828/img/product.png",
      "video_path": "./output/0828/video/product.mp4",
      "error_message": null,
      "metadata": {
        "prompt": "生成图片的提示词",
        "workflow_type": "image_composition"
      }
    }
  },
  "statistics": {
    "total_tasks": 1,
    "completed": 1,
    "image_generating": 0,
    "video_generating": 0,
    "failed": 0,
    "pending": 0
  },
  "metadata": {
    "created_at": "2025-08-28T17:35:18.554123",
    "last_updated": "2025-08-28T17:35:18.556702",
    "version": "1.0"
  }
}
```

## 最佳实践

### 1. 任务ID生成
- 使用 `generate_task_id()` 方法确保唯一性
- 包含行索引和产品名称便于识别
- 包含时间戳避免冲突

### 2. 错误处理
- 始终检查数据库操作的返回值
- 记录详细的错误信息便于调试
- 使用 `mark_task_failed()` 记录失败原因

### 3. 数据维护
- 定期清理旧的已完成任务
- 定期备份数据库文件
- 监控数据库文件大小

### 4. 性能优化
- 数据库操作使用线程锁确保安全
- 避免频繁的数据库读写操作
- 批量操作时考虑性能影响

## 故障排除

### 常见问题

1. **数据库文件损坏**
   - 检查JSON格式是否正确
   - 使用备份文件恢复
   - 删除损坏文件让系统重新创建

2. **任务状态不一致**
   - 检查工作流执行是否正常完成
   - 查看错误日志确定失败原因
   - 使用 `mark_task_failed()` 手动标记失败任务

3. **性能问题**
   - 清理旧任务减少数据库大小
   - 检查是否有死锁或长时间运行的操作
   - 考虑升级到更高性能的数据库系统

### 调试技巧

1. **查看数据库内容**
   ```python
   import json
   with open('data/workflow_db.json', 'r', encoding='utf-8') as f:
       data = json.load(f)
   print(json.dumps(data, indent=2, ensure_ascii=False))
   ```

2. **检查任务状态**
   ```python
   stats = db_manager.get_dashboard_stats()
   print(f"统计信息: {stats}")
   
   recovery_tasks = db_manager.get_recovery_tasks()
   print(f"需要恢复的任务: {len(recovery_tasks)}")
   ```

3. **手动修复任务状态**
   ```python
   # 如果需要手动修复任务状态
   task_id = "task_1_产品名_20250828_173518"
   db_manager.mark_task_failed(task_id, "手动标记为失败")
   ```

## 扩展功能

未来可以考虑的扩展功能：

1. **数据库迁移** - 支持从JSON迁移到SQLite或其他数据库
2. **任务优先级** - 支持任务优先级排序
3. **任务依赖** - 支持任务间的依赖关系
4. **实时监控** - 提供Web界面实时监控任务状态
5. **自动重试** - 失败任务的自动重试机制
6. **分布式支持** - 支持多实例并发执行

---

*最后更新: 2025-08-28*