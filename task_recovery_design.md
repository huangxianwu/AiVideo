# 工作流任务恢复功能设计方案

## 1. 需求分析

### 1.1 核心需求
- **任务记录**：每行数据在图片合成或图生视频工作流执行时，记录到JSON数据表中
- **任务恢复**：main.py启动时，在执行任何工作流前，检查未完成任务并恢复执行
- **状态同步**：恢复的任务需要调用API获取文件，并按现有逻辑更新状态

### 1.2 数据记录要求
- 编号（row_number）
- 产品名（product_name）
- 模特名（model_name）
- 工作流类型（图片合成/图生视频）
- 工作流任务ID（task_id）
- 任务状态（在处理中/已完成/失败）

## 2. 现有基础设施分析

### 2.1 已有组件
- ✅ `WorkflowDatabase` - 基于JSON的数据存储
- ✅ `DatabaseManager` - 数据库管理器
- ✅ `WorkflowStatus` - 状态枚举
- ✅ `get_incomplete_tasks()` - 获取未完成任务

### 2.2 需要扩展的功能
- 🔄 增强任务记录字段（模特名等）
- 🔄 任务恢复逻辑
- 🔄 API文件获取和状态同步

## 3. 设计方案

### 3.1 数据模型扩展

#### 3.1.1 任务记录结构
```json
{
  "task_id": "img_20240101_001",
  "row_number": 67,
  "product_name": "产品A",
  "model_name": "模特B", 
  "workflow_type": "图片合成", // 或 "图生视频"
  "status": "在处理中", // "已完成", "失败"
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:05:00",
  "comfyui_task_id": "abc123", // ComfyUI返回的任务ID
  "output_files": [], // 生成的文件路径
  "error_message": null,
  "metadata": {
    "feishu_row_data": {}, // 原始飞书行数据
    "processing_start_time": "2024-01-01T10:00:00"
  }
}
```

#### 3.1.2 工作流类型枚举
```python
class WorkflowType(Enum):
    IMAGE_COMPOSITION = "图片合成"
    IMAGE_TO_VIDEO = "图生视频"
```

### 3.2 核心组件设计

#### 3.2.1 任务恢复管理器 (TaskRecoveryManager)
```python
class TaskRecoveryManager:
    """任务恢复管理器"""
    
    def __init__(self, db_manager: DatabaseManager, comfyui_client: ComfyUIClient):
        self.db_manager = db_manager
        self.comfyui_client = comfyui_client
    
    async def check_and_recover_tasks(self) -> List[Dict]:
        """检查并恢复未完成任务"""
        
    async def recover_image_composition_task(self, task_data: Dict) -> bool:
        """恢复图片合成任务"""
        
    async def recover_image_to_video_task(self, task_data: Dict) -> bool:
        """恢复图生视频任务"""
```

#### 3.2.2 增强的DatabaseManager
```python
class DatabaseManager:
    def add_workflow_task(self, row_data: RowData, workflow_type: WorkflowType, 
                         comfyui_task_id: str) -> str:
        """添加工作流任务记录"""
        
    def update_task_with_files(self, task_id: str, output_files: List[str]) -> bool:
        """更新任务文件信息"""
        
    def get_incomplete_tasks_by_type(self, workflow_type: WorkflowType) -> List[Dict]:
        """按类型获取未完成任务"""
```

### 3.3 工作流集成点

#### 3.3.1 图片合成工作流集成
```python
class ImageCompositionWorkflow(BaseWorkflow):
    async def process_row(self, row_data: RowData) -> WorkflowResult:
        # 1. 记录任务开始
        task_id = self.db_manager.add_workflow_task(
            row_data, WorkflowType.IMAGE_COMPOSITION, None
        )
        
        try:
            # 2. 提交ComfyUI任务
            comfyui_result = await self.comfyui_client.submit_workflow(...)
            
            # 3. 更新ComfyUI任务ID
            self.db_manager.update_task_comfyui_id(task_id, comfyui_result.task_id)
            
            # 4. 等待完成并获取结果
            result = await self.comfyui_client.wait_for_completion(comfyui_result.task_id)
            
            # 5. 保存文件并更新状态
            output_files = await self._save_result_files(row_data, result)
            self.db_manager.complete_task(task_id, output_files)
            
            # 6. 更新飞书表格
            await self._update_table_status(row_data, output_files)
            
        except Exception as e:
            # 7. 记录失败
            self.db_manager.mark_task_failed(task_id, str(e))
            raise
```

#### 3.3.2 图生视频工作流集成
```python
class ImageToVideoWorkflow(BaseWorkflow):
    async def process_row(self, row_data: RowData) -> WorkflowResult:
        # 类似的集成逻辑
        # ...
```

### 3.4 主程序启动流程

#### 3.4.1 修改main.py启动逻辑
```python
async def main_process(args, workflow_mode):
    # 1. 加载配置和初始化
    config = load_config()
    logger = setup_logging(config)
    
    # 2. 初始化组件
    workflow_manager = WorkflowManager(config, debug_mode=args.debug)
    recovery_manager = TaskRecoveryManager(
        workflow_manager.db_manager, 
        workflow_manager.comfyui_client
    )
    
    # 3. *** 新增：任务恢复检查 ***
    logger.info("🔍 检查未完成任务...")
    recovered_tasks = await recovery_manager.check_and_recover_tasks()
    if recovered_tasks:
        logger.info(f"✅ 恢复了 {len(recovered_tasks)} 个未完成任务")
    
    # 4. 继续正常工作流处理
    # ...
```

### 3.5 任务恢复逻辑详细设计

#### 3.5.1 恢复流程
1. **检测未完成任务**
   - 查询状态为"在处理中"的任务
   - 按工作流类型分组

2. **验证任务状态**
   - 调用ComfyUI API检查任务实际状态
   - 如果已完成，获取结果文件
   - 如果失败，标记为失败状态
   - 如果仍在处理，继续等待

3. **文件处理和状态同步**
   - **图片合成任务**：下载图片 → 更新飞书表格 → 标记完成
   - **图生视频任务**：下载视频 → 保存到文件夹 → 更新飞书状态 → 标记完成

#### 3.5.2 错误处理
- ComfyUI API不可用：记录错误，跳过恢复
- 文件下载失败：重试机制
- 飞书更新失败：记录错误但不影响任务完成状态

## 4. 实现计划

### 4.1 第一阶段：数据模型扩展
- [ ] 扩展WorkflowDatabase支持新字段
- [ ] 添加WorkflowType枚举
- [ ] 增强DatabaseManager方法

### 4.2 第二阶段：任务恢复核心
- [ ] 实现TaskRecoveryManager
- [ ] 实现ComfyUI任务状态检查
- [ ] 实现文件下载和状态同步逻辑

### 4.3 第三阶段：工作流集成
- [ ] 修改ImageCompositionWorkflow
- [ ] 修改ImageToVideoWorkflow
- [ ] 集成任务记录逻辑

### 4.4 第四阶段：主程序集成
- [ ] 修改main.py启动流程
- [ ] 添加恢复检查逻辑
- [ ] 测试完整流程

## 5. 测试策略

### 5.1 单元测试
- TaskRecoveryManager各方法
- DatabaseManager新增方法
- 工作流任务记录逻辑

### 5.2 集成测试
- 模拟中断场景
- 验证恢复逻辑
- 端到端流程测试

### 5.3 边界情况测试
- ComfyUI服务不可用
- 网络中断恢复
- 数据库文件损坏

## 6. 风险评估

### 6.1 技术风险
- **中等风险**：ComfyUI API状态查询可能不稳定
- **低风险**：JSON数据库文件并发访问

### 6.2 业务风险
- **低风险**：恢复逻辑可能导致重复处理
- **缓解措施**：任务ID唯一性检查

## 7. 性能考虑

- 启动时恢复检查应该是异步的，不阻塞正常流程
- 大量未完成任务时，分批处理避免内存压力
- 添加恢复进度显示，提升用户体验

---

**总结**：该设计方案基于现有的数据库基础设施，通过最小化的代码修改实现任务恢复功能。核心思路是在工作流执行的关键节点记录状态，并在程序启动时检查和恢复未完成的任务。