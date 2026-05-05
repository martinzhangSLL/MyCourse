"""
排名路由模块 (Ranking Router)

此模块处理与班级排名相关的 API 请求：

1. GET /api/rankings - 获取班级排名列表
2. GET /api/rankings/export - 导出班级排名 Excel
3. GET /api/rankings/weeks - 获取当前学期可用周数

排名周期说明：
- total: 总排名，基于 current_score 排序
- week: 周排名，只统计指定周内的积分变化
- month: 月排名，只统计指定月内的积分变化
- term: 学期排名，只统计本学期内的积分变化

数据来源：
- 排名基于 StudentClass.current_score（学生当前积分）
- 周期变化基于 ScoreRecord 表的实时计算
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# 导入数据模型
from app.models.models import ClassModel, TermSetting, TeacherClass
# 导入排名计算工具
from app.utils.ranking import calculate_rankings, generate_ranking_excel
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user

# 创建路由实例
router = APIRouter(prefix="/api/rankings", tags=["rankings"])


# ========== 获取排名列表 ==========

@router.get("")
def get_rankings(
    class_id: int = Query(..., description="班级ID"),
    period: str = Query(..., description="排名周期: total|week|month|term"),
    week: Optional[int] = Query(None, description="周数（period=week时必填）"),
    month: Optional[str] = Query(None, description="月份（period=month时必填，格式YYYY-MM）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取班级排名列表

    排名周期说明：
    - total: 总排名，按 current_score 降序排列
    - week: 周排名，只统计指定周的积分变化
    - month: 月排名，只统计指定月的积分变化
    - term: 学期排名，只统计本学期的积分变化

    执行流程：
    1. 验证 period 参数合法性
    2. 验证班级存在
    3. 验证 week/month 参数（根据 period）
    4. 调用 calculate_rankings 计算排名
    5. 返回排名列表

    参数：
        class_id: 班级 ID
        period: 排名周期（total/week/month/term）
        week: 周数（period=week 时必填）
        month: 月份（period=month 时必填，格式 YYYY-MM）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        List[dict]: 排名列表，每项包含 rank, student_id, student_name, student_no, score, change

    异常：
        HTTPException 400: period 不合法或缺少必要参数
        HTTPException 404: 班级不存在
    """
    # Step 1: 验证 period 参数
    if period not in ("total", "week", "month", "term"):
        raise HTTPException(
            status_code=400,
            detail="period must be one of: total, week, month, term"
        )

    # Step 2: 验证班级存在
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=404,
            detail="班级不存在"
        )

    # Step 3: 验证 week 参数（week 周期必填）
    if period == "week" and week is None:
        raise HTTPException(
            status_code=400,
            detail="week parameter is required when period=week"
        )

    # Step 4: 验证 month 参数（month 周期必填）
    if period == "month" and month is None:
        raise HTTPException(
            status_code=400,
            detail="month parameter is required when period=month"
        )

    # Step 5: 计算排名
    rankings = calculate_rankings(db, class_id, period, week, month)

    return rankings


# ========== 导出排名 Excel ==========

@router.get("/export")
def export_rankings(
    class_id: int = Query(..., description="班级ID"),
    period: str = Query("total", description="排名周期: total|week|month|term"),
    week: Optional[int] = Query(None, description="周数（period=week时必填）"),
    month: Optional[str] = Query(None, description="月份（period=month时必填，格式YYYY-MM）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    导出班级排名 Excel 文件

    Excel 包含一个工作表：
    - 排名：排名、学号、姓名、总积分、本周期变化

    执行流程：
    1. 验证班级存在
    2. 计算排名
    3. 生成 Excel 字节数据
    4. 返回文件下载响应

    参数：
        class_id: 班级 ID
        period: 排名周期
        week: 周数（可选）
        month: 月份（可选）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        StreamingResponse: Excel 文件流
    """
    # Step 1: 验证班级存在
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=404,
            detail="班级不存在"
        )

    # Step 2: 计算排名
    rankings = calculate_rankings(db, class_id, period, week, month)

    # Step 3: 生成 Excel 文件
    period_label = {
        "total": "总排名",
        "week": f"第{week}周" if week else "周排名",
        "month": month or "月排名",
        "term": "学期排名"
    }.get(period, "排名")

    excel_bytes = generate_ranking_excel(class_model.name, period_label, rankings)

    # Step 4: 返回文件下载
    filename = f"{class_model.name}_{period_label}.xlsx"

    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


# ========== 获取可用周数 ==========

@router.get("/weeks")
def get_available_weeks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前学期可用的周数列表

    用于前端下拉框选择周数

    执行流程：
    1. 获取最新的学期设置
    2. 计算当前是第几周
    3. 生成周数列表

    返回：
        dict: 包含 weeks（周数列表）、term_start、term_end、current_week
    """
    # Step 1: 获取学期设置
    term_setting = db.query(TermSetting).order_by(
        TermSetting.id.desc()
    ).first()

    if not term_setting:
        return {"weeks": [], "term_start": None, "term_end": None}

    # Step 2: 计算当前日期
    today = date.today()

    # Step 3: 计算总周数和当前周
    total_weeks = get_week_count(term_setting.start_date, term_setting.end_date)
    current_week = get_week_number(term_setting.start_date, today)

    # Step 4: 生成周数列表
    weeks = [
        {"week": i, "label": f"第{i}周", "is_current": i == current_week}
        for i in range(1, total_weeks + 1)
    ]

    return {
        "weeks": weeks,
        "term_start": term_setting.start_date.isoformat(),
        "term_end": term_setting.end_date.isoformat(),
        "current_week": current_week
    }


# ========== 辅助函数 ==========

def get_week_count(start_date: date, end_date: date) -> int:
    """
    计算两个日期之间的总周数

    参数：
        start_date: 开始日期
        end_date: 结束日期

    返回：
        int: 周数
    """
    delta = (end_date - start_date).days
    return delta // 7 + 1


def get_week_number(start_date: date, target_date: date) -> int:
    """
    计算目标日期是第几周（从开始日期算起）

    参数：
        start_date: 开始日期（如学期开始）
        target_date: 目标日期

    返回：
        int: 周数（从 1 开始）
    """
    delta = (target_date - start_date).days
    return delta // 7 + 1


# ========== 获取可访问的班级列表 ==========

@router.get("/classes")
def get_rankings_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户可访问的班级列表

    - admin: 返回所有班级
    - teacher: 返回仅关联的班级

    返回：
        List[ClassBasic]: 班级基本信息列表
    """
    from app.schemas.class_schema import ClassBasic
    from app.models.models import TeacherClass

    role = current_user.get("role")

    if role == "admin":
        classes = db.query(ClassModel).all()
    elif role == "teacher":
        teacher_id = current_user["id"]
        teacher_classes = db.query(TeacherClass).filter(
            TeacherClass.teacher_id == teacher_id
        ).all()
        class_ids = [tc.class_id for tc in teacher_classes]
        classes = db.query(ClassModel).filter(
            ClassModel.id.in_(class_ids)
        ).all()
    else:
        # 未知角色返回空列表，符合最小权限原则
        return []

    return [
        ClassBasic(id=c.id, name=c.name, code=c.code)
        for c in classes
    ]
