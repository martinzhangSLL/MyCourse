# 境界图片上传功能设计

## 概述

为管理员提供境界图片上传功能，确保图片持久化存储在宿主机目录中，不依赖 Docker 卷。

## 架构设计

```
宿主机: /var/www/mycourse/pics/
    ↓ 挂载
容器内: /app/pics/
    ↓ 服务
Nginx: /pics/ → 静态文件服务
```

## 变更清单

### 1. docker-compose.yml

**修改内容**：将 `pics-data` 命名卷改为 host 目录绑定

```yaml
services:
  backend1:
    volumes:
      - /var/www/mycourse/pics:/app/pics  # 替换 pics-data

  backend2:
    volumes:
      - /var/www/mycourse/pics:/app/pics  # 替换 pics-data

  nginx:
    volumes:
      - /var/www/mycourse/pics:/usr/share/nginx/html/pics:ro  # 新增

volumes:
  pics-data:  # 删除此行
```

### 2. 后端 - 图片上传接口

**端点**：`POST /api/upload`

**请求**：
- Content-Type: `multipart/form-data`
- 字段: `file` (图片文件)

**响应**：
```json
{
  "url": "/pics/abc123.png",
  "filename": "abc123.png"
}
```

**约束**：
- 允许类型: `image/png`, `image/jpeg`, `image/gif`
- 最大大小: 5MB
- 文件名: UUID 随机化 + 原始扩展名

**权限**：仅管理员可访问

### 3. Nginx 配置

**新增静态文件路由**：
```nginx
location /pics/ {
    alias /usr/share/nginx/html/pics/;
    autoindex off;
    add_header Cache-Control "public, max-age=31536000";
}
```

### 4. 前端 - 上传组件

**位置**：`repos/frontend/src/views/admin/RankManage.vue`

**功能**：
- 图片上传按钮（支持点击和拖拽）
- 上传进度显示
- 上传成功后自动回填 `image_url` 字段
- 图片预览

## 文件清单

| 文件 | 操作 |
|------|------|
| `deploy/docker-compose.yml` | 修改 |
| `deploy/nginx/nginx.conf` | 修改 |
| `repos/backend/app/routers/upload_router.py` | 新增 |
| `repos/frontend/src/views/admin/RankManage.vue` | 修改 |

## 安全考虑

1. 文件类型白名单验证（MIME type + 扩展名双重检查）
2. 文件大小限制 5MB
3. 文件名 UUID 随机化，防止路径遍历和文件名冲突
4. 管理员权限验证（使用现有 admin 认证中间件）
5. 上传目录与代码分离，阻止 PHP 等脚本执行