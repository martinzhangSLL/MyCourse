"""
JWT Token 认证模块 (Authentication)

此文件负责：
1. 创建 JWT Token（create_access_token）
2. 验证 JWT Token（verify_token）

JWT（JSON Web Token）是一种开放标准（RFC 7519），
用于在各方之间安全地传输信息。
JWT 由三部分组成：Header（头部）、Payload（载荷）、Signature（签名）

架构说明：
- HS256 算法：对称签名算法，使用同一个密钥进行签名和验证
- Token 有效期：24 小时（可配置）
- Token 包含：user_id（用户ID）、role（用户角色）、exp（过期时间）
"""

import os
from datetime import datetime, timedelta  # 日期时间处理

import jwt  # PyJWT 库，用于创建和验证 JWT Token


# ========== JWT 配置 ==========

# JWT 密钥：从环境变量读取
# 警告：生产环境中必须设置此环境变量，否则 Token 可被伪造
# 建议使用：openssl rand -hex 32 生成随机密钥
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    # 如果未设置密钥，启动时抛出错误（强制要求配置）
    raise ValueError("JWT_SECRET_KEY environment variable must be set")

# JWT 签名算法：HS256（HMAC using SHA-256）
# HS256 是对称算法，签名和验证使用相同的密钥
ALGORITHM = "HS256"

# Token 有效期：24 小时（60 分钟/小时 × 24 小时）
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# ========== 创建 Token 函数 ==========

def create_access_token(data: dict) -> str:
    """
    创建 JWT Access Token

    将用户信息（user_id, role）封装到 Token 中，返回给客户端

    执行流程：
    1. 复制传入的 data 字典（避免修改原数据）
    2. 计算过期时间（当前时间 + 有效期）
    3. 将过期时间添加到 data 中
    4. 使用 JWT 库编码，生成 Token 字符串

    参数：
        data: 要包含在 Token 中的数据，必须包含 user_id 和 role
              例如：{"user_id": 1, "role": "teacher"}

    返回：
        str: JWT Token 字符串

    示例：
        token = create_access_token({"user_id": 1, "role": "teacher"})
        # 返回：eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    # Step 1: 复制数据字典，避免修改原数据
    to_encode = data.copy()

    # Step 2: 计算 Token 过期时间
    # datetime.utcnow() 获取当前 UTC 时间
    # timedelta 分钟=有效期
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Step 3: 将过期时间添加到要编码的数据中
    # "exp" 是 JWT 标准中的过期时间字段名
    to_encode.update({"exp": expire})

    # Step 4: 使用 JWT 库编码，生成 Token
    # jwt.encode(payload, secret_key, algorithm)
    # 返回的 Token 是 Base64 编码的字符串
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# ========== 验证 Token 函数 ==========

def verify_token(token: str) -> dict:
    """
    验证 JWT Token 的有效性

    检查 Token 的签名和过期时间，如果有效则返回 Token 的 Payload

    执行流程：
    1. 使用 JWT 库解码 Token
    2. 验证签名是否正确（防止篡改）
    3. 验证 Token 是否过期
    4. 返回 Token 的 Payload（包含用户信息）

    参数：
        token: JWT Token 字符串

    返回：
        dict: Token 的 Payload，包含 user_id, role 等信息

    异常：
        jwt.PyJWTError: Token 无效或已过期（由调用者处理）
    """
    # jwt.decode() 会自动验证：
    # 1. 签名是否正确（SECRET_KEY 是否匹配）
    # 2. Token 是否过期（exp 字段）
    # 如果验证失败，会抛出 jwt.PyJWTError 或其子类
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    return payload
