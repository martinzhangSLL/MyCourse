"""
系统配置路由模块 (Config Router)

此模块处理与系统配置相关的 API 请求：

【积分原因 /api/config/reasons】
1. GET /api/config/reasons - 获取积分原因列表
2. PUT /api/config/reasons - 更新积分原因列表

【确认码 /api/config/codes】
1. GET /api/config/codes - 获取结算码和初始化码
2. PUT /api/config/codes - 更新结算码和初始化码

配置存储：
- 所有配置存储在 Config 表中（Key-Value 格式）
- reasons 存储为 JSON 数组字符串：'["考试","作业","荣誉","其他"]'

安全说明：
- 获取和更新确认码需要管理员权限
- reasons 的 GET 不需要权限（前端页面需要读取）
- reasons 的 PUT 需要管理员权限
"""

import json  # JSON 序列化/反序列化
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 导入数据模型
from app.models.models import Config
# 导入 Pydantic Schema
from app.schemas.config_schema import ReasonsResponse, CodesResponse, CodesUpdate
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user

# 创建路由实例
router = APIRouter(prefix="/api/config", tags=["config"])


# ========== 获取积分原因列表 ==========

@router.get("/reasons", response_model=ReasonsResponse)
def get_reasons(db: Session = Depends(get_db)):
    """
    获取积分原因列表

    积分原因用于教师在给分时选择原因，如"考试"、"作业"等

    执行流程：
    1. 从 Config 表查询 key="reasons" 的配置
    2. 如果不存在，返回空列表
    3. 解析 JSON 字符串为列表
    4. 返回 ReasonsResponse

    参数：
        db: 数据库会话

    返回：
        ReasonsResponse: 包含 reasons 列表
    """
    # Step 1: 查询配置
    config = db.query(Config).filter(
        Config.key == "reasons"
    ).first()

    # Step 2: 如果不存在，返回空列表
    if not config:
        return ReasonsResponse(reasons=[])

    # Step 3: 解析 JSON 字符串
    try:
        reasons = json.loads(config.value)
        # 确保是列表类型
        if not isinstance(reasons, list):
            reasons = []
    except (json.JSONDecodeError, TypeError):
        reasons = []

    # Step 4: 返回结果
    return ReasonsResponse(reasons=reasons)


# ========== 更新积分原因列表 ==========

@router.put("/reasons", response_model=ReasonsResponse)
def update_reasons(
    request: ReasonsResponse,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新积分原因列表（仅管理员可操作）

    执行流程：
    1. 验证当前用户是管理员
    2. 查询现有配置
    3. 如果存在则更新，如果不存在则创建
    4. 将列表序列化为 JSON 字符串存储
    5. 提交事务

    参数：
        request: ReasonsResponse，包含新的 reasons 列表
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ReasonsResponse: 更新后的 reasons 列表

    异常：
        HTTPException 403: 非管理员用户
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 查询现有配置
    config = db.query(Config).filter(
        Config.key == "reasons"
    ).first()

    if config:
        # 配置存在，更新值
        # ensure_ascii=False: 保留中文字符，不转义为 \u...
        config.value = json.dumps(request.reasons, ensure_ascii=False)
    else:
        # 配置不存在，创建新配置
        config = Config(
            key="reasons",
            value=json.dumps(request.reasons, ensure_ascii=False)
        )
        db.add(config)

    # Step 3: 提交事务
    db.commit()

    # Step 4: 返回更新后的结果
    return ReasonsResponse(reasons=request.reasons)


# ========== 获取确认码 ==========

@router.get("/codes", response_model=CodesResponse)
def get_codes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取结算码和初始化码（仅管理员可操作）

    执行流程：
    1. 验证当前用户是管理员
    2. 查询 settlement_code 和 init_code 配置
    3. 返回确认码

    参数：
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        CodesResponse: 包含 settlement_code 和 init_code

    异常：
        HTTPException 403: 非管理员用户
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 查询结算码
    settlement_config = db.query(Config).filter(
        Config.key == "settlement_code"
    ).first()

    # Step 3: 查询初始化码
    init_config = db.query(Config).filter(
        Config.key == "init_code"
    ).first()

    # Step 4: 返回结果
    return CodesResponse(
        settlement_code=settlement_config.value if settlement_config else "",
        init_code=init_config.value if init_config else ""
    )


# ========== 更新确认码 ==========

@router.put("/codes", response_model=CodesResponse)
def update_codes(
    request: CodesUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新结算码和初始化码（仅管理员可操作）

    执行流程：
    1. 验证当前用户是管理员
    2. 查询/更新 settlement_code
    3. 查询/更新 init_code
    4. 提交事务

    参数：
        request: CodesUpdate，包含新的 settlement_code 和 init_code
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        CodesResponse: 更新后的确认码

    异常：
        HTTPException 403: 非管理员用户
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 更新结算码
    settlement_config = db.query(Config).filter(
        Config.key == "settlement_code"
    ).first()

    if settlement_config:
        # 配置存在，更新值
        settlement_config.value = request.settlement_code
    else:
        # 配置不存在，创建新配置
        settlement_config = Config(
            key="settlement_code",
            value=request.settlement_code
        )
        db.add(settlement_config)

    # Step 3: 更新初始化码
    init_config = db.query(Config).filter(
        Config.key == "init_code"
    ).first()

    if init_config:
        init_config.value = request.init_code
    else:
        init_config = Config(
            key="init_code",
            value=request.init_code
        )
        db.add(init_config)

    # Step 4: 提交事务
    db.commit()

    # Step 5: 返回结果
    return CodesResponse(
        settlement_code=request.settlement_code,
        init_code=request.init_code
    )
