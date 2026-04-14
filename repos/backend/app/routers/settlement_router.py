from datetime import date
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import load_workbook

from app.models.models import Config, TermSetting, ScoreRecord, StudentClass, Student, ClassModel, Course, Teacher
from app.dependencies import get_db
from app.utils.settlement import generate_settlement_excel

router = APIRouter(prefix="/api", tags=["settlement"])


def verify_code(db: Session, code: str, config_key: str) -> None:
    """验证确认码是否正确。"""
    config = db.query(Config).filter(Config.key == config_key).first()
    if not config or config.value != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="确认码错误"
        )


@router.post("/settlement")
def settlement(
    class_id: int = Query(..., description="班级ID"),
    code: str = Query(..., description="结算确认码"),
    db: Session = Depends(get_db)
):
    """
    结算接口：生成结算Excel并清零积分。

    1. 校验确认码
    2. 检查学期是否已结束
    3. 生成结算Excel（含排名和明细两个Sheet）
    4. 逻辑删除该班级所有score_record
    5. 重置student_class.current_score为0
    6. 返回Excel文件流
    """
    # 1. 校验确认码
    verify_code(db, code, "settlement_code")

    # 2. 检查学期结束日期
    latest_term_setting = db.query(TermSetting).order_by(TermSetting.id.desc()).first()
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

    # 获取班级信息
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    class_name = class_model.name

    # 获取该班级的所有学生及其积分
    student_classes = db.query(StudentClass).filter(StudentClass.class_id == class_id).all()

    # 构建排名数据 (排名, 学号, 姓名, 当前积分)
    ranking_data = []
    # 按当前积分降序排列
    sorted_students = sorted(
        student_classes,
        key=lambda sc: sc.current_score,
        reverse=True
    )
    for rank, sc in enumerate(sorted_students, start=1):
        student = db.query(Student).filter(Student.id == sc.student_id).first()
        if student:
            ranking_data.append((rank, student.student_no, student.name, sc.current_score))

    # 构建明细数据 (学生姓名, 学号, 分值, 原因, 课程, 操作教师, 时间)
    detail_data = []
    score_records = (
        db.query(ScoreRecord)
        .join(Student, ScoreRecord.student_id == Student.id)
        .join(StudentClass, (ScoreRecord.student_id == StudentClass.student_id) & (StudentClass.class_id == class_id))
        .all()
    )
    for record in score_records:
        student = db.query(Student).filter(Student.id == record.student_id).first()
        course = db.query(Course).filter(Course.id == record.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == record.teacher_id).first()
        detail_data.append((
            student.name if student else "",
            student.student_no if student else "",
            record.value,
            record.reason or "",
            course.name if course else "",
            teacher.name if teacher else "",
            record.score_at.strftime("%Y-%m-%d %H:%M:%S") if record.score_at else ""
        ))

    # 生成Excel
    excel_bytes = generate_settlement_excel(class_name, ranking_data, detail_data)

    # 4. 逻辑删除该班级所有score_record
    db.query(ScoreRecord).filter(
        ScoreRecord.student_id.in_([sc.student_id for sc in student_classes])
    ).delete(synchronize_session=False)

    # 5. 重置student_class.current_score为0
    for sc in student_classes:
        sc.current_score = 0

    db.commit()

    # 6. 返回Excel文件流
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=结算_{class_name}.xlsx"
        }
    )


@router.post("/initialization")
def initialization(
    class_id: int = Query(..., description="班级ID"),
    code: str = Query(..., description="初始化确认码"),
    file: UploadFile = File(..., description="Excel文件"),
    db: Session = Depends(get_db)
):
    """
    初始化接口：从Excel读取数据重置学生积分。

    1. 校验确认码
    2. 读取上传的Excel（第一列姓名，第二列学号，第三列初始积分）
    3. 在student_class表中查找对应学生，更新current_score为初始积分
    4. 返回更新数量
    """
    # 1. 校验确认码
    verify_code(db, code, "init_code")

    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传Excel文件"
        )

    # 2. 读取Excel
    try:
        contents = file.file.read()
        wb = load_workbook(BytesIO(contents))
        ws = wb.active

        # 跳过表头，从第二行开始读取
        update_count = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) < 3:
                continue
            name, student_no, init_score = row[0], row[1], row[2]
            if not name or not student_no or init_score is None:
                continue

            # 查找学生
            student = db.query(Student).filter(Student.student_no == str(student_no)).first()
            if not student:
                continue

            # 查找student_class记录
            student_class = (
                db.query(StudentClass)
                .filter(StudentClass.student_id == student.id, StudentClass.class_id == class_id)
                .first()
            )
            if student_class:
                student_class.current_score = int(init_score)
                update_count += 1

        db.commit()
        return {"message": f"成功更新{update_count}名学生的积分", "count": update_count}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理Excel文件失败: {str(e)}"
        )
