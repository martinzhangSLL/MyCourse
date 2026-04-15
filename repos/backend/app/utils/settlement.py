"""
结算工具模块 (Settlement Utilities)

此模块提供结算功能的工具函数：

1. generate_settlement_excel(): 生成结算 Excel 文件
   - Sheet1 "排名": 班级学生排名（排名、学号、姓名、当前积分）
   - Sheet2 "明细": 积分明细（学生姓名、学号、分值、原因、课程、操作教师、时间）

结算说明：
- 结算操作只能在学期结束后进行
- 结算生成 Excel 文件，包含排名和明细两个工作表
- 用于存档和对账
"""

from io import BytesIO
from typing import List, Tuple

from openpyxl import Workbook


def generate_settlement_excel(
    class_name: str,
    ranking_data: List[Tuple[int, str, str, int]],
    detail_data: List[Tuple[str, str, int, str, str, str, str]]
) -> bytes:
    """
    生成结算 Excel 文件

    Excel 包含两个工作表：
    1. 排名：班级学生的积分排名
    2. 明细：每条积分记录的详细信息

    参数：
        class_name: 班级名称
        ranking_data: 排名数据列表
            - 每项为 (排名, 学号, 姓名, 当前积分) 的元组
            - 示例：[(1, "2025001", "张三", 100), (2, "2025002", "李四", 90)]
        detail_data: 明细数据列表
            - 每项为 (学生姓名, 学号, 分值, 原因, 课程, 操作教师, 时间) 的元组
            - 示例：[("张三", "2025001", 10, "考试", "数学", "王老师", "2025-01-15")]

    返回：
        bytes: Excel 文件的字节数据
    """
    # Step 1: 创建工作簿
    wb = Workbook()

    # ========== Sheet1: 排名 ==========

    # 获取活动工作表作为排名表
    ws_ranking = wb.active
    ws_ranking.title = "排名"

    # 写入表头
    ranking_headers = ["排名", "学号", "姓名", "当前积分"]
    ws_ranking.append(ranking_headers)

    # 写入排名数据
    for row in ranking_data:
        ws_ranking.append(row)

    # ========== Sheet2: 明细 ==========

    # 创建新的工作表作为明细表
    ws_detail = wb.create_sheet(title="明细")

    # 写入表头
    detail_headers = ["学生姓名", "学号", "分值", "原因", "课程", "操作教师", "时间"]
    ws_detail.append(detail_headers)

    # 写入明细数据
    for row in detail_data:
        ws_detail.append(row)

    # ========== 保存到 BytesIO ==========

    # 创建内存缓冲区
    buffer = BytesIO()

    # 保存工作簿到缓冲区
    wb.save(buffer)

    # 将指针移到开头，准备被读取
    buffer.seek(0)

    # 返回字节数据
    return buffer.getvalue()
