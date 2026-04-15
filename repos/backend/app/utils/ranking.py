"""
排名计算工具模块 (Ranking Utilities)

此模块提供排名计算的核心功能：

1. 周数计算：
   - get_week_number(): 计算指定日期是第几周
   - get_date_range_for_week(): 获取某周的开始和结束日期
   - get_date_range_for_month(): 获取某月的开始和结束日期

2. 积分变化计算：
   - calculate_score_change(): 计算学生在指定时间范围内的积分变化

3. 排名计算：
   - calculate_rankings(): 计算班级的学生排名

4. Excel 生成：
   - generate_ranking_excel(): 生成排名 Excel 文件
"""

from datetime import date, timedelta
from fastapi import HTTPException
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import StudentClass, Student, ScoreRecord, TermSetting


# ========== 周数计算函数 ==========

def get_week_number(start_date: date, target_date: date) -> int:
    """
    计算目标日期是第几周（从开始日期算起）

    算法：计算两个日期的天数差，除以 7 向下取整后加 1

    参数：
        start_date: 开始日期（如学期开始日期）
        target_date: 目标日期

    返回：
        int: 周数（从 1 开始）
    """
    # 计算天数差
    delta = (target_date - start_date).days
    # 除以 7 取整后加 1（周数从 1 开始）
    return delta // 7 + 1


def get_date_range_for_week(start_date: date, week: int) -> tuple[date, date]:
    """
    获取指定周的开始和结束日期

    参数：
        start_date: 学期开始日期
        week: 周数（从 1 开始）

    返回：
        Tuple[date, date]: (该周开始日期, 该周结束日期)
    """
    # 计算该周的开始日期
    # 第 1 周的开始日期就是 start_date
    # 第 2 周的开始日期是 start_date + 7 天
    week_start = start_date + ((week - 1) * 7)

    # 该周结束日期 = 开始日期 + 6 天（一周 7 天）
    week_end = week_start + 6

    return week_start, week_end


def get_date_range_for_month(year: int, month: int) -> tuple[date, date]:
    """
    获取指定月份的开始和结束日期

    参数：
        year: 年份
        month: 月份（1-12）

    返回：
        Tuple[date, date]: (该月第一天, 该月最后一天)
    """
    # 该月第一天
    month_start = date(year, month, 1)

    # 计算下月第一天
    if month == 12:
        # 12 月的下月是次年 1 月
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)

    # 该月最后一天 = 下月第一天 - 1 天
    month_end = next_month_start - timedelta(days=1)

    return month_start, month_end


# ========== 积分变化计算 ==========

def calculate_score_change(
    db: Session,
    student_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    计算学生在指定时间范围内的积分变化

    通过查询 ScoreRecord 表，筛选指定时间范围内的记录，
    累加所有记录的 value（正数加分，负数扣分）

    参数：
        db: 数据库会话
        student_id: 学生 ID
        start_date: 开始日期（可选，None 表示不限制下限）
        end_date: 结束日期（可选，None 表示不限制上限）

    返回：
        int: 该时间范围内的积分变化总和
    """
    # 构建基础查询：筛选该学生的所有积分记录
    query = db.query(ScoreRecord).filter(
        ScoreRecord.student_id == student_id
    )

    # 添加开始日期筛选
    if start_date:
        query = query.filter(ScoreRecord.score_at >= start_date)

    # 添加结束日期筛选
    if end_date:
        query = query.filter(ScoreRecord.score_at <= end_date)

    # 执行查询，获取所有记录
    records = query.all()

    # 累加所有积分值
    return sum(record.value for record in records)


# ========== 排名计算 ==========

def calculate_rankings(
    db: Session,
    class_id: int,
    period: str,
    week: int = None,
    month: str = None
) -> list[dict]:
    """
    计算班级的学生排名

    支持多种排名周期：
    - total: 基于 current_score 排序，change 为所有加减分总和
    - week: 只统计选定周内的加减分
    - month: 只统计选定月内的加减分
    - term: 只统计本学期内的加减分

    执行流程：
    1. 获取学期设置（用于计算日期范围）
    2. 根据 period 计算日期范围
    3. 获取班级所有学生
    4. 对每个学生，计算积分变化
    5. 按 current_score 降序排序
    6. 添加排名号

    参数：
        db: 数据库会话
        class_id: 班级 ID
        period: 排名周期（total/week/month/term）
        week: 周数（period=week 时使用）
        month: 月份字符串（period=month 时使用，格式 YYYY-MM）

    返回：
        List[dict]: 排名列表，每项包含：
        - rank: 排名（从 1 开始）
        - student_id: 学生 ID
        - student_name: 学生姓名
        - student_no: 学号
        - score: 当前积分
        - change: 本周期积分变化
    """
    # Step 1: 获取学期设置
    term_setting = db.query(TermSetting).order_by(
        TermSetting.id.desc()
    ).first()

    if not term_setting:
        return []

    today = date.today()

    # Step 2: 根据 period 计算日期范围
    start_date = None
    end_date = None

    if period == "week":
        # 周排名：计算指定周或当前周的日期范围
        if week is None:
            # 如果未指定周，默认使用当前周
            week = get_week_number(term_setting.start_date, today)

        week_start, week_end = get_date_range_for_week(term_setting.start_date, week)
        start_date = week_start
        end_date = week_end

    elif period == "month":
        # 月排名：计算指定月或当前月的日期范围
        if month:
            # 验证月份格式：YYYY-MM
            if not re.match(r"^\d{4}-\d{2}$", month):
                raise ValueError("month must be in YYYY-MM format")

            # 解析年份和月份
            year, month_num = map(int, month.split("-"))
            start_date, end_date = get_date_range_for_month(year, month_num)
        else:
            # 默认当前月
            start_date, end_date = get_date_range_for_month(today.year, today.month)

    elif period == "term":
        # 学期排名：使用学期的开始和结束日期
        start_date = term_setting.start_date
        end_date = term_setting.end_date

    # 对于 "total"，不设置日期范围，使用所有历史记录

    # Step 3: 获取班级所有学生
    student_classes = db.query(StudentClass).filter(
        StudentClass.class_id == class_id
    ).all()

    # Step 4: 计算每个学生的排名数据
    ranking_data = []
    for sc in student_classes:
        # 获取学生信息
        student = db.query(Student).filter(
            Student.id == sc.student_id
        ).first()

        if not student:
            continue

        # 计算该学生在指定时间范围内的积分变化
        change = calculate_score_change(
            db, sc.student_id, start_date, end_date
        )

        # 添加到排名数据
        ranking_data.append({
            "student_id": student.id,
            "student_name": student.name,
            "student_no": student.student_no,
            "score": sc.current_score,  # 当前总积分
            "change": change            # 本周期变化
        })

    # Step 5: 排序
    # 按 current_score 降序，再按 change 降序
    ranking_data.sort(key=lambda x: (x["score"], x["change"]), reverse=True)

    # Step 6: 添加排名号
    for i, item in enumerate(ranking_data, start=1):
        item["rank"] = i

    return ranking_data


# ========== Excel 生成 ==========

def generate_ranking_excel(
    class_name: str,
    period: str,
    ranking_data: list[dict]
) -> bytes:
    """
    生成排名 Excel 文件

    参数：
        class_name: 班级名称（用于文件名）
        period: 周期描述（用于文件名）
        ranking_data: 排名数据列表

    返回：
        bytes: Excel 文件的字节数据
    """
    from io import BytesIO
    from openpyxl import Workbook

    # Step 1: 创建工作簿
    wb = Workbook()

    # Step 2: 获取活动工作表
    ws = wb.active
    ws.title = "排名"

    # Step 3: 写入表头
    headers = ["排名", "学号", "姓名", "总积分", "本周期变化"]
    ws.append(headers)

    # Step 4: 写入数据行
    for item in ranking_data:
        ws.append([
            item["rank"],
            item["student_no"],
            item["student_name"],
            item["score"],
            item["change"]
        ])

    # Step 5: 自动调整列宽
    for col_idx, _ in enumerate(headers, start=1):
        col_letter = chr(64 + col_idx)  # A, B, C, D, E
        max_length = 0

        # 遍历该列所有单元格，找出最大长度
        for cell in ws[col_letter]:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Excel generation failed: {str(e)}"
                )

        # 设置列宽（最大长度 + 2）
        ws.column_dimensions[col_letter].width = max_length + 2

    # Step 6: 保存到 BytesIO
    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)

    return excel_bytes.getvalue()
