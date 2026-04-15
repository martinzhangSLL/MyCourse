"""
结算路由模块 (Settlement Router)

此模块处理与结算和初始化相关的 API 请求：

1. POST /api/settlement - 学期结算
   - 验证确认码
   - 检查学期是否已结束
   - 生成结算 Excel 文件（排名 + 明细）
   - 清空积分记录
   - 重置学生积分为 0

2. POST /api/initialization - 学期初始化
   - 验证确认码
   - 从 Excel 读取学生初始积分
   - 更新学生的 current_score

安全说明：
- 两个接口都需要管理员权限
- 需要输入正确的确认码才能执行操作

确认码：
- settlement_code: 结算确认码，用于验证结算操作
- init_code: 初始化确认码，用于验证初始化操作
"""

from datetime import date
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import load_workbook

# 导入数据模型
from app.models.models import (
    Config,           # 系统配置模型
    TermSetting,      # 学期设置模型
    ScoreRecord,      # 积分记录模型
    StudentClass,     # 学生-班级关联模型
    Student,          # 学生模型
    ClassModel,       # 班级模型
    Course,           # 课程模型
    Teacher,          # 教师模型
)
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user
# 导入结算 Excel 生成工具
from app.utils.settlement import generate_settlement_excel

# 创建路由实例
router = APIRouter(prefix="/api", tags=["settlement"])

# 文件大小限制：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


# ========== 确认码验证辅助函数 ==========

def verify_code(db: Session, code: str, config_key: str) -> None:
    """
    验证确认码是否正确

    用于结算和初始化操作的身份验证

    执行流程：
    1. 从 Config 表查询指定 key 的配置
    2. 比较输入的码与存储的值是否匹配

    参数：
        db: 数据库会话
        code: 用户输入的确认码
        config_key: 配置键名（如 "settlement_code" 或 "init_code"）

    异常：
        HTTPException 400: 确认码错误
    """
    config = db.query(Config).filter(
        Config.key == config_key
    ).first()

    if not config or config.value != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="确认码错误"
        )


# ========== 学期结算接口 ==========

@router.post("/settlement")
def settlement(
    class_id: int = Query(..., description="班级ID"),
    code: str = Query(..., description="结算确认码"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    学期结算接口

    在学期结束后执行，将班级积分清零并生成结算 Excel

    执行流程：
    1. 验证结算确认码
    2. 检查学期是否已结束
    3. 获取班级信息
    4. 构建排名数据
    5. 构建明细数据
    6. 生成结算 Excel
    7. 删除积分记录
    8. 重置学生积分为 0
    9. 返回 Excel 文件流

    参数：
        class_id: 班级 ID（查询参数）
        code: 结算确认码（查询参数）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        StreamingResponse: Excel 文件流，用于下载结算文件

    异常：
        HTTPException 400: 确认码错误或学期未结束
        HTTPException 404: 班级不存在
        HTTPException 500: 结算失败
    """
    # Step 1: 验证确认码
    verify_code(db, code, "settlement_code")

    # Step 2: 检查学期结束日期
    latest_term_setting = db.query(TermSetting).order_by(
        TermSetting.id.desc()
    ).first()

    if not latest_term_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未找到学期设置"
        )

    today = date.today()
    if today < latest_term_setting.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前学期未结束，无法结算"
        )

    # Step 3: 获取班级信息
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    class_name = class_model.name

    # Step 4: 获取班级所有学生
    student_classes = db.query(StudentClass).filter(
        StudentClass.class_id == class_id
    ).all()

    # Step 5: 构建排名数据（按 current_score 降序）
    ranking_data = []
    sorted_students = sorted(
        student_classes,
        key=lambda sc: sc.current_score,
        reverse=True
    )

    for rank, sc in enumerate(sorted_students, start=1):
        student = db.query(Student).filter(
            Student.id == sc.student_id
        ).first()

        if student:
            ranking_data.append((
                rank,                      # 排名
                student.student_no,        # 学号
                student.name,              # 姓名
                sc.current_score           # 当前积分
            ))

    # Step 6: 构建明细数据
    detail_data = []
    score_records = (
        db.query(ScoreRecord)
        .join(Student, ScoreRecord.student_id == Student.id)
        .join(
            StudentClass,
            (ScoreRecord.student_id == StudentClass.student_id) &
            (StudentClass.class_id == class_id)
        )
        .all()
    )

    for record in score_records:
        student = db.query(Student).filter(
            Student.id == record.student_id
        ).first()

        course = db.query(Course).filter(
            Course.id == record.course_id
        ).first()

        teacher = db.query(Teacher).filter(
            Teacher.id == record.teacher_id
        ).first()

        detail_data.append((
            student.name if student else "",
            student.student_no if student else "",
            record.value,
            record.reason or "",
            course.name if course else "",
            teacher.name if teacher else "",
            record.score_at.strftime("%Y-%m-%d %H:%M:%S") if record.score_at else ""
        ))

    # Step 7: 生成 Excel 文件
    excel_bytes = generate_settlement_excel(class_name, ranking_data, detail_data)

    # Step 8: 清空积分记录并重置积分
    try:
        # 删除该班级所有学生的积分记录
        db.query(ScoreRecord).filter(
            ScoreRecord.student_id.in_([sc.student_id for sc in student_classes])
        ).delete(synchronize_session=False)

        # 重置每个学生的积分为 0
        for sc in student_classes:
            sc.current_score = 0

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="结算失败，数据已回滚"
        )

    # Step 9: 返回 Excel 文件下载
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=结算_{class_name}.xlsx"
        }
    )


# ========== 学期初始化接口 ==========

@router.post("/initialization")
def initialization(
    class_id: int = Query(..., description="班级ID"),
    code: str = Query(..., description="初始化确认码"),
    file: UploadFile = File(..., description="Excel文件"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    学期初始化接口

    从 Excel 读取学生初始积分，更新到系统中

    Excel 文件格式：
    - 第一列：学生姓名
    - 第二列：学生学号
    - 第三列：初始积分

    执行流程：
    1. 验证初始化确认码
    2. 验证文件类型
    3. 读取 Excel 文件
    4. 遍历每一行，根据学号查找学生
    5. 更新该学生在指定班级的 current_score
    6. 返回更新数量

    参数：
        class_id: 班级 ID（查询参数）
        code: 初始化确认码（查询参数）
        file: Excel 文件（multipart/form-data）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        dict: 包含 message 和 count（成功更新的学生数量）

    异常：
        HTTPException 400: 确认码错误、文件类型错误、文件过大
        HTTPException 500: 处理失败
    """
    # Step 1: 验证确认码
    verify_code(db, code, "init_code")

    # Step 2: 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传Excel文件"
        )

    # Step 3: 读取并处理 Excel 文件
    try:
        # 读取文件内容
        contents = file.file.read()

        # 检查文件大小
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过5MB限制"
            )

        # 加载 Excel 工作簿
        wb = load_workbook(BytesIO(contents))
        ws = wb.active

        # Step 4: 遍历 Excel 行
        update_count = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            # 跳过空行或格式不正确的行
            if len(row) < 3:
                continue

            name, student_no, init_score = row[0], row[1], row[2]

            if not name or not student_no or init_score is None:
                continue

            # Step 5: 根据学号查找学生
            student = db.query(Student).filter(
                Student.student_no == str(student_no)
            ).first()

            if not student:
                continue

            # Step 6: 查找学生在该班级的关联记录
            student_class = (
                db.query(StudentClass)
                .filter(
                    StudentClass.student_id == student.id,
                    StudentClass.class_id == class_id
                )
                .first()
            )

            if student_class:
                # 更新初始积分
                student_class.current_score = int(init_score)
                update_count += 1

        # Step 7: 提交事务
        db.commit()

        return {"message": f"成功更新{update_count}名学生的积分", "count": update_count}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理Excel文件失败: {str(e)}"
        )
