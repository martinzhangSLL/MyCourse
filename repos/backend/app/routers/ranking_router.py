from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.models import ClassModel, TermSetting
from app.utils.ranking import calculate_rankings, generate_ranking_excel
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


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
    获取班级排名列表。

    - total: 基于current_score排序，change为所有加减分总和
    - week: 只统计选定周内的加减分
    - month: 只统计选定月内的加减分
    - term: 只统计本学期内的加减分
    """
    # Validate period
    if period not in ("total", "week", "month", "term"):
        raise HTTPException(
            status_code=400,
            detail="period must be one of: total, week, month, term"
        )

    # Validate class exists
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=404,
            detail="班级不存在"
        )

    # Validate week/month requirements
    if period == "week" and week is None:
        raise HTTPException(
            status_code=400,
            detail="week parameter is required when period=week"
        )

    if period == "month" and month is None:
        raise HTTPException(
            status_code=400,
            detail="month parameter is required when period=month"
        )

    # Get rankings
    rankings = calculate_rankings(db, class_id, period, week, month)

    return rankings


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
    导出班级排名Excel文件。
    """
    # Validate class exists
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=404,
            detail="班级不存在"
        )

    # Get rankings
    rankings = calculate_rankings(db, class_id, period, week, month)

    # Generate Excel
    period_label = {
        "total": "总排名",
        "week": f"第{week}周" if week else "周排名",
        "month": month or "月排名",
        "term": "学期排名"
    }.get(period, "排名")

    excel_bytes = generate_ranking_excel(class_model.name, period_label, rankings)

    filename = f"{class_model.name}_{period_label}.xlsx"

    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


@router.get("/weeks")
def get_available_weeks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前学期可用的周数列表。
    """
    term_setting = db.query(TermSetting).order_by(TermSetting.id.desc()).first()
    if not term_setting:
        return {"weeks": [], "term_start": None, "term_end": None}

    today = date.today()
    total_weeks = get_week_count(term_setting.start_date, term_setting.end_date)
    current_week = get_week_number(term_setting.start_date, today)

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


def get_week_count(start_date: date, end_date: date) -> int:
    """Calculate total number of weeks between two dates."""
    delta = (end_date - start_date).days
    return delta // 7 + 1


def get_week_number(start_date: date, target_date: date) -> int:
    """Calculate the week number given a start date and target date."""
    delta = (target_date - start_date).days
    return delta // 7 + 1
