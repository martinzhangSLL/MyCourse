from io import BytesIO
from typing import List, Tuple

from openpyxl import Workbook


def generate_settlement_excel(
    class_name: str,
    ranking_data: List[Tuple[int, str, str, int]],
    detail_data: List[Tuple[str, str, int, str, str, str, str]]
) -> bytes:
    """
    生成结算 Excel，返回字节数据。

    Args:
        class_name: 班级名称
        ranking_data: 排名数据列表，每项为 (排名, 学号, 姓名, 当前积分)
        detail_data: 明细数据列表，每项为 (学生姓名, 学号, 分值, 原因, 课程, 操作教师, 时间)

    Returns:
        Excel 文件的字节数据
    """
    wb = Workbook()

    # Sheet1: 排名
    ws_ranking = wb.active
    ws_ranking.title = "排名"

    # 表头
    ranking_headers = ["排名", "学号", "姓名", "当前积分"]
    ws_ranking.append(ranking_headers)

    # 数据
    for row in ranking_data:
        ws_ranking.append(row)

    # Sheet2: 明细
    ws_detail = wb.create_sheet(title="明细")

    # 表头
    detail_headers = ["学生姓名", "学号", "分值", "原因", "课程", "操作教师", "时间"]
    ws_detail.append(detail_headers)

    # 数据
    for row in detail_data:
        ws_detail.append(row)

    # 写入到 BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
