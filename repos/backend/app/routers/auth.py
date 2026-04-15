"""
认证路由模块 (Authentication Router)

此模块处理与用户认证相关的 API 请求：

1. POST /api/auth/login - 用户登录
   - 验证用户名和密码
   - 返回 JWT Token

2. GET /api/auth/me - 获取当前用户信息
   - 验证 Token 有效性
   - 返回用户信息

认证流程：
1. 用户提交用户名、密码、角色
2. 后端验证凭证
3. 验证成功后，签发 JWT Token
4. 用户后续请求携带 Token（Authorization: Bearer <token>）

支持的角色：
- admin: 管理员（内置用户，不在数据库中）
- teacher: 教师（存储在数据库的 teacher 表）
"""

from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI 路由组件
from sqlalchemy.orm import Session  # SQLAlchemy 数据库会话

# 导入应用内部模块
from app.auth import create_access_token  # JWT Token 创建函数
from app.models.models import Teacher, Config  # 数据模型
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse  # Pydantic 请求/响应模型
from app.utils.security import verify_password  # 密码验证函数
from app.dependencies import get_current_user, get_db  # 依赖注入函数

# 创建路由实例
# prefix: 所有此路由下的接口都会以 /api/auth 开头
# tags: API 文档中的分组标签，用于组织和分类端点
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ========== 辅助函数 ==========

def get_admin_password(db: Session) -> str:
    """
    从数据库获取管理员密码的哈希值

    管理员密码哈希值存储在 Config 表中，键名为 "admin_password_hash"

    参数：
        db: 数据库会话

    返回：
        str: 管理员密码的 bcrypt 哈希值

    异常：
        HTTPException 500: 如果管理员密码未初始化（系统错误）
    """
    # 查询 Config 表，获取键为 "admin_password_hash" 的配置
    admin_password_config = db.query(Config).filter(
        Config.key == "admin_password_hash"
    ).first()

    # 如果配置存在，返回其哈希值
    if admin_password_config:
        return admin_password_config.value

    # 如果配置不存在，说明系统未正确初始化
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Admin password not initialized"  # 管理员密码未初始化
    )


# ========== 登录接口 ==========

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口

    验证用户凭证（用户名、密码、角色），验证成功后返回 JWT Token

    执行流程：

    【管理员登录】
    1. 检查用户名是否为 "admin"（管理员用户名固定）
    2. 从数据库获取管理员密码哈希
    3. 使用 bcrypt 验证密码
    4. 密码正确则签发 Token（user_id=0, role="admin"）

    【教师登录】
    1. 从数据库查询用户名对应的教师记录
    2. 如果教师不存在，返回认证失败
    3. 使用 bcrypt 验证密码
    4. 密码正确则签发 Token（user_id=<教师ID>, role="teacher"）

    参数：
        request: LoginRequest，包含 username, password, role
        db: 数据库会话（依赖注入）

    返回：
        LoginResponse: 包含 token 和用户信息

    异常：
        HTTPException 401: 用户名或密码错误
        HTTPException 400: 无效的角色
    """
    # 根据角色类型分别处理登录逻辑
    if request.role == "admin":
        # ========== 管理员登录 ==========

        # Step 1: 验证用户名必须是 "admin"
        # 管理员是系统内置用户，用户名固定为 "admin"
        if request.username != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"  # 笼统的错误信息，防止信息泄露
            )

        # Step 2: 获取管理员密码哈希
        admin_password_hash = get_admin_password(db)

        # Step 3: 验证密码是否正确
        # verify_password 使用 bcrypt 自动处理盐值提取和比较
        if not verify_password(request.password, admin_password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Step 4: 创建 JWT Token
        # 管理员的 user_id 固定为 0
        token = create_access_token({"user_id": 0, "role": "admin"})

        # Step 5: 返回登录响应
        return LoginResponse(
            token=token,
            user=UserResponse(id=0, name="admin", role="admin")
        )

    elif request.role == "teacher":
        # ========== 教师登录 ==========

        # Step 1: 查询数据库，获取用户名对应的教师记录
        # 使用 Teacher.name 字段进行查询
        teacher = db.query(Teacher).filter(
            Teacher.name == request.username
        ).first()

        # Step 2: 如果教师不存在，返回认证失败
        # 注意：不要告诉攻击者是"用户不存在"还是"密码错误"
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Step 3: 验证密码是否正确
        if not verify_password(request.password, teacher.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Step 4: 创建 JWT Token
        # 教师的 user_id 就是 Teacher 表的主键 id
        token = create_access_token({"user_id": teacher.id, "role": "teacher"})

        # Step 5: 返回登录响应
        return LoginResponse(
            token=token,
            user=UserResponse(id=teacher.id, name=teacher.name, role="teacher")
        )

    else:
        # ========== 无效角色 ==========
        # 只有 admin 和 teacher 是有效角色
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )


# ========== 获取当前用户接口 ==========

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户的信息

    此接口需要携带有效的 JWT Token
    Token 的验证由 get_current_user 依赖自动完成

    执行流程：
    1. get_current_user 从请求头提取并验证 Token
    2. 解析 Token 获取用户信息
    3. 返回用户信息字典

    参数：
        current_user: 当前用户信息（依赖注入，自动从 Token 解析）

    返回：
        UserResponse: 当前用户的信息
    """
    # current_user 已经由 get_current_user 依赖验证并解析
    # 格式：{"id": <用户ID>, "name": <用户名>, "role": "<角色>"}
    return UserResponse(**current_user)
