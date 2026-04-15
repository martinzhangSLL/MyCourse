"""
学生管理路由模块 (Student Management Router)

此模块处理与学生管理相关的 API 请求：

1. GET /api/students - 获取学生列表
2. POST /api/students - 创建新学生
3. GET /api/students/template - 下载学生导入模板
4. POST /api/students/import - 批量导入学生
5. PUT /api/students/{student_id} - 更新学生信息
6. DELETE /api/students/{student_id} - 删除学生

数据模型关系：
- 学生与班级：多对多关系（通过 StudentClass 关联表）
- 学生与积分记录：一对多关系（一个学生可以有多条积分记录）

特殊说明：
- 学生的当前积分（current_score）存储在 StudentClass 关联表中
- 因为一个学生可能在不同班级有不同积分
- 导入学生只能导入到未激活的班级
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse  # 用于文件下载
from sqlalchemy.orm import Session  # SQLAlchemy 数据库会话
from io import BytesIO  # 内存文件对象

# 导入依赖注入函数
from app.dependencies import get_db, get_current_user
# 导入数据模型
from app.models.models import Student, StudentClass, ClassModel
# 导入 Pydantic Schema
from app.schemas.student_schema import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentImportResponse,
)
# 导入 Excel 工具函数
from app.utils.excel import read_student_import, create_student_template

# 创建路由实例
router = APIRouter(prefix="/api/students", tags=["students"])

# 文件大小限制：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


# ========== 下载导入模板 ==========

@router.get("/template")
def download_template(current_user: dict = Depends(get_current_user)):
    """
    下载学生信息导入模板

    返回一个 Excel 文件，包含示例数据行
    用户可以下载模板，填写学生信息后上传导入

    执行流程：
    1. 调用 create_student_template() 生成 Excel 文件字节数据
    2. 将字节数据包装为 BytesIO 对象
    3. 使用 StreamingResponse 返回文件下载

    参数：
        current_user: 当前登录用户（依赖注入）

    返回：
        StreamingResponse: Excel 文件流，用于文件下载
    """
    # Step 1: 生成模板文件字节数据
    template_bytes = create_student_template()

    # Step 2: 返回文件下载响应
    # media_type: Excel 文件的 MIME 类型
    # Content-Disposition: 指示浏览器下载文件，filename 指定保存的文件名
    return StreamingResponse(
        BytesIO(template_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=student_import_template.xlsx"
        },
    )


# ========== 获取学生列表 ==========

@router.get("", response_model=list[StudentResponse])
def list_students(
    class_id: int | None = None,  # 可选：按班级筛选
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取学生列表

    支持按班级筛选，返回该班级的学生及其当前积分

    执行流程：

    【按班级筛选】
    1. 连接 Student 和 StudentClass 表
    2. 筛选指定班级的学生
    3. 从 StudentClass 获取 current_score

    【获取全部学生】
    1. 直接查询 Student 表
    2. 返回所有学生，积分统一为 0

    参数：
        class_id: 可选，班级 ID，用于筛选该班级的学生
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        List[StudentResponse]: 学生列表
    """
    if class_id is not None:
        # ========== 按班级筛选 ==========

        # Step 1: 连接查询 Student 和 StudentClass
        # 同时获取学生信息和该学生在此班级的当前积分
        query = (
            db.query(Student, StudentClass.current_score)
            .join(StudentClass, Student.id == StudentClass.student_id)
            .filter(StudentClass.class_id == class_id)
        )

        # Step 2: 执行查询
        results = query.all()

        # Step 3: 转换为响应格式
        return [
            StudentResponse(
                id=student.id,
                name=student.name,
                student_no=student.student_no,
                current_score=current_score,
            )
            for student, current_score in results
        ]

    else:
        # ========== 获取全部学生 ==========

        # Step 1: 查询所有学生
        students = db.query(Student).all()

        # Step 2: 转换为响应格式
        # 注意：没有关联班级时，积分显示为 0
        return [
            StudentResponse(
                id=s.id,
                name=s.name,
                student_no=s.student_no,
                current_score=0,
            )
            for s in students
        ]


# ========== 创建学生 ==========

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    创建新学生

    创建一个新学生并关联到指定班级

    执行流程：
    1. 验证班级存在
    2. 验证学号唯一（不能与已存在学生重复）
    3. 创建学生记录
    4. 创建学生-班级关联记录（默认积分 0，未激活）
    5. 提交事务

    参数：
        student_data: StudentCreate，包含 name, student_no, class_id
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        StudentResponse: 新创建的学生信息

    异常：
        HTTPException 404: 班级不存在
        HTTPException 400: 学号已存在
    """
    # Step 1: 验证班级存在
    class_model = db.query(ClassModel).filter(
        ClassModel.id == student_data.class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # Step 2: 检查学号唯一性
    existing_student = (
        db.query(Student)
        .filter(Student.student_no == student_data.student_no)
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this student number already exists",
        )

    # Step 3: 创建学生记录
    student = Student(
        name=student_data.name,
        student_no=student_data.student_no,
    )
    db.add(student)
    db.flush()  # 刷新以获取学生 ID

    # Step 4: 创建学生-班级关联
    # 新学生的积分从 0 开始，默认未激活
    student_class = StudentClass(
        student_id=student.id,
        class_id=student_data.class_id,
        is_active=False,  # 新学生默认未激活
        current_score=0,  # 初始积分为 0
    )
    db.add(student_class)

    # Step 5: 提交事务
    db.commit()
    db.refresh(student)

    # Step 6: 返回创建的学生信息
    return StudentResponse(
        id=student.id,
        name=student.name,
        student_no=student.student_no,
        current_score=0,
    )


# ========== 批量导入学生 ==========

@router.post("/import", response_model=StudentImportResponse)
async def import_students(
    file: UploadFile = File(...),  # 上传的 Excel 文件
    class_id: int = Form(...),    # 导入到的班级 ID
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    批量导入学生

    从 Excel 文件读取学生数据，批量创建学生并关联到指定班级

    限制：
    - 只能导入到未激活的班级（防止已激活班级数据被篡改）
    - 文件大小限制 5MB
    - Excel 文件必须包含 "学生姓名" 和 "学生学号" 两列

    执行流程：
    1. 验证班级存在且未激活
    2. 读取并验证 Excel 文件
    3. 遍历每一行数据：
       - 如果学生已存在，关联到班级
       - 如果学生不存在，创建新学生并关联
    4. 提交事务

    参数：
        file: 上传的 Excel 文件（multipart/form-data）
        class_id: 目标班级 ID（form data）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        StudentImportResponse: 导入结果，包含成功导入的学生数量

    异常：
        HTTPException 400: 班级已激活、文件过大、文件格式错误、无数据
    """
    # Step 1: 验证班级存在且未激活
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if class_model.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot import students to an activated class",
        )

    # Step 2: 读取 Excel 文件
    file_content = await file.read()

    # Step 3: 检查文件大小
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过5MB限制"
        )

    # Step 4: 解析 Excel 数据
    try:
        students_data = read_student_import(file_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Step 5: 验证数据非空
    if not students_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No student data found in Excel file",
        )

    # Step 6: 批量导入学生
    imported_count = 0

    for name, student_no in students_data:
        # Step 6a: 检查学号是否已存在
        existing_student = (
            db.query(Student)
            .filter(Student.student_no == student_no)
            .first()
        )

        if existing_student:
            # 学生已存在：关联到班级（如果尚未关联）
            existing_association = (
                db.query(StudentClass)
                .filter(
                    StudentClass.student_id == existing_student.id,
                    StudentClass.class_id == class_id,
                )
                .first()
            )

            if not existing_association:
                # 创建关联记录
                student_class = StudentClass(
                    student_id=existing_student.id,
                    class_id=class_id,
                    is_active=False,
                    current_score=0,
                )
                db.add(student_class)
                imported_count += 1

        else:
            # 学生不存在：创建新学生
            new_student = Student(
                name=name,
                student_no=student_no,
            )
            db.add(new_student)
            db.flush()  # 获取新学生 ID

            # 创建关联记录
            student_class = StudentClass(
                student_id=new_student.id,
                class_id=class_id,
                is_active=False,
                current_score=0,
            )
            db.add(student_class)
            imported_count += 1

    # Step 7: 提交事务
    db.commit()

    # Step 8: 返回导入结果
    return StudentImportResponse(
        imported=imported_count,
        message=f"Successfully imported {imported_count} students",
    )


# ========== 更新学生 ==========

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    更新学生信息

    可更新姓名和学号

    执行流程：
    1. 获取学生记录
    2. 更新姓名（如果提供）
    3. 更新学号（如果提供，需检查唯一性）
    4. 提交事务
    5. 获取该学生的当前积分并返回

    参数：
        student_id: 学生 ID
        student_data: StudentUpdate，包含要更新的字段
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        StudentResponse: 更新后的学生信息

    异常：
        HTTPException 404: 学生不存在
        HTTPException 400: 学号已存在
    """
    # Step 1: 获取学生记录
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Step 2: 更新姓名
    if student_data.name is not None:
        student.name = student_data.name

    # Step 3: 更新学号（需检查唯一性）
    if student_data.student_no is not None:
        # 检查新学号是否与其他学生冲突
        existing = (
            db.query(Student)
            .filter(
                Student.student_no == student_data.student_no,
                Student.id != student_id  # 排除自身
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student number already exists",
            )

        student.student_no = student_data.student_no

    # Step 4: 提交事务
    db.commit()
    db.refresh(student)

    # Step 5: 获取当前积分
    student_class = (
        db.query(StudentClass)
        .filter(StudentClass.student_id == student_id)
        .first()
    )
    current_score = student_class.current_score if student_class else 0

    # Step 6: 返回更新后的学生信息
    return StudentResponse(
        id=student.id,
        name=student.name,
        student_no=student.student_no,
        current_score=current_score,
    )


# ========== 删除学生 ==========

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    删除学生

    删除学生及其所有关联数据：
    1. 删除学生-班级关联（StudentClass）
    2. 删除学生的积分记录（ScoreRecord）
    3. 删除学生记录（Student）

    注意：这是物理删除，数据无法恢复

    参数：
        student_id: 学生 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        None（HTTP 204 状态码）

    异常：
        HTTPException 404: 学生不存在
    """
    # Step 1: 获取学生记录
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Step 2: 删除学生-班级关联
    db.query(StudentClass).filter(
        StudentClass.student_id == student_id
    ).delete()

    # Step 3: 删除积分记录
    from app.models.models import ScoreRecord
    db.query(ScoreRecord).filter(
        ScoreRecord.student_id == student_id
    ).delete()

    # Step 4: 删除学生记录
    db.delete(student)

    # Step 5: 提交事务
    db.commit()

    # HTTP 204 No Content
    return None
