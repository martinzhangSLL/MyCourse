# MyCourse 云服务器部署指南

> 适用于阿里云 Alibaba Cloud Linux 3 + Docker 部署

---

## 一、首次部署流程

### 1.1 SSH 免密登录配置（本地执行）

```bash
# 本地生成 SSH key（已有可跳过）
ssh-keygen -t ed25519

# 上传公钥到服务器
ssh-copy-id -p 22 root@47.93.44.227
# 输入密码: Martin1201!
```

**Windows 无 ssh-copy-id 的替代方案：**
```powershell
# 1. 复制公钥内容
cat ~/.ssh/id_ed25519.pub

# 2. SSH 到服务器手动添加
ssh root@47.93.44.227
mkdir -p ~/.ssh
echo "粘贴公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 1.2 服务器环境准备

```bash
ssh root@47.93.44.227

# 安装 Docker（阿里云 Linux 用 CentOS 源）
yum install -y yum-utils
yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动 Docker
systemctl start docker
systemctl enable docker

# 配置 Docker 镜像加速（解决国内访问 Docker Hub 超时问题）
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}
EOF
systemctl restart docker
```

### 1.3 创建部署目录

```bash
ssh root@47.93.44.227
mkdir -p /var/www/mycourse/{db,logs,data,docker,nginx}
```

### 1.4 上传项目文件

**方式1: 使用 tar 打包（推荐，避免文件遗漏）**

```bash
# 本地打包（排除 node_modules 和测试文件）
cd D:/Learning/MyCourse
tar --exclude='repos/frontend/node_modules' \
    --exclude='repos/frontend/.vite' \
    --exclude='repos/frontend/dist' \
    --exclude='repos/frontend/tests' \
    --exclude='repos/frontend/src/views/__tests__' \
    --exclude='repos/backend/__pycache__' \
    --exclude='repos/backend/.pytest_cache' \
    --exclude='repos/backend/tests' \
    -czf /tmp/mycourse.tar.gz .

# 上传到服务器
scp -P 22 /tmp/mycourse.tar.gz root@47.93.44.227:/var/www/mycourse/

# 服务器解压
ssh root@47.93.44.227
cd /var/www/mycourse
tar -xzf mycourse.tar.gz
```

**方式2: 分开上传前后端**

```bash
# 上传部署配置
scp -P 22 deploy/docker-compose.yml root@47.93.44.227:/var/www/mycourse/
scp -P 22 deploy/docker/* root@47.93.44.227:/var/www/mycourse/docker/
scp -P 22 deploy/nginx/* root@47.93.44.227:/var/www/mycourse/nginx/

# 上传后端
scp -P 22 -r repos/backend root@47.93.44.227:/var/www/mycourse/repos/

# 上传前端（打包）
cd repos && tar --exclude='node_modules' --exclude='.vite' --exclude='dist' -czf /tmp/frontend.tar.gz frontend
scp -P 22 /tmp/frontend.tar.gz root@47.93.44.227:/var/www/mycourse/repos/
ssh root@47.93.44.227 "cd /var/www/mycourse/repos && tar -xzf frontend.tar.gz"
```

### 1.5 配置并启动服务

```bash
ssh root@47.93.44.227
cd /var/www/mycourse

# 设置 JWT Secret（生产环境必须设置强密码）
export JWT_SECRET_KEY="$(openssl rand -base64 32)"

# 停止已有 nginx（避免端口冲突）
systemctl stop nginx 2>/dev/null || true
killall nginx 2>/dev/null || true

# 启动服务
docker compose up -d --build
```

### 1.6 验证部署

```bash
# 检查容器状态
docker compose ps

# 测试前端
curl http://localhost/

# 测试后端健康检查
curl http://localhost:8001/health

# 测试登录 API
curl -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123","role":"admin"}'
```

---

## 二、服务管理命令

### 启动/停止/重启

```bash
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose start|stop|restart"
```

### 查看日志

```bash
# 所有服务日志
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose logs -f"

# 特定服务日志
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose logs -f nginx"
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose logs -f backend1"
```

### 重新构建

```bash
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose up -d --build"
```

### 完全重置

```bash
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose down -v && docker volume prune -f"
```

---

## 三、更新部署流程

### 3.1 更新代码后重新部署

```bash
# 本地重新打包上传
cd D:/Learning/MyCourse
tar --exclude='repos/frontend/node_modules' \
    --exclude='repos/frontend/.vite' \
    --exclude='repos/frontend/dist' \
    -czf /tmp/mycourse.tar.gz .

scp -P 22 /tmp/mycourse.tar.gz root@47.93.44.227:/var/www/mycourse/
ssh root@47.93.44.227 "cd /var/www/mycourse && tar -xzf mycourse.tar.gz && docker compose up -d --build"
```

### 3.2 仅更新前端

```bash
cd D:/Learning/MyCourse/repos
tar --exclude='node_modules' --exclude='.vite' --exclude='dist' -czf /tmp/frontend.tar.gz frontend
scp -P 22 /tmp/frontend.tar.gz root@47.93.44.227:/var/www/mycourse/repos/
ssh root@47.93.44.227 "cd /var/www/mycourse/repos && tar -xzf frontend.tar.gz && docker compose build frontend && docker compose up -d frontend"
```

### 3.3 仅更新后端

```bash
cd D:/Learning/MyCourse/repos
scp -P 22 -r backend root@47.93.44.227:/var/www/mycourse/repos/
ssh root@47.93.44.227 "cd /var/www/mycourse && docker compose build backend1 backend2 && docker compose up -d backend1 backend2"
```

---

## 四、关键配置文件说明

### 4.1 docker-compose.yml

```yaml
services:
  backend1:
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}  # 必须设置
      - DATABASE_URL=sqlite:////var/www/mycourse/db/mycourse.db  # 4个斜杠=绝对路径
```

**重要**: SQLite URL 必须用 `sqlite:///` + 绝对路径 + 4个斜杠

### 4.2 nginx/nginx.conf

```nginx
# Docker DNS 解析器（必须）
resolver 127.0.0.11 ipv6=off valid=10s;

# 代理配置使用变量方式（避免启动时 DNS 解析失败）
location /api/ {
    set $backend backend1:8001;
    proxy_pass http://$backend;
}
```

### 4.3 前端独立 nginx 配置

standalone-frontend.conf 用于 Docker 内部 nginx，不要在此配置 upstream。

---

## 五、常见问题排查

### 5.1 容器不断重启

```bash
# 查看容器日志
docker compose logs <服务名>

# 常见原因:
# - DATABASE_URL 格式错误（应为 sqlite:////xxx）
# - 卷挂载路径不存在
# - nginx upstream 解析失败
```

### 5.2 nginx 报 "host not found in upstream"

**原因**: nginx 启动时容器未就绪，DNS 解析失败

**解决**: 使用变量方式 + resolver
```nginx
resolver 127.0.0.11 ipv6=off valid=10s;
set $backend backend1:8001;
proxy_pass http://$backend;
```

### 5.3 Docker Hub 下载超时

**解决**: 配置镜像加速器
```bash
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}
EOF
systemctl restart docker
```

### 5.4 端口 80 被占用

```bash
# 检查端口占用
netstat -tlnp | grep ':80'

# 停止占用进程
systemctl stop nginx
killall nginx
```

### 5.5 后端无法连接数据库

```bash
# 检查卷是否正确挂载
docker volume inspect mycourse_db-data

# 检查容器内目录
docker exec mycourse-backend1 ls -la /var/www/mycourse/db/
```

---

## 六、生产环境安全建议

### 6.1 JWT Secret Key

```bash
# 使用强随机密钥
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
```

### 6.2 防火墙配置

```bash
# 只开放 80/443 端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 6.3 数据库备份

```bash
# 定期备份 SQLite
ssh root@47.93.44.227 "cp /var/lib/docker/volumes/mycourse_db-data/_data/mycourse.db /var/www/mycourse/db/backup_$(date +%Y%m%d).db"
```

---

## 七、服务器信息速查

| 项目 | 值 |
|------|-----|
| 服务器 IP | 47.93.44.227 |
| SSH 端口 | 22 |
| 用户名 | root |
| 项目目录 | /var/www/mycourse |
| 数据库 | /var/www/mycourse/db/mycourse.db |
| 初始管理员 | admin / MarT17! |

### Docker 服务

```bash
# 一键启动
ssh root@47.93.44.227 "cd /var/www/mycourse && export JWT_SECRET_KEY='$existing_key' && docker compose up -d"
```

---

## 八、部署检查清单

- [ ] SSH 免密登录已配置
- [ ] Docker 已安装并启动
- [ ] 镜像加速器已配置
- [ ] 端口 80 无冲突
- [ ] JWT_SECRET_KEY 已设置
- [ ] docker-compose.yml 中 DATABASE_URL 使用 4 个斜杠
- [ ] nginx.conf 使用变量方式代理
- [ ] 前端 standalone-frontend.conf 无 upstream
- [ ] 容器已启动并运行
- [ ] 登录测试通过
