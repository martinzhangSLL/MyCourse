# 云服务器部署信息表

> 已完成部署配置生成

---

## 一、服务器基本信息

### 连接信息
- **云服务商**：阿里云
- **服务器公网 IP**：47.93.44.227
- **SSH 端口**：22
- **服务器用户名**：root
- **登录方式**：密码登录 → Martin1201!

### 系统环境
- **操作系统**：Alibaba Cloud Linux 3.2104 LTS 64位
- **CPU 架构**：X86_64

---

## 二、域名配置（如有）

- **域名**：无
- **是否已备案**：否
- **是否已有 SSL 证书**：否
- **是否使用 CDN**：否

---

## 三、部署配置

### 部署方式
- [x] **Docker 部署**（已完成 docker-compose.yml）

### 数据库选择
- [x] **继续使用 SQLite**（当前方案）

### Nginx 配置
- [x] 配置 Nginx 反向代理 + 负载均衡（2个后端服务）

---

## 四、端口配置

- **前端端口**：80 (容器内 3000)
- **后端 API 端口**：8001 (2个实例)
- **Nginx 对外端口**：80, 443

---

## 五、安全配置

- **防火墙**：云服务商安全组已开放必要端口
- **fail2ban**：建议配置（见 deploy.sh）

---

## 六、目录规划

- **项目部署目录**：/var/www/mycourse
- **数据库文件目录**：/var/www/mycourse/db
- **日志目录**：/var/www/mycourse/logs

---

## 七、预期负载

- **日均访问量**：100-1000
- **是否需要负载均衡**：是，2个后端服务

---

## 八、已生成文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| docker-compose.yml | /var/www/mycourse/ | 服务编排配置 |
| Dockerfile.backend | /var/www/mycourse/docker/ | 后端 Docker 镜像 |
| Dockerfile.frontend | /var/www/mycourse/docker/ | 前端 Docker 镜像 |
| nginx.conf | /var/www/mycourse/nginx/ | Nginx 负载均衡配置 |
| standalone-frontend.conf | /var/www/mycourse/nginx/ | 独立前端配置 |
| deploy.sh | /var/www/mycourse/ | 一键部署脚本 |
| README.md | /var/www/mycourse/ | 部署文档 |

---

## 九、部署方法

### 方法1: 使用部署脚本
```bash
cd deploy
./deploy.sh deploy
```

### 方法2: 手动部署
```bash
# 1. 上传文件到服务器
rsync -avz -e "ssh -p 22" ./ root@47.93.44.227:/var/www/mycourse/

# 2. SSH 到服务器
ssh root@47.93.44.227

# 3. 设置环境变量
export JWT_SECRET_KEY="your-secret-key"

# 4. 启动服务
cd /var/www/mycourse
docker-compose up -d
```

---

## 十、验证命令

```bash
# 服务状态
docker-compose ps

# 健康检查
curl http://47.93.44.227/api/health

# 负载均衡验证
curl http://47.93.44.227/api/health
curl http://47.93.44.227/api/health
```
