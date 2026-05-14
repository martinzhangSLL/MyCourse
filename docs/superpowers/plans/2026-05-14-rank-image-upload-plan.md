# 境界图片上传功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为管理员提供境界图片上传功能，图片持久化存储在宿主机目录中

**Architecture:** 图片上传到后端 `/app/pics/` 目录，通过 Nginx 静态文件服务对外提供访问

**Tech Stack:** FastAPI + Python + Vue + Element Plus + Docker

---

## Task 1: 后端图片上传接口

**Files:**
- Create: `repos/backend/app/routers/upload_router.py`
- Modify: `repos/backend/app/main.py:195` (添加 router 注册)

- [ ] **Step 1: 创建 upload_router.py**

```python
"""
图片上传路由模块 (Upload Router)

此模块处理图片上传相关请求：
1. POST /api/upload - 上传图片文件

权限：仅管理员可访问
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from app.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["upload"])

# 上传目录
UPLOAD_DIR = "/app/pics"
ALLOWED_TYPES = ["image/png", "image/jpeg", "image/gif"]
MAX_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """上传图片文件"""
    # 权限检查：仅管理员可上传
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # 验证文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。仅允许: {', '.join(ALLOWED_TYPES)}"
        )

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制 (最大 5MB)"
        )

    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 生成唯一文件名：UUID + 原始扩展名
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 写入文件
    with open(filepath, "wb") as f:
        f.write(content)

    # 返回访问路径
    return {
        "url": f"/pics/{filename}",
        "filename": filename
    }
```

- [ ] **Step 2: 在 main.py 中注册 router**

在 `repos/backend/app/main.py` 第 195 行后添加：

```python
from app.routers.upload_router import router as upload_router
# ...
app.include_router(upload_router)
```

- [ ] **Step 3: 验证接口可用**

```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@test.png"
```

---

## Task 2: 前端上传组件

**Files:**
- Modify: `repos/frontend/src/views/admin/RankManage.vue`

- [ ] **Step 1: 添加 el-upload 组件**

在对话框的"图片路径"表单项中添加上传按钮：

```html
<el-form-item label="图片路径">
  <div class="upload-row">
    <el-input v-model="form.image_url" placeholder="/pics/xxx.png" style="flex: 1" />
    <el-upload
      action="/api/upload"
      :headers="{ Authorization: token }"
      :show-file-list="false"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      accept="image/png,image/jpeg,image/gif"
    >
      <el-button type="primary" plain>上传图片</el-button>
    </el-upload>
  </div>
  <div class="image-preview" v-if="form.image_url">
    <img :src="form.image_url" alt="预览" />
  </div>
</el-form-item>
```

- [ ] **Step 2: 添加样式**

```css
.upload-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.image-preview {
  margin-top: 10px;
}
.image-preview img {
  max-width: 100px;
  max-height: 100px;
  border-radius: 8px;
}
```

- [ ] **Step 3: 添加 token 获取和方法**

在 script 中添加：
```js
const token = localStorage.getItem('token')

function handleUploadSuccess(response) {
  form.image_url = response.url
  ElMessage.success('上传成功')
}

function handleUploadError() {
  ElMessage.error('上传失败')
}
```

---

## Task 3: Docker 配置更新

**Files:**
- Modify: `deploy/docker-compose.yml`
- Modify: `deploy/nginx/nginx.conf`

- [ ] **Step 1: 修改 docker-compose.yml**

将 `pics-data` 命名卷改为 host 目录绑定：

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

- [ ] **Step 2: 修改 nginx.conf**

在 `deploy/nginx/nginx.conf` 的 `server` 块中添加：

```nginx
location /pics/ {
    alias /usr/share/nginx/html/pics/;
    autoindex off;
    add_header Cache-Control "public, max-age=31536000";
}
```

---

## Task 4: 测试验证

- [ ] **Step 1: 测试后端上传接口**

```bash
# 获取 admin token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'

# 上传图片
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@repos/frontend/pics/1.png"
```

- [ ] **Step 2: 测试前端上传组件**
- 登录管理员账号
- 进入段位管理页面
- 点击"新增段位"或"编辑"
- 测试上传图片功能
- 验证图片 URL 回填和预览

- [ ] **Step 3: 验证 Nginx 静态文件服务**

```bash
# 测试图片访问
curl -I http://localhost/pics/xxx.png
```

---

## 完成标准

1. 后端 `POST /api/upload` 接口正常工作
2. 前端段位管理对话框中有图片上传功能
3. 上传成功后的 URL 自动填充到表单
4. 图片可以通过 `/pics/` 路径访问
5. docker-compose.yml 配置 host 目录挂载