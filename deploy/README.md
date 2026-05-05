# MyCourse 部署指南

## 快速开始

### 1. 服务器环境准备

在阿里云服务器上执行以下命令安装 Docker 环境：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 启动 Docker
systemctl start docker
systemctl enable docker
```

### 2. 上传部署文件

```bash
rsync -avz -e "ssh -p 22" \
  --exclude 'node_modules' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '*.pyc' \
  --exclude '.git' \
  ./ root@47.93.44.227:/var/www/mycourse/
```

### 3. 配置环境变量

```bash
ssh root@47.93.44.227
cd /var/www/mycourse

# 设置 JWT Secret Key (重要: 生产环境必须设置!)
export JWT_SECRET_KEY="your-secret-key-here"
```

### 4. 启动服务

```bash
cd /var/www/mycourse

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 使用部署脚本

本地执行 `deploy.sh` 可以一键部署：

```bash
# 部署
./deploy.sh deploy

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 健康检查
./deploy.sh health

# 重启服务
./deploy.sh restart
```

## 服务架构

```
                    ┌─────────────────────────────────────┐
                    │          Nginx (端口 80)            │
                    │    反向代理 + 负载均衡 + 静态文件    │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼──────────────────────┐
              │                    │                      │
              ▼                    ▼                      ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Backend API 1   │  │  Backend API 2   │  │  Frontend       │
    │  (端口 8001)     │  │  (端口 8001)     │  │  (端口 3000)    │
    └────────┬────────┘  └────────┬────────┘  └─────────────────┘
             │                    │
             └──────────┬─────────┘
                        │
                        ▼
              ┌─────────────────┐
              │   SQLite DB     │
              │ (/var/www/.../db)│
              └─────────────────┘
```

## 验证部署

### 服务状态
```bash
docker-compose ps
```

### 健康检查
```bash
# 前端
curl http://47.93.44.227/

# 后端 API
curl http://47.93.44.227/api/health
```

### 负载均衡验证
```bash
# 多次访问，观察 X-Backend header 或响应时间差异
curl http://47.93.44.227/api/health
curl http://47.93.44.227/api/health
```

## 目录结构

```
/var/www/mycourse/
├── docker-compose.yml     # 服务编排配置
├── docker/
│   ├── Dockerfile.backend # 后端 Docker 镜像
│   └── Dockerfile.frontend# 前端 Docker 镜像
├── nginx/
│   ├── nginx.conf         # Nginx 主配置 (负载均衡)
│   └── standalone-frontend.conf # 独立前端配置
├── db/                    # SQLite 数据库目录
├── logs/                  # 日志目录
└── data/                  # 持久化数据
```

## 容器说明

| 容器名 | 镜像 | 端口 | 说明 |
|--------|------|------|------|
| mycourse-frontend | nginx:alpine | 80 | 前端静态文件服务 |
| mycourse-backend1 | mycourse-backend | 8001 | 后端 API 服务 1 |
| mycourse-backend2 | mycourse-backend | 8001 | 后端 API 服务 2 |
| mycourse-nginx | nginx:alpine | 80, 443 | 负载均衡器 |

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose stop

# 重启所有服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend1

# 重新构建并启动
docker-compose up -d --build

# 进入后端容器
docker exec -it mycourse-backend1 /bin/bash

# 初始化管理员
docker exec -it mycourse-backend1 python scripts/init_admin.py
```

## 安全建议

1. **JWT Secret Key**: 生产环境必须设置强密码
2. **防火墙**: 只开放 80/443 端口
3. **fail2ban**: 配置防止 SSH 暴力破解
4. **定期备份**: 备份 SQLite 数据库文件

## 故障排除

### 容器无法启动
```bash
# 查看日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep -E '80|8001|8002'
```

### 数据库连接错误
```bash
# 检查数据库文件权限
ls -la /var/www/mycourse/db/

# 修复权限
chmod 755 /var/www/mycourse/db
chmod 644 /var/www/mycourse/db/*.db
```

### Nginx 502 错误
```bash
# 检查后端是否启动
docker-compose ps

# 检查后端健康状态
curl http://localhost:8001/api/health
```
