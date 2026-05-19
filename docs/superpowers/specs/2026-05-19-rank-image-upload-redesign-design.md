# 段位图片上传功能设计

## 概述

重构段位管理中的图片上传功能，使其能同时适配本地开发环境和 Docker 生产环境。

## 架构

### 核心设计
- **环境变量控制**：`UPLOAD_DIR` 环境变量指定上传目录路径
- **本地环境**：设为 `D:\Learning\MyCourse\repos\pic`
- **生产环境**：设为 `/app/pics`

### 文件存储策略
- 生成 UUID 文件名避免冲突：`{uuid}.{ext}`
- 支持类型：PNG、JPEG、GIF
- 文件大小限制：5MB

## 需要修改的文件

### 1. `repos/backend/app/routers/upload_router.py`
- 读取 `UPLOAD_DIR` 环境变量
- 若未设置或无效，使用默认值

### 2. `repos/backend/.env.example`
- 添加 `UPLOAD_DIR` 配置示例

### 3. 本地 `.env`（若存在）
- 设置 `UPLOAD_DIR=D:\Learning\MyCourse\repos\pic`

### 4. `repos/frontend/pics/`
- 前端 pics 目录暂不使用（图片统一由后端管理）

## API

### POST /api/upload
- 权限：仅管理员
- 请求：multipart/form-data，字段名 `file`
- 响应：`{"url": "/pics/{filename}", "filename": "{uuid}.{ext}"}`

## 访问路径

- 上传后返回 `/pics/{filename}`
- Nginx 已配置 `/pics/` 路径指向对应目录

## 数据流

1. 管理员在 RankManage.vue 上传图片
2. 前端 POST 到 `/api/upload`
3. 后端验证权限、类型、大小
4. 保存到 `UPLOAD_DIR/{uuid}.{ext}`
5. 返回访问路径
6. 前端将路径存入 `image_url` 字段