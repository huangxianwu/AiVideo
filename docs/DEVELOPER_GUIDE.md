# 开发者指南

## 📋 目录

- [1. 开发环境搭建](#1-开发环境搭建)
- [2. 项目架构详解](#2-项目架构详解)
- [3. 代码规范](#3-代码规范)
- [4. 开发工作流](#4-开发工作流)
- [5. 测试指南](#5-测试指南)
- [6. 性能优化](#6-性能优化)
- [7. 安全最佳实践](#7-安全最佳实践)
- [8. 扩展开发](#8-扩展开发)

---

## 1. 开发环境搭建

### 1.1 系统要求

- **操作系统**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python**: 3.8 或更高版本
- **内存**: 最少 4GB，推荐 8GB+
- **磁盘空间**: 至少 5GB 可用空间
- **网络**: 稳定的互联网连接

### 1.2 开发工具推荐

#### IDE/编辑器
- **PyCharm Professional** - 功能最全面
- **Visual Studio Code** - 轻量级，插件丰富
- **Sublime Text** - 快速响应

#### 必装插件（VS Code）
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.pylint",
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json"
  ]
}
```

### 1.3 环境配置

#### 克隆项目
```bash
git clone <repository_url>
cd toolKit
```

#### 创建虚拟环境
```bash
# 使用 venv
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 或使用 conda
conda create -n toolkit python=3.9
conda activate toolkit
```

#### 安装开发依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

#### 开发依赖说明
```txt
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
isort>=5.10.0
mypy>=0.991
pre-commit>=2.20.0
sphinx>=5.0.0
sphinx-rtd-theme>=1.0.0
```

### 1.4 Git Hooks 配置

#### 安装 pre-commit
```bash
pre-commit install
```

#### 配置文件 (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

---

## 2. 项目架构详解

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask Backend │    │  External APIs  │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │◄──►│ • Route Handlers│◄──►│ • Feishu API    │
│ • Bootstrap UI  │    │ • Business Logic│    │ • ComfyUI API   │
│ • AJAX Requests │    │ • Data Processing│    │ • Image Services│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Data Storage   │
                       │                 │
                       │ • CSV Files     │
                       │ • Image Files   │
                       │ • Log Files     │
                       │ • Config Files  │
                       └─────────────────┘
```

### 2.2 模块设计

#### 核心模块层次
```python
toolKit/
├── 🏗️ 基础设施层 (Infrastructure)
│   ├── config.py              # 配置管理
│   ├── logging_config.py      # 日志配置
│   └── exceptions.py          # 自定义异常
│
├── 🔌 数据访问层 (Data Access)
│   ├── feishu_client.py       # 飞书API客户端
│   ├── comfyui_client.py      # ComfyUI API客户端
│   └── csv_processor.py       # CSV数据处理
│
├── 🎯 业务逻辑层 (Business Logic)
│   ├── product_manager.py     # 产品管理
│   ├── workflow_processor.py  # 工作流处理
│   └── png_processor.py       # 图像处理
│
├── 🌐 表现层 (Presentation)
│   ├── web_app.py            # Web应用
│   ├── templates/            # HTML模板
│   └── static/               # 静态资源
│
└── 🚀 应用层 (Application)
    └── main.py               # 主程序入口
```

#### 依赖关系图
```
Presentation Layer
       ↓
Business Logic Layer
       ↓
Data Access Layer
       ↓
Infrastructure Layer
```

### 2.3 设计模式应用

#### 单例模式 - 配置管理
```python
class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        # 加载配置逻辑
        pass
```

#### 工厂模式 - 客户端创建
```python
class ClientFactory:
    @staticmethod
    def create_feishu_client(config: Dict[str, Any]) -> FeishuClient:
        return FeishuClient(
            app_id=config['app_id'],
            app_secret=config['app_secret']
        )
    
    @staticmethod
    def create_comfyui_client(config: Dict[str, Any]) -> ComfyUIClient:
        return ComfyUIClient(
            base_url=config['base_url'],
            api_key=config.get('api_key')
        )
```

#### 策略模式 - 图像处理
```python
from abc import ABC, abstractmethod

class ImageProcessor(ABC):
    @abstractmethod
    def process(self, image_path: str) -> str:
        pass

class WhiteBackgroundRemover(ImageProcessor):
    def process(self, image_path: str) -> str:
        # 白底去除逻辑
        pass

class ImageResizer(ImageProcessor):
    def process(self, image_path: str) -> str:
        # 图像缩放逻辑
        pass

class ImageProcessorContext:
    def __init__(self, processor: ImageProcessor):
        self.processor = processor
    
    def execute(self, image_path: str) -> str:
        return self.processor.process(image_path)
```

#### 观察者模式 - 状态更新
```python
from typing import List, Protocol

class Observer(Protocol):
    def update(self, event: str, data: Any) -> None:
        ...

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self, event: str, data: Any) -> None:
        for observer in self._observers:
            observer.update(event, data)

class ProcessingStatusObserver:
    def update(self, event: str, data: Any) -> None:
        if event == 'processing_started':
            print(f"开始处理: {data['product_id']}")
        elif event == 'processing_completed':
            print(f"处理完成: {data['product_id']}")
```

---

## 3. 代码规范

### 3.1 Python 代码风格

#### PEP 8 规范
- 使用 4 个空格缩进
- 行长度限制为 88 字符（Black 默认）
- 导入语句按字母顺序排列
- 类名使用 PascalCase
- 函数和变量名使用 snake_case
- 常量使用 UPPER_CASE

#### 示例代码
```python
from typing import Dict, List, Optional, Any
import logging
import os
from datetime import datetime

from flask import Flask, request, jsonify
from requests import Session

# 常量定义
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
API_VERSION = "v1"

logger = logging.getLogger(__name__)


class ProductManager:
    """产品管理器
    
    负责产品数据的加载、处理和管理。
    
    Attributes:
        data_file: 数据文件路径
        products: 产品数据列表
    """
    
    def __init__(self, data_file: str) -> None:
        """初始化产品管理器
        
        Args:
            data_file: 数据文件路径
            
        Raises:
            FileNotFoundError: 当数据文件不存在时
        """
        self.data_file = data_file
        self.products: List[Dict[str, Any]] = []
        self._load_data()
    
    def _load_data(self) -> None:
        """加载产品数据（私有方法）"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")
        
        try:
            # 数据加载逻辑
            logger.info(f"成功加载 {len(self.products)} 个产品")
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            raise
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取产品
        
        Args:
            product_id: 产品ID
            
        Returns:
            产品数据字典，如果不存在则返回None
        """
        for product in self.products:
            if product.get('product_id') == product_id:
                return product
        return None
    
    def filter_products(
        self, 
        name_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """过滤产品
        
        Args:
            name_filter: 名称过滤条件
            status_filter: 状态过滤条件
            
        Returns:
            过滤后的产品列表
        """
        filtered = self.products
        
        if name_filter:
            filtered = [
                p for p in filtered 
                if name_filter.lower() in p.get('name', '').lower()
            ]
        
        if status_filter:
            filtered = [
                p for p in filtered 
                if p.get('status') == status_filter
            ]
        
        return filtered
```

### 3.2 类型注解

#### 基础类型注解
```python
from typing import (
    Dict, List, Optional, Union, Tuple, Set,
    Callable, Any, TypeVar, Generic, Protocol
)
from dataclasses import dataclass
from enum import Enum

# 基础类型
def process_data(data: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in data}

# 可选类型
def find_user(user_id: str) -> Optional[Dict[str, Any]]:
    # 可能返回用户数据或None
    pass

# 联合类型
def parse_value(value: Union[str, int, float]) -> str:
    return str(value)

# 回调函数
def process_async(
    data: List[str], 
    callback: Callable[[str], None]
) -> None:
    for item in data:
        callback(item)
```

#### 数据类定义
```python
@dataclass
class ProductInfo:
    """产品信息数据类"""
    product_id: str
    name: str
    image_url: str
    status: str = "pending"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
```

#### 枚举类型
```python
class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class APIEndpoint(Enum):
    """API端点枚举"""
    FEISHU_TOKEN = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    FEISHU_SHEETS = "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets"
    COMFYUI_UPLOAD = "/upload/image"
    COMFYUI_PROMPT = "/prompt"
```

### 3.3 文档字符串规范

#### Google 风格文档字符串
```python
def download_and_process_image(
    image_url: str, 
    output_dir: str,
    remove_background: bool = True
) -> ProcessingResult:
    """下载并处理图片
    
    从指定URL下载图片，并根据参数进行处理。
    
    Args:
        image_url: 图片URL地址
        output_dir: 输出目录路径
        remove_background: 是否去除背景，默认为True
        
    Returns:
        ProcessingResult: 包含处理结果的数据类
            - success: 是否成功
            - message: 处理消息
            - data: 处理后的数据（可选）
            - error_code: 错误代码（可选）
    
    Raises:
        ValueError: 当image_url为空时
        FileNotFoundError: 当output_dir不存在时
        ProcessingError: 当图片处理失败时
        
    Example:
        >>> result = download_and_process_image(
        ...     "https://example.com/image.jpg",
        ...     "/path/to/output",
        ...     remove_background=True
        ... )
        >>> if result.success:
        ...     print(f"处理成功: {result.message}")
        
    Note:
        此函数会自动创建输出目录（如果不存在）。
        处理后的图片将保存为PNG格式。
    """
    if not image_url:
        raise ValueError("图片URL不能为空")
    
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"输出目录不存在: {output_dir}")
    
    try:
        # 处理逻辑
        return ProcessingResult(
            success=True,
            message="处理完成",
            data={"output_path": "/path/to/processed/image.png"}
        )
    except Exception as e:
        logger.exception(f"图片处理失败: {e}")
        return ProcessingResult(
            success=False,
            message=f"处理失败: {str(e)}",
            error_code="PROCESSING_ERROR"
        )
```

### 3.4 错误处理规范

#### 异常层次结构
```python
class ToolKitError(Exception):
    """工具包基础异常类"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(ToolKitError):
    """配置错误"""
    pass

class APIError(ToolKitError):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.status_code = status_code

class ProcessingError(ToolKitError):
    """数据处理错误"""
    pass

class ValidationError(ToolKitError):
    """数据验证错误"""
    pass
```

#### 错误处理装饰器
```python
from functools import wraps
from typing import Callable, TypeVar, Any

F = TypeVar('F', bound=Callable[..., Any])

def handle_exceptions(default_return: Any = None) -> Callable[[F], F]:
    """异常处理装饰器
    
    Args:
        default_return: 异常时的默认返回值
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ToolKitError:
                # 重新抛出自定义异常
                raise
            except Exception as e:
                logger.exception(f"未预期的错误在 {func.__name__}: {e}")
                if default_return is not None:
                    return default_return
                raise ProcessingError(f"处理失败: {str(e)}") from e
        return wrapper
    return decorator

# 使用示例
@handle_exceptions(default_return=[])
def get_products() -> List[Dict[str, Any]]:
    # 可能抛出异常的代码
    pass
```

---

## 4. 开发工作流

### 4.1 Git 工作流

#### 分支策略
```
master/main     ←── 生产环境代码
    ↑
develop         ←── 开发环境代码
    ↑
feature/*       ←── 功能开发分支
hotfix/*        ←── 紧急修复分支
release/*       ←── 发布准备分支
```

#### 分支命名规范
```bash
# 功能开发
feature/user-authentication
feature/image-processing-optimization
feature/api-rate-limiting

# 错误修复
bugfix/fix-csv-import-encoding
bugfix/resolve-memory-leak

# 紧急修复
hotfix/security-patch-v2.1.1
hotfix/critical-api-fix

# 发布分支
release/v2.2.0
release/v2.1.1-hotfix
```

#### 提交消息规范
```bash
# 格式: <type>(<scope>): <description>

# 功能添加
feat(api): add PNG conversion status endpoint
feat(ui): implement real-time progress display

# 错误修复
fix(csv): resolve encoding issue with Chinese characters
fix(memory): fix memory leak in image processing

# 文档更新
docs(api): update API reference documentation
docs(readme): add installation instructions

# 代码重构
refactor(client): simplify Feishu API client structure
refactor(utils): extract common validation functions

# 性能优化
perf(image): optimize white background removal algorithm
perf(db): improve CSV data loading performance

# 测试相关
test(api): add unit tests for PNG conversion
test(integration): add end-to-end workflow tests

# 构建相关
build(deps): update Flask to version 2.3.0
build(docker): optimize Docker image size
```

### 4.2 开发流程

#### 1. 创建功能分支
```bash
# 从 develop 分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature-name
```

#### 2. 开发和测试
```bash
# 编写代码
# 运行测试
pytest tests/

# 代码格式化
black .
isort .

# 代码检查
flake8 .
mypy .

# 提交代码
git add .
git commit -m "feat(scope): add new feature description"
```

#### 3. 创建 Pull Request
```markdown
## Pull Request 模板

### 变更描述
简要描述此PR的变更内容。

### 变更类型
- [ ] 新功能 (feature)
- [ ] 错误修复 (bugfix)
- [ ] 性能优化 (performance)
- [ ] 代码重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 测试相关 (test)

### 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

### 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 没有引入破坏性变更

### 相关Issue
Closes #123
```

#### 4. 代码审查
```markdown
## 代码审查检查点

### 功能性
- [ ] 功能是否按预期工作
- [ ] 边界条件是否处理正确
- [ ] 错误处理是否完善

### 代码质量
- [ ] 代码是否清晰易读
- [ ] 是否遵循项目规范
- [ ] 是否有重复代码

### 性能
- [ ] 是否有性能问题
- [ ] 资源使用是否合理
- [ ] 是否有内存泄漏

### 安全性
- [ ] 是否有安全漏洞
- [ ] 输入验证是否充分
- [ ] 敏感信息是否泄露
```

### 4.3 发布流程

#### 版本号规范 (Semantic Versioning)
```
MAJOR.MINOR.PATCH

例如: 2.1.3
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能性新增
- PATCH: 向后兼容的问题修正
```

#### 发布步骤
```bash
# 1. 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v2.2.0

# 2. 更新版本号
# 更新 setup.py, __init__.py 等文件中的版本号

# 3. 更新 CHANGELOG.md
# 记录此版本的所有变更

# 4. 提交发布准备
git add .
git commit -m "chore(release): prepare for v2.2.0"

# 5. 合并到 master
git checkout master
git merge release/v2.2.0
git tag v2.2.0
git push origin master --tags

# 6. 合并回 develop
git checkout develop
git merge release/v2.2.0
git push origin develop

# 7. 删除发布分支
git branch -d release/v2.2.0
```

---

## 5. 测试指南

### 5.1 测试策略

#### 测试金字塔
```
        /\        E2E Tests (少量)
       /  \       - 完整工作流测试
      /____\      - UI自动化测试
     /      \     
    / Integration\    Integration Tests (适量)
   /    Tests    \   - API集成测试
  /______________\  - 数据库集成测试
 /                \ 
/   Unit Tests     \ Unit Tests (大量)
\   (Fast & Many)  / - 函数级别测试
 \________________/  - 类级别测试
```

### 5.2 单元测试

#### 测试文件结构
```
tests/
├── unit/
│   ├── test_product_manager.py
│   ├── test_feishu_client.py
│   ├── test_comfyui_client.py
│   └── test_image_processor.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_workflow_integration.py
│   └── test_database_operations.py
├── e2e/
│   ├── test_complete_workflow.py
│   └── test_ui_interactions.py
├── fixtures/
│   ├── sample_data.json
│   ├── test_images/
│   └── mock_responses.py
└── conftest.py
```

#### 单元测试示例
```python
# tests/unit/test_product_manager.py
import pytest
from unittest.mock import Mock, patch, mock_open
import pandas as pd

from src.product_manager import ProductManager
from src.exceptions import ValidationError


class TestProductManager:
    """ProductManager 单元测试"""
    
    @pytest.fixture
    def sample_data(self):
        """测试数据fixture"""
        return [
            {
                'product_id': '123',
                'product_name': '测试商品1',
                'image_url': 'https://example.com/image1.jpg'
            },
            {
                'product_id': '456',
                'product_name': '测试商品2',
                'image_url': 'https://example.com/image2.jpg'
            }
        ]
    
    @pytest.fixture
    def product_manager(self, sample_data):
        """ProductManager实例fixture"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_df = Mock()
            mock_df.to_dict.return_value = sample_data
            mock_read_csv.return_value = mock_df
            
            with patch('os.path.exists', return_value=True):
                return ProductManager('test.csv')
    
    def test_init_loads_data_successfully(self, product_manager, sample_data):
        """测试初始化时成功加载数据"""
        assert len(product_manager.data) == 2
        assert product_manager.data == sample_data
    
    def test_init_handles_missing_file(self):
        """测试处理文件不存在的情况"""
        with patch('os.path.exists', return_value=False):
            manager = ProductManager('nonexistent.csv')
            assert manager.data == []
    
    def test_get_paginated_data(self, product_manager):
        """测试分页数据获取"""
        result = product_manager.get_paginated_data(page=1, per_page=1)
        
        assert result['pagination']['page'] == 1
        assert result['pagination']['per_page'] == 1
        assert result['pagination']['total'] == 2
        assert result['pagination']['total_pages'] == 2
        assert len(result['data']) == 1
    
    def test_get_product_by_id_found(self, product_manager):
        """测试根据ID查找产品 - 找到"""
        product = product_manager.get_product_by_id('123')
        assert product is not None
        assert product['product_name'] == '测试商品1'
    
    def test_get_product_by_id_not_found(self, product_manager):
        """测试根据ID查找产品 - 未找到"""
        product = product_manager.get_product_by_id('999')
        assert product is None
    
    @patch('requests.get')
    def test_download_images_success(self, mock_get, product_manager):
        """测试图片下载成功"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                result = product_manager.download_images(['123'])
        
        assert result['success'] == True
        assert result['downloaded_count'] == 1
        assert result['failed_count'] == 0
    
    @patch('requests.get')
    def test_download_images_failure(self, mock_get, product_manager):
        """测试图片下载失败"""
        # 模拟HTTP错误
        mock_get.side_effect = Exception("Network error")
        
        result = product_manager.download_images(['123'])
        
        assert result['success'] == False
        assert result['downloaded_count'] == 0
        assert result['failed_count'] == 1
        assert len(result['failed_products']) == 1
```

#### 测试配置文件
```python
# tests/conftest.py
import pytest
import tempfile
import os
from unittest.mock import Mock

from src.config import Config
from src.feishu_client import FeishuClient
from src.comfyui_client import ComfyUIClient


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        'feishu': {
            'app_id': 'test_app_id',
            'app_secret': 'test_app_secret',
            'spreadsheet_token': 'test_token'
        },
        'comfyui': {
            'base_url': 'http://localhost:8188',
            'api_key': 'test_api_key'
        }
    }


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端"""
    client = Mock(spec=FeishuClient)
    client.get_tenant_access_token.return_value = 'mock_token'
    client.read_spreadsheet_data.return_value = {
        'values': [['id', 'name'], ['1', 'test']]
    }
    return client


@pytest.fixture
def mock_comfyui_client():
    """模拟ComfyUI客户端"""
    client = Mock(spec=ComfyUIClient)
    client.upload_image.return_value = {'name': 'uploaded_image.jpg'}
    client.execute_workflow.return_value = 'task_123'
    client.check_task_status.return_value = {
        'status': 'completed',
        'outputs': {'node_1': {'images': [{'filename': 'output.png'}]}}
    }
    return client


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境"""
    # 设置测试环境变量
    monkeypatch.setenv('TESTING', 'true')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    
    # 禁用网络请求
    monkeypatch.setattr('requests.get', Mock())
    monkeypatch.setattr('requests.post', Mock())
```

### 5.3 集成测试

#### API集成测试
```python
# tests/integration/test_api_endpoints.py
import pytest
import json
from flask import Flask

from src.web_app import app, product_manager


class TestAPIEndpoints:
    """API端点集成测试"""
    
    @pytest.fixture
    def client(self):
        """Flask测试客户端"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_products(self):
        """示例产品数据"""
        return [
            {
                'product_id': '123',
                'product_name': '测试商品',
                'image_url': 'https://example.com/image.jpg',
                'downloaded': False
            }
        ]
    
    def test_get_data_endpoint(self, client, sample_products):
        """测试获取数据端点"""
        # 模拟产品数据
        product_manager.data = sample_products
        
        response = client.get('/api/data?page=1&per_page=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert 'pagination' in data
        assert len(data['data']) == 1
    
    def test_download_endpoint_success(self, client, sample_products):
        """测试下载端点成功情况"""
        product_manager.data = sample_products
        
        with patch.object(product_manager, 'download_images') as mock_download:
            mock_download.return_value = {
                'success': True,
                'downloaded_count': 1,
                'failed_count': 0
            }
            
            response = client.post(
                '/api/download',
                data=json.dumps({'selected_ids': ['123']}),
                content_type='application/json'
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['downloaded_count'] == 1
    
    def test_download_endpoint_invalid_data(self, client):
        """测试下载端点无效数据"""
        response = client.post(
            '/api/download',
            data=json.dumps({'invalid_field': 'value'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_convert_to_png_endpoint(self, client, sample_products):
        """测试PNG转换端点"""
        product_manager.data = sample_products
        
        with patch('src.png_processor.WhiteBackgroundRemover') as mock_processor:
            with patch('src.feishu_client.FeishuClient') as mock_feishu:
                mock_processor.return_value.remove_white_background.return_value = True
                mock_feishu.return_value.upload_image_to_feishu.return_value = 'image_token'
                
                response = client.post(
                    '/api/convert_to_png',
                    data=json.dumps({'selected_ids': ['123']}),
                    content_type='application/json'
                )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'processing_results' in data
```

### 5.4 端到端测试

#### Selenium Web测试
```python
# tests/e2e/test_ui_interactions.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class TestUIInteractions:
    """UI交互端到端测试"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Selenium WebDriver fixture"""
        options = Options()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """设置测试数据"""
        # 准备测试数据
        pass
    
    def test_product_selection_workflow(self, driver):
        """测试产品选择工作流"""
        # 访问主页
        driver.get('http://localhost:8080')
        
        # 等待页面加载
        wait = WebDriverWait(driver, 10)
        products_table = wait.until(
            EC.presence_of_element_located((By.ID, 'products-container'))
        )
        
        # 选择第一个产品
        first_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        first_checkbox.click()
        
        # 检查选择计数器
        selected_count = driver.find_element(By.ID, 'selected-count')
        assert selected_count.text == '1'
        
        # 点击下载按钮
        download_btn = driver.find_element(By.ID, 'download-selected-btn')
        download_btn.click()
        
        # 等待下载完成提示
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        )
        assert '下载完成' in success_message.text
    
    def test_erp_system_navigation(self, driver):
        """测试ERP系统导航"""
        # 访问ERP页面
        driver.get('http://localhost:8080/erp')
        
        # 检查页面标题
        assert 'ERP系统' in driver.title
        
        # 测试菜单展开/收缩
        menu_toggle = driver.find_element(By.ID, 'menu-toggle')
        menu_toggle.click()
        
        # 检查菜单状态
        sidebar = driver.find_element(By.ID, 'sidebar')
        assert 'expanded' in sidebar.get_attribute('class')
        
        # 点击已选商品菜单
        selected_menu = driver.find_element(By.LINK_TEXT, '已选商品')
        selected_menu.click()
        
        # 检查页面跳转
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains('/erp/selected'))
        assert '/erp/selected' in driver.current_url
    
    def test_png_conversion_workflow(self, driver):
        """测试PNG转换工作流"""
        # 访问已选商品页面
        driver.get('http://localhost:8080/erp/selected')
        
        # 点击PNG转换按钮
        convert_btn = driver.find_element(By.ID, 'convert-to-png-btn')
        convert_btn.click()
        
        # 等待状态面板出现
        wait = WebDriverWait(driver, 10)
        status_panel = wait.until(
            EC.visibility_of_element_located((By.ID, 'conversionStatusPanel'))
        )
        
        # 检查进度显示
        progress_bar = driver.find_element(By.CLASS_NAME, 'progress-bar')
        assert progress_bar.is_displayed()
        
        # 等待处理完成
        wait.until(
            EC.text_to_be_present_in_element(
                (By.ID, 'overall-status'), '处理完成'
            )
        )
        
        # 检查成功消息
        success_items = driver.find_elements(By.CLASS_NAME, 'status-success')
        assert len(success_items) > 0
```

### 5.5 性能测试

#### 负载测试
```python
# tests/performance/test_load.py
import pytest
import time
import concurrent.futures
import requests
from statistics import mean, median


class TestPerformance:
    """性能测试"""
    
    BASE_URL = 'http://localhost:8080'
    
    def test_api_response_time(self):
        """测试API响应时间"""
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = requests.get(f'{self.BASE_URL}/api/data')
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = mean(response_times)
        median_time = median(response_times)
        
        # 断言平均响应时间小于1秒
        assert avg_time < 1.0, f"平均响应时间过长: {avg_time:.2f}s"
        assert median_time < 0.5, f"中位数响应时间过长: {median_time:.2f}s"
    
    def test_concurrent_requests(self):
        """测试并发请求"""
        def make_request():
            start_time = time.time()
            response = requests.get(f'{self.BASE_URL}/api/data')
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # 并发10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # 检查所有请求都成功
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        assert all(code == 200 for code in status_codes)
        assert max(response_times) < 2.0, "并发请求响应时间过长"
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 执行一些操作
        for _ in range(100):
            requests.get(f'{self.BASE_URL}/api/data')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过100MB
        assert memory_increase < 100 * 1024 * 1024, f"内存泄漏: {memory_increase / 1024 / 1024:.2f}MB"
```

---

## 6. 性能优化

### 6.1 代码层面优化

#### 数据处理优化
```python
# 优化前：逐行处理
def process_products_slow(products):
    results = []
    for product in products:
        if product['status'] == 'pending':
            processed = expensive_operation(product)
            results.append(processed)
    return results

# 优化后：批量处理 + 向量化操作
def process_products_fast(products):
    import pandas as pd
    
    # 转换为DataFrame进行向量化操作
    df = pd.DataFrame(products)
    
    # 使用布尔索引过滤
    pending_df = df[df['status'] == 'pending']
    
    # 批量处理
    if not pending_df.empty:
        processed_data = batch_expensive_operation(pending_df.to_dict('records'))
        return processed_data
    
    return []

def batch_expensive_operation(products_batch):
    """批量处理，减少函数调用开销"""
    # 批量处理逻辑
    pass
```

#### 缓存策略
```python
from functools import lru_cache
from typing import Dict, Any
import time
import threading

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str, default=None):
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                cache_item = self._cache[key]
                if time.time() < cache_item['expires_at']:
                    return cache_item['value']
                else:
                    del self._cache[key]
            return default
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

# 全局缓存实例
cache = CacheManager()

# 使用装饰器实现方法缓存
def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# 使用示例
@cached(ttl=600)  # 缓存10分钟
def get_feishu_data(spreadsheet_token: str, range_str: str):
    """获取飞书数据（带缓存）"""
    # 实际的API调用
    pass
```

#### 异步处理
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class AsyncImageProcessor:
    """异步图像处理器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def download_images_async(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """异步下载多个图片"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._download_single_image(session, url) 
                for url in image_urls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            result if not isinstance(result, Exception) else {'error': str(result)}
            for result in results
        ]
    
    async def _download_single_image(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """下载单个图片"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    return {
                        'url': url,
                        'content': content,
                        'size': len(content)
                    }
                else:
                    return {'url': url, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'url': url, 'error': str(e)}
    
    async def process_images_async(self, images_data: List[bytes]) -> List[bytes]:
        """异步处理多个图片"""
        loop = asyncio.get_event_loop()
        
        # 将CPU密集型任务提交到线程池
        tasks = [
            loop.run_in_executor(self.executor, self._process_single_image, image_data)
            for image_data in images_data
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    def _process_single_image(self, image_data: bytes) -> bytes:
        """处理单个图片（CPU密集型任务）"""
        # 图片处理逻辑
        # 这里会在线程池中执行，不会阻塞事件循环
        pass

# 使用示例
async def main():
    processor = AsyncImageProcessor()
    
    # 异步下载图片
    image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
    download_results = await processor.download_images_async(image_urls)
    
    # 提取图片数据
    images_data = [result['content'] for result in download_results if 'content' in result]
    
    # 异步处理图片
    processed_images = await processor.process_images_async(images_data)
    
    return processed_images

# 在Flask中使用异步处理
from flask import Flask, jsonify
import asyncio

app = Flask(__name__)

@app.route('/api/process_images_async', methods=['POST'])
def process_images_async_endpoint():
    # 获取请求数据
    image_urls = request.json.get('image_urls', [])
    
    # 在新的事件循环中运行异步任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        processor = AsyncImageProcessor()
        results = loop.run_until_complete(
            processor.download_images_async(image_urls)
        )
        return jsonify({'success': True, 'results': results})
    finally:
        loop.close()
```

### 6.2 数据库优化

#### CSV文件优化
```python
import pandas as pd
from typing import List, Dict, Any, Optional
import os

class OptimizedCSVManager:
    """优化的CSV管理器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._data_cache: Optional[pd.DataFrame] = None
        self._last_modified: Optional[float] = None
    
    def _should_reload(self) -> bool:
        """检查是否需要重新加载数据"""
        if not os.path.exists(self.file_path):
            return False
        
        current_modified = os.path.getmtime(self.file_path)
        return (self._last_modified is None or 
                current_modified > self._last_modified)
    
    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """加载数据（带缓存）"""
        if force_reload or self._should_reload():
            try:
                # 使用优化的读取参数
                self._data_cache = pd.read_csv(
                    self.file_path,
                    dtype={'product_id': 'string'},  # 指定数据类型
                    parse_dates=['created_at'],       # 解析日期
                    na_filter=False,                  # 不将空字符串转换为NaN
                    engine='c'                        # 使用C引擎提高性能
                )
                self._last_modified = os.path.getmtime(self.file_path)
            except Exception as e:
                logger.error(f"加载CSV文件失败: {e}")
                self._data_cache = pd.DataFrame()
        
        return self._data_cache.copy() if self._data_cache is not None else pd.DataFrame()
    
    def query_data(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """查询数据（优化版）"""
        df = self.load_data()
        
        if df.empty:
            return df
        
        # 应用过滤条件
        if filters:
            for column, value in filters.items():
                if column in df.columns:
                    if isinstance(value, list):
                        df = df[df[column].isin(value)]
                    else:
                        df = df[df[column] == value]
        
        # 选择指定列
        if columns:
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
        
        # 限制结果数量
        if limit:
            df = df.head(limit)
        
        return df
    
    def update_data(self, updates: List[Dict[str, Any]], key_column: str = 'product_id') -> bool:
        """批量更新数据"""
        try:
            df = self.load_data()
            
            for update in updates:
                key_value = update.get(key_column)
                if key_value:
                    mask = df[key_column] == key_value
                    for column, value in update.items():
                        if column in df.columns:
                            df.loc[mask, column] = value
            
            # 保存更新后的数据
            df.to_csv(self.file_path, index=False)
            self._last_modified = os.path.getmtime(self.file_path)
            return True
        except Exception as e:
             logger.error(f"更新数据失败: {e}")
             return False
```

#### 内存优化
```python
import gc
from memory_profiler import profile

class MemoryOptimizedProcessor:
    """内存优化处理器"""
    
    def __init__(self):
        self.chunk_size = 1000  # 分块处理大小
    
    def process_large_dataset(self, data_source: str) -> None:
        """分块处理大数据集"""
        # 使用chunksize参数分块读取
        chunk_iter = pd.read_csv(data_source, chunksize=self.chunk_size)
        
        for chunk_num, chunk in enumerate(chunk_iter):
            try:
                # 处理当前块
                processed_chunk = self._process_chunk(chunk)
                
                # 保存处理结果
                self._save_chunk_result(processed_chunk, chunk_num)
                
                # 显式删除变量并触发垃圾回收
                del chunk, processed_chunk
                gc.collect()
                
            except Exception as e:
                logger.error(f"处理第{chunk_num}块数据失败: {e}")
                continue
    
    def _process_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """处理数据块"""
        # 数据处理逻辑
        return chunk
    
    def _save_chunk_result(self, chunk: pd.DataFrame, chunk_num: int) -> None:
        """保存块处理结果"""
        output_file = f"processed_chunk_{chunk_num}.csv"
        chunk.to_csv(output_file, index=False)
    
    @profile  # 内存分析装饰器
    def memory_intensive_operation(self, data: List[Any]) -> List[Any]:
        """内存密集型操作（带内存分析）"""
        # 使用生成器减少内存占用
        def process_generator():
            for item in data:
                yield self._process_item(item)
        
        # 批量处理而不是一次性加载所有结果
        results = []
        batch_size = 100
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_results = list(self._process_item(item) for item in batch)
            results.extend(batch_results)
            
            # 定期清理内存
            if i % (batch_size * 10) == 0:
                gc.collect()
        
        return results
```

### 6.3 Web应用优化

#### Flask应用优化
```python
from flask import Flask, request, jsonify, g
from flask_caching import Cache
from flask_compress import Compress
from werkzeug.middleware.profiler import ProfilerMiddleware
import time

# 创建Flask应用
app = Flask(__name__)

# 配置缓存
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# 启用压缩
Compress(app)

# 性能分析中间件（仅开发环境）
if app.debug:
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# 请求计时中间件
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        response.headers['X-Response-Time'] = f'{duration:.3f}s'
    return response

# 缓存装饰器使用
@app.route('/api/data')
@cache.cached(timeout=300, query_string=True)  # 根据查询参数缓存
def get_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 数据获取逻辑
    data = product_manager.get_paginated_data(page, per_page)
    return jsonify(data)
```

---

## 7. 安全最佳实践

### 7.1 输入验证

#### 数据验证框架
```python
from marshmallow import Schema, fields, validate, ValidationError
from typing import Dict, Any

class ProductSchema(Schema):
    """产品数据验证模式"""
    product_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    product_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    image_url = fields.Url(required=True)
    status = fields.Str(validate=validate.OneOf(['pending', 'processing', 'completed', 'failed']))
    price = fields.Decimal(validate=validate.Range(min=0))

def validate_request_data(schema_class, data: Dict[str, Any]) -> Dict[str, Any]:
    """验证请求数据"""
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as e:
        raise ValueError(f"数据验证失败: {e.messages}")
```

### 7.2 身份认证和授权

#### JWT令牌认证
```python
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

class AuthManager:
    """认证管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=24)
    
    def generate_token(self, user_id: str, permissions: List[str] = None) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("令牌已过期")
        except jwt.InvalidTokenError:
            raise ValueError("无效令牌")
```

---

## 8. 扩展开发

### 8.1 插件系统

#### 插件架构
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import importlib
import os

class Plugin(ABC):
    """插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        pass

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = 'plugins'):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Plugin]] = {}
    
    def load_plugins(self) -> None:
        """加载所有插件"""
        if not os.path.exists(self.plugin_dir):
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                     self._load_plugin(module_name)
                 except Exception as e:
                     logger.error(f"加载插件 {module_name} 失败: {e}")
    
    def _load_plugin(self, module_name: str) -> None:
        """加载单个插件"""
        module_path = f"{self.plugin_dir}.{module_name}"
        module = importlib.import_module(module_path)
        
        # 查找插件类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Plugin) and 
                attr != Plugin):
                
                plugin_instance = attr()
                self.plugins[plugin_instance.name] = plugin_instance
                logger.info(f"已加载插件: {plugin_instance.name} v{plugin_instance.version}")
                break
    
    def register_hook(self, hook_name: str, plugin: Plugin) -> None:
        """注册插件钩子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(plugin)
    
    def execute_hook(self, hook_name: str, data: Any) -> Any:
        """执行钩子"""
        if hook_name not in self.hooks:
            return data
        
        result = data
        for plugin in self.hooks[hook_name]:
            try:
                result = plugin.process(result)
            except Exception as e:
                logger.error(f"插件 {plugin.name} 执行失败: {e}")
        
        return result
```

### 8.2 RESTful API扩展

#### API版本控制
```python
from flask import Blueprint, request, jsonify
from functools import wraps

class APIVersionManager:
    """API版本管理器"""
    
    def __init__(self):
        self.versions = {}
        self.default_version = 'v1'
    
    def register_version(self, version: str, blueprint: Blueprint) -> None:
        """注册API版本"""
        self.versions[version] = blueprint
    
    def get_version_from_request(self) -> str:
        """从请求中获取API版本"""
        # 从URL路径获取版本
        if request.path.startswith('/api/'):
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and path_parts[2].startswith('v'):
                return path_parts[2]
        
        # 从请求头获取版本
        version = request.headers.get('API-Version')
        if version:
            return version
        
        # 从查询参数获取版本
        version = request.args.get('version')
        if version:
            return version
        
        return self.default_version

def api_version(version: str):
    """API版本装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_version = api_version_manager.get_version_from_request()
            if request_version != version:
                return jsonify({
                    'error': 'API version mismatch',
                    'requested': request_version,
                    'supported': version
                }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 使用示例
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v1.route('/products')
@api_version('v1')
def get_products_v1():
    """获取产品列表 - v1版本"""
    return jsonify({'version': 'v1', 'products': []})

@api_v2.route('/products')
@api_version('v2')
def get_products_v2():
    """获取产品列表 - v2版本（增强功能）"""
    return jsonify({
        'version': 'v2', 
        'products': [],
        'metadata': {'total': 0, 'page': 1}
    })
```

### 8.3 数据库集成扩展

#### SQLAlchemy集成
```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()

class Product(Base):
    """产品模型"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    image_url = Column(Text)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'image_url': self.image_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """创建产品"""
        with self.get_session() as session:
            product = Product(**product_data)
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """获取产品"""
        with self.get_session() as session:
            return session.query(Product).filter(
                Product.product_id == product_id
            ).first()
    
    def update_product_status(self, product_id: str, status: str) -> bool:
        """更新产品状态"""
        with self.get_session() as session:
            product = session.query(Product).filter(
                Product.product_id == product_id
            ).first()
            
            if product:
                product.status = status
                product.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
    
    def get_products_by_status(self, status: str, limit: int = 100) -> List[Product]:
        """根据状态获取产品列表"""
        with self.get_session() as session:
            return session.query(Product).filter(
                Product.status == status
            ).limit(limit).all()
```

---

## 9. 测试指南

### 9.1 单元测试

#### 测试框架配置
```python
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

class TestConfig:
    """测试配置"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    FEISHU_APP_ID = 'test_app_id'
    FEISHU_APP_SECRET = 'test_app_secret'
    COMFYUI_SERVER_ADDRESS = 'http://localhost:8188'

@pytest.fixture
def mock_config():
    """模拟配置"""
    return TestConfig()

@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端"""
    client = Mock()
    client.get_access_token.return_value = 'mock_token'
    client.get_spreadsheet_info.return_value = {
        'spreadsheet_token': 'test_token',
        'sheets': [{'sheet_id': 'sheet1', 'title': 'Sheet1'}]
    }
    return client

class TestProductManager(unittest.TestCase):
    """产品管理器测试"""
    
    def setUp(self):
        """测试设置"""
        self.test_data = [
            {'product_id': 'P001', 'product_name': 'Test Product 1'},
            {'product_id': 'P002', 'product_name': 'Test Product 2'}
        ]
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame(self.test_data)
            self.product_manager = ProductManager('test.csv')
    
    def test_get_paginated_data(self):
        """测试分页数据获取"""
        result = self.product_manager.get_paginated_data(page=1, per_page=1)
        
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['per_page'], 1)
    
    def test_search_products(self):
        """测试产品搜索"""
        result = self.product_manager.search_products('Test Product 1')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['product_name'], 'Test Product 1')
    
    @patch('requests.get')
    def test_download_image(self, mock_get):
        """测试图片下载"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.content = b'fake_image_data'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 测试下载
        result = self.product_manager.download_image(
            'http://example.com/image.jpg', 
            'test_image.jpg'
        )
        
        self.assertTrue(result)
        mock_get.assert_called_once_with('http://example.com/image.jpg')
```

---

## 10. 部署指南

### 10.1 生产环境部署

#### Docker部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "web_app:app"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/toolkit
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=toolkit
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
  
  redis:
    image: redis:6-alpine
    restart: unless-stopped
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 11. 故障排除

### 11.1 常见问题解决

#### 性能问题诊断
```python
import psutil
import time
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.initial_memory = psutil.virtual_memory().used
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory': {
                'total': memory.total,
                'used': memory.used,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'uptime': time.time() - self.start_time
        }
    
    def check_memory_leak(self) -> Dict[str, Any]:
        """检查内存泄漏"""
        current_memory = psutil.virtual_memory().used
        memory_increase = current_memory - self.initial_memory
        
        return {
            'initial_memory': self.initial_memory,
            'current_memory': current_memory,
            'memory_increase': memory_increase,
            'potential_leak': memory_increase > (100 * 1024 * 1024)  # 100MB阈值
        }
```

---

## 12. 更新日志

### 版本历史

#### v2.0.0 (2024-01-XX)
- 新增PNG转换状态控制功能
- 优化ERP系统界面和用户体验
- 增强错误处理和日志记录
- 添加实时状态更新机制

#### v1.5.0 (2023-12-XX)
- 集成ComfyUI工作流处理
- 添加飞书API集成
- 实现图像处理自动化
- 优化性能和内存使用

#### v1.0.0 (2023-11-XX)
- 初始版本发布
- 基础ERP功能实现
- Web界面开发
- 数据管理功能

---

*本文档持续更新中，如有问题请联系开发团队。*
```