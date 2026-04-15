"""
FastAPI 依赖注入模块 (Dependencies)

此文件定义了 FastAPI 应用的依赖项（Dependencies），包括：
1. get_db: 数据库会话依赖
2. get_current_user: 当前登录用户依赖

依赖注入是 FastAPI 的核心特性，允许在处理请求时自动调用这些函数
并将其返回值注入到路由处理函数中

执行流程示例：
1. 用户发送请求 GET /api/classes
2. FastAPI 检查路由需要 get_current_user 依赖
3. FastAPI 调用 get_current_user，获取当前用户信息
4. FastAPI 将用户信息注入到路由处理函数的 current_user 参数
5. 路由处理函数使用 current_user 信息进行权限验证
"""

import jwt  # JSON Web Token 库，用于验证 Token
from fastapi import Depends, HTTPException, status  # FastAPI 核心组件
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # HTTP 认证方案
from sqlalchemy.orm import Session  # SQLAlchemy 数据库会话

# 导入应用内部模块
from app.auth import verify_token  # Token 验证函数
from app.database import SessionLocal  # 数据库会话工厂
from app.models.models import Teacher  # 教师模型


# ========== HTTP Bearer 认证方案 ==========

# HTTPBearer 是 FastAPI 提供的 HTTP 认证方案
# 客户端需要在请求头中携带：Authorization: Bearer <token>
# security 是一个 HTTPBearer 实例，用于保护路由
security = HTTPBearer()


# ========== 数据库会话依赖 (get_db) ==========

def get_db():
    """
    数据库会话依赖函数

    创建一个新的数据库会话，提供给路由处理函数使用
    在请求处理完成后自动关闭会话，释放数据库连接

    使用方式：
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items

    执行流程：
    1. 调用 SessionLocal() 创建新会话（Session）
    2. 将会话注入到路由处理函数
    3. 路由处理函数使用会话操作数据库
    4. 请求完成后（无论成功或失败），执行 finally 块
    5. 调用 db.close() 关闭会话，释放连接回连接池

    Returns:
        Session: SQLAlchemy 数据库会话对象
    """
    # Step 1: 创建新的数据库会话
    db = SessionLocal()

    try:
        # Step 2: yield 会话给调用者
        # 这里使用 yield 而不是 return，因为 yield 支持上下文管理
        # 可以确保会话在使用后被正确关闭
        yield db
    finally:
        # Step 3: 请求处理完成后执行（无论成功或失败）
        # 这是防御性编程，确保数据库连接不会泄漏
        db.close()


# ========== 当前用户依赖 (get_current_user) ==========

def get_current_user(
    # Depends() 是 FastAPI 依赖注入的核心
    # 它告诉 FastAPI 这些参数的值来自依赖函数，而不是请求数据

    # credentials 参数来自 security 依赖（HTTPBearer）
    # 它会从请求头中提取 Authorization: Bearer <token>
    credentials: HTTPAuthorizationCredentials = Depends(security),

    # db 参数来自 get_db 依赖，获取数据库会话
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户依赖函数

    从请求头中的 JWT Token 解析出用户信息
    验证 Token 有效后，返回用户的基本信息

    执行流程：
    1. 从请求头提取 Bearer Token
    2. 使用 jwt.verify_token() 验证 Token 签名和有效期
    3. 从 Token payload 中提取 user_id 和 role
    4. 根据 role 查询对应的用户信息
    5. 返回用户信息字典，包含 id, name, role

    参数：
        credentials: HTTP 认证凭据，包含 Token
        db: 数据库会话

    返回：
        dict: 用户信息字典，格式：
            - admin: {"id": 0, "name": "admin", "role": "admin"}
            - teacher: {"id": <teacher_id>, "name": <teacher_name>, "role": "teacher"}

    异常：
        HTTPException 401: Token 无效、过期或用户不存在
    """
    # Step 1: 从认证凭据中提取 Token 字符串
    # credentials.credentials 包含 Token 的实际值（不含 "Bearer " 前缀）
    token = credentials.credentials

    try:
        # Step 2: 验证 Token 的有效性和完整性
        # verify_token() 会：
        # - 检查 Token 签名是否正确（防止篡改）
        # - 检查 Token 是否过期
        # - 解析 Token payload 并返回
        payload = verify_token(token)

        # Step 3: 从 payload 中提取用户信息
        user_id = payload.get("user_id")  # 用户ID
        role = payload.get("role")        # 用户角色：admin 或 teacher

        # Step 4: 验证 Token payload 完整性
        # 如果缺少必要字段，说明 Token 格式不正确
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"  # Token payload 无效
            )

        # Step 5: 根据角色处理不同用户类型
        if role == "teacher":
            # 教师用户：从数据库查询教师信息
            # 注意：user_id 对于教师用户就是 Teacher 表的主键 id
            teacher = db.query(Teacher).filter(Teacher.id == user_id).first()

            # 验证教师是否存在
            if teacher is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"  # 用户不存在
                )

            # 返回教师用户信息
            # 格式：{"id": <教师ID>, "name": <教师姓名>, "role": "teacher"}
            return {"id": teacher.id, "name": teacher.name, "role": "teacher"}

        elif role == "admin":
            # 管理员用户：admin 用户不在数据库中存储
            # admin 是系统内置用户，id 固定为 0
            # 返回管理员信息：{"id": 0, "name": "admin", "role": "admin"}
            return {"id": 0, "name": "admin", "role": "admin"}

        else:
            # 未知角色，拒绝访问
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid role"  # 角色无效
            )

    except jwt.PyJWTError:
        # Token 验证失败（签名错误、过期等）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"  # 无法验证凭据
        )
