"""
学期管理路由模块 (Term Router)

此模块处理与学期配置相关的 API 请求：

1. GET /api/config/terms - 获取所有学期列表
2. POST /api/config/terms - 创建新学期
3. PUT /api/config/terms/{term_id} - 更新学期日期
4. DELETE /api/config/terms/{term_id} - 删除学期

数据模型关系：
- Term: 学期表，存储学期基本信息（名称、学年）
- TermSetting: 学期设置表，存储学期时间（开始日期、结束日期）
- 一个 Term 对应一个 TermSetting

用途：
- 用于判断当前是否在学期内
- 用于限制结算操作（只能在学期结束后结算）
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 导入数据模型
from app.models.models import Term, TermSetting
# 导入 Pydantic Schema
from app.schemas.config_schema import TermCreate, TermUpdate, TermResponse
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user

# 创建路由实例
router = APIRouter(prefix="/api/config/terms", tags=["terms"])


# ========== 获取学期列表 ==========

@router.get("", response_model=list[TermResponse])
def get_terms(db: Session = Depends(get_db)):
    """
    获取所有学期列表，包含每个学期的时间设置

    执行流程：
    1. 查询所有学期
    2. 对每个学期，查询对应的 TermSetting
    3. 组装 TermResponse 并返回

    参数：
        db: 数据库会话

    返回：
        List[TermResponse]: 学期列表
    """
    # Step 1: 查询所有学期
    terms = db.query(Term).all()

    # Step 2: 准备结果列表
    result = []

    # Step 3: 遍历每个学期，获取时间设置
    for term in terms:
        # 查询该学期的时间设置
        setting = db.query(TermSetting).filter(
            TermSetting.term_id == term.id
        ).first()

        # 组装响应对象
        # 如果没有时间设置，使用今天的日期作为默认值
        result.append(TermResponse(
            id=term.id,
            name=term.name,
            year=term.year,
            start_date=setting.start_date if setting else date.today(),
            end_date=setting.end_date if setting else date.today()
        ))

    return result


# ========== 创建学期 ==========

@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
def create_term(
    request: TermCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建新学期（仅管理员可操作）

    执行流程：
    1. 验证当前用户是管理员
    2. 创建 Term 记录（学期基本信息）
    3. 创建 TermSetting 记录（学期时间设置）
    4. 提交事务

    参数：
        request: TermCreate，包含 name, year, start_date, end_date
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        TermResponse: 创建的学期信息

    异常：
        HTTPException 403: 非管理员用户
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 创建学期记录
    term = Term(
        name=request.name,
        year=request.year
    )
    db.add(term)
    db.flush()  # 获取学期 ID

    # Step 3: 创建学期时间设置
    term_setting = TermSetting(
        term_id=term.id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    db.add(term_setting)

    # Step 4: 提交事务
    db.commit()

    # Step 5: 返回创建的学期信息
    return TermResponse(
        id=term.id,
        name=term.name,
        year=term.year,
        start_date=request.start_date,
        end_date=request.end_date
    )


# ========== 更新学期 ==========

@router.put("/{term_id}", response_model=TermResponse)
def update_term(
    term_id: int,
    request: TermUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新学期日期（仅管理员可操作）

    注意：只能更新开始和结束日期，不能修改名称和学年

    执行流程：
    1. 验证当前用户是管理员
    2. 查询学期记录
    3. 如果不存在，抛出 404
    4. 查询或创建 TermSetting
    5. 更新日期
    6. 提交事务

    参数：
        term_id: 学期 ID
        request: TermUpdate，包含 start_date, end_date
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        TermResponse: 更新后的学期信息

    异常：
        HTTPException 403: 非管理员用户
        HTTPException 404: 学期不存在
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 查询学期
    term = db.query(Term).filter(Term.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found"
        )

    # Step 3: 查询或创建 TermSetting
    term_setting = db.query(TermSetting).filter(
        TermSetting.term_id == term_id
    ).first()

    if term_setting:
        # 存在则更新日期
        term_setting.start_date = request.start_date
        term_setting.end_date = request.end_date
    else:
        # 不存在则创建
        term_setting = TermSetting(
            term_id=term_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        db.add(term_setting)

    # Step 4: 提交事务
    db.commit()

    # Step 5: 返回更新后的学期信息
    return TermResponse(
        id=term.id,
        name=term.name,
        year=term.year,
        start_date=request.start_date,
        end_date=request.end_date
    )


# ========== 删除学期 ==========

@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除学期（仅管理员可操作）

    注意：会同时删除学期的时间设置（TermSetting）
    不会删除关联的积分记录

    执行流程：
    1. 验证当前用户是管理员
    2. 查询学期记录
    3. 如果不存在，抛出 404
    4. 删除 TermSetting
    5. 删除 Term
    6. 提交事务

    参数：
        term_id: 学期 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        None（HTTP 204）

    异常：
        HTTPException 403: 非管理员用户
        HTTPException 404: 学期不存在
    """
    # Step 1: 验证管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Step 2: 查询学期
    term = db.query(Term).filter(Term.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found"
        )

    # Step 3: 删除 TermSetting（时间设置）
    db.query(TermSetting).filter(
        TermSetting.term_id == term_id
    ).delete()

    # Step 4: 删除 Term
    db.delete(term)

    # Step 5: 提交事务
    db.commit()
