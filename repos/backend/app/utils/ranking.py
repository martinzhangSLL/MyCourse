from datetime import date, timedelta
from fastapi import HTTPException
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import StudentClass, Student, ScoreRecord, TermSetting


def get_week_number(start_date: date, target_date: date) -> int:
    """
    Calculate the week number given a start date and target date.

    Args:
        start_date: The term start date
        target_date: The date to calculate week number for

    Returns:
        Week number (1-indexed)
    """
    delta = (target_date - start_date).days
    return delta // 7 + 1


def get_date_range_for_week(start_date: date, week: int) -> tuple[date, date]:
    """
    Get the start and end date for a given week number.

    Args:
        start_date: The term start date
        week: Week number (1-indexed)

    Returns:
        Tuple of (week_start_date, week_end_date)
    """
    week_start = start_date + ((week - 1) * 7)
    week_end = week_start + 6
    return week_start, week_end


def get_date_range_for_month(year: int, month: int) -> tuple[date, date]:
    """
    Get the start and end date for a given month.

    Args:
        year: Year
        month: Month number (1-12)

    Returns:
        Tuple of (month_start_date, month_end_date)
    """
    month_start = date(year, month, 1)
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    return month_start, month_end


def calculate_score_change(
    db: Session,
    student_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Calculate the score change for a student within a date range.

    Args:
        db: Database session
        student_id: Student ID
        start_date: Start date (inclusive), None means no lower bound
        end_date: End date (inclusive), None means no upper bound

    Returns:
        Total score change (sum of all ScoreRecord values)
    """
    query = db.query(ScoreRecord).filter(ScoreRecord.student_id == student_id)

    if start_date:
        query = query.filter(ScoreRecord.score_at >= start_date)
    if end_date:
        query = query.filter(ScoreRecord.score_at <= end_date)

    records = query.all()
    return sum(record.value for record in records)


def calculate_rankings(
    db: Session,
    class_id: int,
    period: str,
    week: int = None,
    month: str = None
) -> list[dict]:
    """
    Calculate rankings for students in a class.

    Args:
        db: Database session
        class_id: Class ID
        period: "total" | "week" | "month" | "term"
        week: Week number (required for period="week")
        month: Month string in format "YYYY-MM" (required for period="month")

    Returns:
        List of ranking dictionaries with keys: rank, student_id, student_name, student_no, score, change
    """
    # Get term setting for date calculations
    term_setting = db.query(TermSetting).order_by(TermSetting.id.desc()).first()
    if not term_setting:
        return []

    today = date.today()

    # Determine date range based on period
    start_date = None
    end_date = None

    if period == "week":
        if week is None:
            week = get_week_number(term_setting.start_date, today)
        week_start, week_end = get_date_range_for_week(term_setting.start_date, week)
        start_date = week_start
        end_date = week_end
    elif period == "month":
        if month:
            if not re.match(r"^\d{4}-\d{2}$", month):
                raise ValueError("month must be in YYYY-MM format")
            year, month_num = map(int, month.split("-"))
            start_date, end_date = get_date_range_for_month(year, month_num)
        else:
            # Default to current month
            start_date, end_date = get_date_range_for_month(today.year, today.month)
    elif period == "term":
        start_date = term_setting.start_date
        end_date = term_setting.end_date
    # For "total", no date range filter - use all records

    # Get all students in the class
    student_classes = db.query(StudentClass).filter(
        StudentClass.class_id == class_id
    ).all()

    ranking_data = []
    for sc in student_classes:
        student = db.query(Student).filter(Student.id == sc.student_id).first()
        if not student:
            continue

        # Calculate score change for the period
        change = calculate_score_change(db, sc.student_id, start_date, end_date)

        ranking_data.append({
            "student_id": student.id,
            "student_name": student.name,
            "student_no": student.student_no,
            "score": sc.current_score,
            "change": change
        })

    # Sort by current_score descending, then by change descending
    ranking_data.sort(key=lambda x: (x["score"], x["change"]), reverse=True)

    # Add rank
    for i, item in enumerate(ranking_data, start=1):
        item["rank"] = i

    return ranking_data


def generate_ranking_excel(
    class_name: str,
    period: str,
    ranking_data: list[dict]
) -> bytes:
    """
    Generate an Excel file for rankings.

    Args:
        class_name: Name of the class
        period: Period string for the title
        ranking_data: List of ranking dictionaries

    Returns:
        Excel file content as bytes
    """
    from io import BytesIO
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "排名"

    # Headers
    headers = ["排名", "学号", "姓名", "总积分", "本周期变化"]
    ws.append(headers)

    # Data rows
    for item in ranking_data:
        ws.append([
            item["rank"],
            item["student_no"],
            item["student_name"],
            item["score"],
            item["change"]
        ])

    # Auto-adjust column widths
    for col_idx, _ in enumerate(headers, start=1):
        col_letter = chr(64 + col_idx)
        max_length = 0
        for cell in ws[col_letter]:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")
        ws.column_dimensions[col_letter].width = max_length + 2

    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    return excel_bytes.getvalue()
