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

# 上传目录：从环境变量读取，若未设置则使用默认值
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/pics")
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