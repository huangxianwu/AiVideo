# ToolKit - 智能图像处理工作流平台

一个集成飞书API、ComfyUI工作流和ERP系统的智能图像处理平台，提供完整的自动化图像处理解决方案。

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone <repository_url>
cd toolKit

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑 .env 文件填入配置信息

# 4. 启动应用
python web_app.py
```

访问 http://localhost:5000 开始使用

## 📚 完整文档

### 🎯 按角色查看文档

| 角色 | 推荐文档 | 说明 |
|------|----------|------|
| **新用户** | [用户手册](docs/USER_MANUAL.md) | 快速上手指南和功能介绍 |
| **开发者** | [开发者指南](docs/DEVELOPER_GUIDE.md) | 开发环境、架构设计、API文档 |
| **运维人员** | [部署指南](docs/DEPLOYMENT_GUIDE.md) | 部署、监控、维护指南 |
| **产品经理** | [项目文档](docs/PROJECT_DOCUMENTATION.md) | 完整的功能特性和技术规范 |

### 📖 按内容查看文档

| 文档类型 | 文档链接 | 内容概述 |
|----------|----------|----------|
| **📋 文档导航** | [文档中心](docs/README.md) | 所有文档的导航和快速查找 |
| **📖 项目概述** | [项目文档](docs/PROJECT_DOCUMENTATION.md) | 项目完整介绍和技术规范 |
| **👤 用户指南** | [用户手册](docs/USER_MANUAL.md) | 详细的操作指南和功能说明 |
| **💻 开发文档** | [开发者指南](docs/DEVELOPER_GUIDE.md) | 开发环境、架构、编码规范 |
| **🔌 API文档** | [API参考](docs/API_REFERENCE.md) | 完整的API接口文档 |
| **🚀 部署文档** | [部署指南](docs/DEPLOYMENT_GUIDE.md) | 部署、监控、维护指南 |

> 💡 **提示**：首次使用建议先查看 [文档中心](docs/README.md) 了解完整的文档结构

## ✨ 核心功能

- 🔐 **飞书集成** - 自动获取表格数据和图片
- 🤖 **AI工作流** - ComfyUI智能图像处理
- 🌐 **Web界面** - 直观的操作界面和ERP系统
- 🎨 **图像处理** - 白底去除、PNG转换、批量处理
- 📊 **数据管理** - CSV导入、状态跟踪、报告生成
- 🔄 **自动化** - 完整的端到端处理流程

## 🛠️ 技术栈

- **后端**: Python 3.8+, Flask, asyncio
- **前端**: HTML5, CSS3, JavaScript
- **集成**: 飞书API, ComfyUI API
- **数据**: CSV, JSON, 图像处理
- **部署**: Docker, Nginx, Gunicorn

## 📋 快速导航

### 常见任务

| 我想要... | 查看文档 |
|-----------|----------|
| 🚀 **快速上手** | [用户手册 - 快速开始](docs/USER_MANUAL.md#快速开始) |
| 🔧 **搭建开发环境** | [开发者指南 - 环境设置](docs/DEVELOPER_GUIDE.md#开发环境设置) |
| 🚀 **部署到生产** | [部署指南](docs/DEPLOYMENT_GUIDE.md) |
| 🔌 **API集成** | [API参考文档](docs/API_REFERENCE.md) |
| ❓ **解决问题** | [用户手册 - 故障排除](docs/USER_MANUAL.md#故障排除) |
| 📖 **了解架构** | [项目文档 - 系统架构](docs/PROJECT_DOCUMENTATION.md#系统架构) |

### 详细安装和配置

完整的安装步骤、环境配置、系统要求等详细信息，请查看：
- 📖 [项目文档 - 安装指南](docs/PROJECT_DOCUMENTATION.md#安装指南)
- 👤 [用户手册 - 系统要求](docs/USER_MANUAL.md#系统要求)
- 💻 [开发者指南 - 开发环境](docs/DEVELOPER_GUIDE.md#开发环境设置)

## 🏗️ 项目结构

```
toolKit/
├── docs/                    # 📚 完整文档目录
│   ├── README.md           # 📋 文档中心导航
│   ├── PROJECT_DOCUMENTATION.md  # 📖 项目完整文档
│   ├── USER_MANUAL.md      # 👤 用户操作手册
│   ├── DEVELOPER_GUIDE.md  # 💻 开发者指南
│   ├── API_REFERENCE.md    # 🔌 API接口文档
│   └── DEPLOYMENT_GUIDE.md # 🚀 部署运维指南
├── web_app.py              # 🌐 Web应用主程序
├── main.py                 # 🚀 命令行工具入口
├── config.py               # ⚙️ 配置管理
├── feishu_client.py        # 📊 飞书API客户端
├── comfyui_client.py       # 🤖 ComfyUI API客户端
├── templates/              # 📄 Web模板目录
├── static/                 # 🎨 静态资源目录
└── requirements.txt        # 📦 依赖包列表
```

## 🌟 主要特色

### 🎯 智能化处理
- **自动化工作流**：从数据获取到结果输出的完整自动化
- **智能重试机制**：网络异常和处理失败的自动重试
- **状态实时跟踪**：处理进度和状态的实时监控

### 🔧 易用性设计
- **Web可视化界面**：直观的操作界面，无需命令行
- **批量处理支持**：支持大规模数据的批量处理
- **详细日志记录**：完整的操作日志和错误追踪

### 🚀 高性能架构
- **异步处理**：高并发的异步任务处理
- **模块化设计**：松耦合的模块化架构
- **可扩展性**：支持插件和功能扩展

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [开发者指南](docs/DEVELOPER_GUIDE.md) 了解：
- 开发环境搭建
- 代码规范和最佳实践
- 测试指南
- 提交流程

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 获取帮助

### 📚 文档资源
- [文档中心](docs/README.md) - 完整的文档导航
- [常见问题](docs/USER_MANUAL.md#常见问题) - FAQ和解决方案
- [故障排除](docs/USER_MANUAL.md#故障排除) - 问题诊断指南

### 💬 社区支持
- **GitHub Issues** - 报告问题和功能请求
- **Discussions** - 社区讨论和经验分享
- **Wiki** - 社区维护的知识库

### 🔧 技术支持
- **邮箱**: support@toolkit.com
- **文档问题**: docs@toolkit.com

---

**开始使用**: [用户手册](docs/USER_MANUAL.md) | **开发指南**: [开发者文档](docs/DEVELOPER_GUIDE.md) | **API文档**: [API参考](docs/API_REFERENCE.md)