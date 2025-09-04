# 部署指南

## 目录

1. [部署概述](#1-部署概述)
2. [环境准备](#2-环境准备)
3. [本地开发部署](#3-本地开发部署)
4. [生产环境部署](#4-生产环境部署)
5. [Docker部署](#5-docker部署)
6. [云平台部署](#6-云平台部署)
7. [监控和维护](#7-监控和维护)
8. [故障排除](#8-故障排除)

---

## 1. 部署概述

### 1.1 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   Flask应用     │    │   外部服务      │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│   (飞书/ComfyUI)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   数据存储      │
                       │   (CSV/文件)    │
                       └─────────────────┘
```

### 1.2 部署选项

#### 开发环境
- **目的**：本地开发和测试
- **特点**：快速启动，调试友好
- **适用场景**：功能开发、bug修复

#### 测试环境
- **目的**：功能验证和集成测试
- **特点**：接近生产环境配置
- **适用场景**：版本发布前验证

#### 生产环境
- **目的**：正式业务运行
- **特点**：高可用、高性能、安全
- **适用场景**：正式业务使用

### 1.3 部署要求

#### 最低配置
- **CPU**：2核心
- **内存**：4GB RAM
- **存储**：20GB可用空间
- **网络**：100Mbps带宽

#### 推荐配置
- **CPU**：4核心或更多
- **内存**：8GB RAM或更多
- **存储**：100GB SSD
- **网络**：1Gbps带宽

---

## 2. 环境准备

### 2.1 操作系统要求

#### Linux (推荐)
```bash
# Ubuntu 20.04 LTS 或更新版本
sudo apt update
sudo apt upgrade -y

# CentOS 8 或更新版本
sudo yum update -y
```

#### macOS
```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 更新系统
brew update
brew upgrade
```

#### Windows
```powershell
# 启用 WSL2 (推荐)
wsl --install

# 或使用 Windows 原生环境
# 安装 Python 3.8+
# 安装 Git
```

### 2.2 Python环境

#### 安装Python 3.8+
```bash
# Ubuntu/Debian
sudo apt install python3.8 python3.8-pip python3.8-venv

# CentOS/RHEL
sudo yum install python38 python38-pip

# macOS
brew install python@3.8

# 验证安装
python3 --version
pip3 --version
```

#### 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv toolkit_env

# 激活虚拟环境
# Linux/macOS
source toolkit_env/bin/activate

# Windows
toolkit_env\Scripts\activate

# 升级pip
pip install --upgrade pip
```

### 2.3 系统依赖

#### Linux系统依赖
```bash
# Ubuntu/Debian
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev

# CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    openssl-devel \
    libffi-devel \
    python3-devel \
    postgresql-devel \
    libjpeg-devel \
    libpng-devel \
    freetype-devel
```

#### macOS系统依赖
```bash
# 安装必要的开发工具
xcode-select --install

# 安装图像处理库
brew install jpeg libpng freetype
```

---

## 3. 本地开发部署

### 3.1 获取源码

```bash
# 克隆代码仓库
git clone <repository_url>
cd toolKit

# 查看项目结构
ls -la
```

### 3.2 安装依赖

```bash
# 激活虚拟环境
source toolkit_env/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 验证安装
pip list
```

### 3.3 配置文件

#### 创建配置文件
```bash
# 复制配置模板
cp config.py.example config.py

# 编辑配置文件
vim config.py
```

#### 配置示例
```python
# config.py
class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    
    # 飞书配置
    FEISHU_APP_ID = 'your_app_id'
    FEISHU_APP_SECRET = 'your_app_secret'
    
    # ComfyUI配置
    COMFYUI_SERVER_ADDRESS = 'http://localhost:8188'
    
    # 文件路径
    UPLOAD_FOLDER = 'uploads'
    DOWNLOAD_FOLDER = 'downloads'
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'logs/app.log'
```

### 3.4 启动开发服务器

```bash
# 启动Flask开发服务器
python web_app.py

# 或使用flask命令
export FLASK_APP=web_app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8080
```

### 3.5 验证部署

```bash
# 检查服务状态
curl http://localhost:8080

# 检查API接口
curl http://localhost:8080/api/data

# 查看日志
tail -f logs/app.log
```

---

## 4. 生产环境部署

### 4.1 服务器准备

#### 创建应用用户
```bash
# 创建专用用户
sudo useradd -m -s /bin/bash toolkit
sudo usermod -aG sudo toolkit

# 切换到应用用户
sudo su - toolkit
```

#### 创建目录结构
```bash
# 创建应用目录
mkdir -p /opt/toolkit/{app,logs,uploads,downloads,backups}

# 设置权限
sudo chown -R toolkit:toolkit /opt/toolkit
sudo chmod -R 755 /opt/toolkit
```

### 4.2 部署应用

#### 部署代码
```bash
# 进入应用目录
cd /opt/toolkit/app

# 克隆代码
git clone <repository_url> .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 生产配置
```python
# config.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    
    # 安全配置
    SECRET_KEY = 'your-secret-key-here'
    
    # 数据库配置
    DATABASE_URL = 'postgresql://user:password@localhost/toolkit'
    
    # 外部服务配置
    FEISHU_APP_ID = 'prod_app_id'
    FEISHU_APP_SECRET = 'prod_app_secret'
    COMFYUI_SERVER_ADDRESS = 'http://comfyui-server:8188'
    
    # 文件路径
    UPLOAD_FOLDER = '/opt/toolkit/uploads'
    DOWNLOAD_FOLDER = '/opt/toolkit/downloads'
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/opt/toolkit/logs/app.log'
    
    # 性能配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1年
```

### 4.3 Web服务器配置

#### 安装Nginx
```bash
# Ubuntu/Debian
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Nginx配置
```nginx
# /etc/nginx/sites-available/toolkit
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/toolkit.crt;
    ssl_certificate_key /etc/ssl/private/toolkit.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 静态文件
    location /static {
        alias /opt/toolkit/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件
    location /uploads {
        alias /opt/toolkit/uploads;
        expires 1d;
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
}
```

#### 启用站点
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/toolkit /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

### 4.4 应用服务配置

#### 安装Gunicorn
```bash
# 在虚拟环境中安装
source /opt/toolkit/app/venv/bin/activate
pip install gunicorn
```

#### Gunicorn配置
```python
# gunicorn.conf.py
bind = "127.0.0.1:8080"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5

# 日志配置
accesslog = "/opt/toolkit/logs/gunicorn_access.log"
errorlog = "/opt/toolkit/logs/gunicorn_error.log"
loglevel = "info"

# 进程配置
user = "toolkit"
group = "toolkit"
pidfile = "/opt/toolkit/app/gunicorn.pid"

# 安全配置
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

#### Systemd服务配置
```ini
# /etc/systemd/system/toolkit.service
[Unit]
Description=ToolKit Web Application
After=network.target

[Service]
Type=forking
User=toolkit
Group=toolkit
WorkingDirectory=/opt/toolkit/app
Environment=PATH=/opt/toolkit/app/venv/bin
ExecStart=/opt/toolkit/app/venv/bin/gunicorn --config gunicorn.conf.py web_app:app
ExecReload=/bin/kill -s HUP $MAINPID
PIDFile=/opt/toolkit/app/gunicorn.pid
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/toolkit

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start toolkit

# 设置开机自启
sudo systemctl enable toolkit

# 查看服务状态
sudo systemctl status toolkit
```

---

## 5. Docker部署

### 5.1 Docker环境准备

#### 安装Docker
```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd -m -u 1000 toolkit && \
    mkdir -p /app /app/logs /app/uploads /app/downloads && \
    chown -R toolkit:toolkit /app

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置权限
RUN chown -R toolkit:toolkit /app

# 切换到应用用户
USER toolkit

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "web_app:app"]
```

### 5.3 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    container_name: toolkit-web
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://toolkit:password@db:5432/toolkit
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
      - ./logs:/app/logs
      - ./config.py:/app/config.py:ro
    depends_on:
      - db
      - redis
    networks:
      - toolkit-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:13-alpine
    container_name: toolkit-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=toolkit
      - POSTGRES_USER=toolkit
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - toolkit-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U toolkit"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    container_name: toolkit-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - toolkit-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: toolkit-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./uploads:/var/www/uploads:ro
    depends_on:
      - web
    networks:
      - toolkit-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:

networks:
  toolkit-network:
    driver: bridge
```

### 5.4 Docker部署命令

```bash
# 构建和启动服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web

# 进入容器
docker-compose exec web bash

# 停止服务
docker-compose down

# 清理资源
docker-compose down -v --remove-orphans
docker system prune -f
```

---

## 6. 云平台部署

### 6.1 AWS部署

#### EC2实例配置
```bash
# 创建EC2实例
aws ec2 run-instances \
    --image-id ami-0abcdef1234567890 \
    --count 1 \
    --instance-type t3.medium \
    --key-name my-key-pair \
    --security-group-ids sg-903004f8 \
    --subnet-id subnet-6e7f829e

# 配置安全组
aws ec2 authorize-security-group-ingress \
    --group-id sg-903004f8 \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-903004f8 \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

#### RDS数据库配置
```bash
# 创建RDS实例
aws rds create-db-instance \
    --db-instance-identifier toolkit-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username toolkit \
    --master-user-password mypassword \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-903004f8
```

#### ELB负载均衡器
```bash
# 创建应用负载均衡器
aws elbv2 create-load-balancer \
    --name toolkit-alb \
    --subnets subnet-6e7f829e subnet-e7f829f \
    --security-groups sg-903004f8

# 创建目标组
aws elbv2 create-target-group \
    --name toolkit-targets \
    --protocol HTTP \
    --port 8080 \
    --vpc-id vpc-12345678
```

### 6.2 阿里云部署

#### ECS实例配置
```bash
# 使用阿里云CLI创建ECS实例
aliyun ecs CreateInstance \
    --RegionId cn-hangzhou \
    --ImageId ubuntu_20_04_x64_20G_alibase_20210420.vhd \
    --InstanceType ecs.t6-c1m2.large \
    --SecurityGroupId sg-bp1fg655nh68xyz9**** \
    --VSwitchId vsw-bp1s5fnvk4gn2tws0****
```

#### RDS数据库配置
```bash
# 创建RDS实例
aliyun rds CreateDBInstance \
    --RegionId cn-hangzhou \
    --Engine PostgreSQL \
    --EngineVersion 13.0 \
    --DBInstanceClass rds.pg.s2.large \
    --DBInstanceStorage 20 \
    --PayType Postpaid
```

### 6.3 腾讯云部署

#### CVM实例配置
```bash
# 使用腾讯云CLI创建CVM实例
tccli cvm RunInstances \
    --Placement.Zone ap-guangzhou-3 \
    --ImageId img-pi0ii46r \
    --InstanceChargeType POSTPAID_BY_HOUR \
    --InstanceType S5.MEDIUM2 \
    --SystemDisk.DiskType CLOUD_PREMIUM \
    --SystemDisk.DiskSize 50
```

---

## 7. 监控和维护

### 7.1 系统监控

#### 安装监控工具
```bash
# 安装Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 配置Prometheus
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'toolkit'
    static_configs:
      - targets: ['localhost:8080']
EOF

# 启动Prometheus
./prometheus --config.file=prometheus.yml
```

#### 安装Grafana
```bash
# Ubuntu/Debian
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana

# 启动Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### 7.2 日志管理

#### 日志轮转配置
```bash
# /etc/logrotate.d/toolkit
/opt/toolkit/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 toolkit toolkit
    postrotate
        systemctl reload toolkit
    endscript
}
```

#### ELK Stack部署
```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### 7.3 备份策略

#### 数据库备份
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/toolkit/backups"
DB_NAME="toolkit"
DB_USER="toolkit"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 文件备份
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /opt/toolkit/uploads /opt/toolkit/downloads

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*backup*" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### 定时备份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点执行备份
0 2 * * * /opt/toolkit/scripts/backup.sh >> /opt/toolkit/logs/backup.log 2>&1
```

### 7.4 性能优化

#### 系统调优
```bash
# /etc/sysctl.conf
# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 文件描述符限制
fs.file-max = 65535

# 应用配置
sysctl -p
```

#### 应用优化
```python
# 性能配置
class ProductionConfig:
    # 数据库连接池
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 会话配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.from_url('redis://localhost:6379/1')
    
    # 文件上传优化
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
```

---

## 8. 故障排除

### 8.1 常见问题诊断

#### 服务无法启动
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8080

# 检查进程状态
sudo systemctl status toolkit

# 查看详细日志
sudo journalctl -u toolkit -f

# 检查配置文件
python -c "import config; print('Config loaded successfully')"
```

#### 性能问题诊断
```bash
# 系统资源监控
top
htop
iotop

# 内存使用情况
free -h
ps aux --sort=-%mem | head

# 磁盘使用情况
df -h
du -sh /opt/toolkit/*

# 网络连接状态
ss -tuln
netstat -i
```

#### 数据库问题诊断
```bash
# 检查数据库连接
psql -U toolkit -h localhost -d toolkit -c "SELECT version();"

# 查看数据库大小
psql -U toolkit -h localhost -d toolkit -c "SELECT pg_size_pretty(pg_database_size('toolkit'));"

# 检查慢查询
psql -U toolkit -h localhost -d toolkit -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 8.2 故障恢复流程

#### 服务故障恢复
```bash
#!/bin/bash
# recovery.sh

echo "Starting service recovery..."

# 停止服务
sudo systemctl stop toolkit
sudo systemctl stop nginx

# 检查并修复文件权限
sudo chown -R toolkit:toolkit /opt/toolkit
sudo chmod -R 755 /opt/toolkit

# 清理临时文件
sudo rm -rf /tmp/toolkit_*
sudo rm -rf /opt/toolkit/app/*.pyc

# 重启服务
sudo systemctl start toolkit
sudo systemctl start nginx

# 验证服务状态
sleep 10
curl -f http://localhost/health || echo "Service health check failed"

echo "Recovery completed"
```

#### 数据恢复流程
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting data restoration from $BACKUP_FILE"

# 停止应用服务
sudo systemctl stop toolkit

# 恢复数据库
gunzip -c $BACKUP_FILE | psql -U toolkit -h localhost toolkit

# 重启服务
sudo systemctl start toolkit

echo "Data restoration completed"
```

### 8.3 安全事件响应

#### 安全检查脚本
```bash
#!/bin/bash
# security_check.sh

echo "Starting security check..."

# 检查异常登录
sudo grep "Failed password" /var/log/auth.log | tail -20

# 检查异常进程
ps aux | grep -v "\[" | awk '{print $11}' | sort | uniq -c | sort -nr | head -10

# 检查网络连接
ss -tuln | grep -E ":(22|80|443|8080)"

# 检查文件权限
find /opt/toolkit -type f -perm /o+w -ls

# 检查系统更新
sudo apt list --upgradable

echo "Security check completed"
```

#### 应急响应流程
1. **隔离系统**：断开网络连接
2. **保存证据**：备份日志和系统状态
3. **分析威胁**：确定攻击类型和影响范围
4. **修复漏洞**：应用安全补丁
5. **恢复服务**：从备份恢复数据
6. **加强监控**：增加安全监控措施

---

## 附录

### A. 部署检查清单

#### 部署前检查
- [ ] 服务器资源充足（CPU、内存、磁盘）
- [ ] 网络连接正常
- [ ] 依赖服务可用（数据库、Redis等）
- [ ] 配置文件正确
- [ ] SSL证书有效
- [ ] 备份策略就绪

#### 部署后验证
- [ ] 服务正常启动
- [ ] 健康检查通过
- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 监控告警配置

### B. 常用命令参考

```bash
# 服务管理
sudo systemctl start/stop/restart/status toolkit
sudo systemctl enable/disable toolkit

# 日志查看
sudo journalctl -u toolkit -f
tail -f /opt/toolkit/logs/app.log

# 进程管理
ps aux | grep toolkit
kill -9 <pid>
pkill -f toolkit

# 网络诊断
curl -I http://localhost:8080
telnet localhost 8080
nmap -p 8080 localhost

# 文件操作
find /opt/toolkit -name "*.log" -mtime +7 -delete
du -sh /opt/toolkit/*
df -h
```

### C. 配置模板

#### 环境变量模板
```bash
# .env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/toolkit
REDIS_URL=redis://localhost:6379/0
FEISHU_APP_ID=your-app-id
FEISHU_APP_SECRET=your-app-secret
COMFYUI_SERVER_ADDRESS=http://localhost:8188
UPLOAD_FOLDER=/opt/toolkit/uploads
DOWNLOAD_FOLDER=/opt/toolkit/downloads
LOG_LEVEL=INFO
```

---

*本部署指南版本：v2.0.0*  
*最后更新时间：2024年1月*  
*如有问题，请联系运维团队*