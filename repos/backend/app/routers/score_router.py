"""
积分路由模块 (Score Router)

此模块处理与积分记录相关的 API 请求：

【管理员端 /api/scores】
1. GET /api/scores - 获取积分记录列表（支持多条件筛选）
2. POST /api/scores - 创建积分记录
3. GET /api/scores/student/{student_id} - 获取指定学生的积分记录

【教师端 /api/teacher】
1. GET /api/teacher/classes - 获取教师关联的班级列表
2. GET /api/teacher/class-courses - 获取班级的课程列表
3. POST /api/teacher/scores - 教师创建积分记录

数据模型关系：
- ScoreRecord: 积分记录表，存储每次积分变动
- StudentClass: 学生-班级关联表，存储学生的当前积分

积分流程：
1. 教师选择班级和课程
2. 教师输入学生姓名、积分值、原因
3. 系统创建 ScoreRecord 记录
4. 系统更新 StudentClass.current_score
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# 导入依赖注入函数
from app.dependencies import get_db, get_current_user
# 导入数据模型
from app.models.models import (
    ScoreRecord,      # 积分记录模型
    StudentClass,     # 学生-班级关联模型
    ClassCourse,      # 班级-课程关联模型
    Course,           # 课程模型
    Teacher,          # 教师模型
    TeacherClass,     # 教师-班级关联模型
    ClassModel,       # 班级模型
    Student,          # 学生模型
)
# 导入 Pydantic Schema
from app.schemas.score_schema import ScoreCreate, ScoreResponse, ScoreDetailResponse
from app.schemas.class_schema import ClassBasic


# ========== 创建路由实例 ==========

# 管理员积分路由
router = APIRouter(prefix="/api/scores", tags=["scores"])

# 教师端路由（用于教师端积分管理页面）
teacher_score_router = APIRouter(prefix="/api/teacher", tags=["teacher-scores"])


# ========== 教师端：获取教师关联的班级 ==========

@teacher_score_router.get("/classes", response_model=List[ClassBasic])
def get_teacher_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前教师关联的所有班级

    用于教师端积分管理页面的班级下拉框

    执行流程：
    1. 验证当前用户是教师角色
    2. 查询 TeacherClass 表，获取教师关联的所有班级 ID
    3. 查询班级信息并返回

    参数：
        db: 数据库会话
        current_user: 当前登录用户（包含 id, name, role）

    返回：
        List[ClassBasic]: 班级基本信息列表

    异常：
        HTTPException 403: 非教师用户访问
    """
    # Step 1: 验证用户角色（只有教师可以访问）
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )

    # Step 2: 获取教师 ID
    teacher_id = current_user["id"]

    # Step 3: 查询教师关联的所有班级
    teacher_classes = (
        db.query(TeacherClass)
        .filter(TeacherClass.teacher_id == teacher_id)
        .all()
    )

    # Step 4: 提取班级 ID 列表
    class_ids = [tc.class_id for tc in teacher_classes]

    # 如果教师没有关联任何班级，返回空列表
    if not class_ids:
        return []

    # Step 5: 查询班级详细信息
    classes = db.query(ClassModel).filter(
        ClassModel.id.in_(class_ids)
    ).all()

    # Step 6: 转换为响应格式
    return [
        ClassBasic(id=c.id, name=c.name)
        for c in classes
    ]


# ========== 教师端：获取班级的课程列表 ==========

@teacher_score_router.get("/class-courses", response_model=List)
def get_teacher_class_courses(
    class_id: int,  # URL 查询参数
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取指定班级关联的所有课程

    用于教师端选择班级后，显示该班级可选的课程列表

    执行流程：
    1. 验证当前用户是教师
    2. 验证教师被分配到该班级
    3. 查询班级关联的所有课程
    4. 返回课程列表

    参数：
        class_id: 班级 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        List[dict]: 课程列表，每项包含 id 和 name

    异常：
        HTTPException 403: 教师未被分配到该班级
        HTTPException 404: 班级不存在
    """
    # Step 1: 验证用户角色
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )

    # Step 2: 获取教师 ID
    teacher_id = current_user["id"]

    # Step 3: 验证教师被分配到该班级
    teacher_class = (
        db.query(TeacherClass)
        .filter(
            TeacherClass.teacher_id == teacher_id,
            TeacherClass.class_id == class_id
        )
        .first()
    )

    if not teacher_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )

    # Step 4: 查询班级关联的所有课程
    class_courses = (
        db.query(ClassCourse)
        .filter(ClassCourse.class_id == class_id)
        .all()
    )

    # Step 5: 转换为响应格式
    return [
        {"id": cc.course_id, "name": cc.course.name}
        for cc in class_courses
        if cc.course  # 安全检查
    ]


# ========== 创建积分记录（管理员） ==========

@router.post("", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
def create_score(
    score_data: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    创建积分记录（增加或扣除积分）

    正数积分：加分（如考试优秀 +10）
    负数积分：扣分（如违纪 -5）

    执行流程：
    1. 验证用户是教师
    2. 验证学生存在
    3. 验证课程存在
    4. 创建 ScoreRecord 记录
    5. 更新 StudentClass.current_score
    6. 提交事务

    参数：
        score_data: ScoreCreate，包含 student_id, value, reason, course_id, score_at
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ScoreResponse: 创建的积分记录

    异常：
        HTTPException 403: 非教师用户
        HTTPException 404: 学生或课程不存在
    """
    # Step 1: 验证用户角色
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create score records"
        )

    # Step 2: 验证学生存在
    # 注意：这里检查的是 StudentClass，而不是 Student
    # 因为积分是学生在特定班级的积分
    student_class = (
        db.query(StudentClass)
        .filter(StudentClass.student_id == score_data.student_id)
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Step 3: 验证课程存在
    course = db.query(Course).filter(
        Course.id == score_data.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Step 4: 获取教师 ID（从当前用户信息）
    teacher_id = current_user["id"]

    # Step 5: 创建积分记录
    score_record = ScoreRecord(
        student_id=score_data.student_id,
        value=score_data.value,           # 正数=加分，负数=扣分
        reason=score_data.reason,         # 积分原因
        course_id=score_data.course_id,   # 关联课程
        teacher_id=teacher_id,            # 记录操作教师
        score_at=score_data.score_at,      # 积分发生时间
    )
    db.add(score_record)

    # Step 6: 更新学生的当前积分
    # 直接在内存中修改，由 commit() 写入数据库
    student_class.current_score += score_data.value

    # Step 7: 提交事务
    db.commit()
    db.refresh(score_record)

    # Step 8: 返回创建的记录
    return ScoreRecord(
        id=score_record.id,
        student_id=score_record.student_id,
        value=score_record.value,
        reason=score_record.reason,
        course_id=score_record.course_id,
        teacher_id=score_record.teacher_id,
        score_at=score_record.score_at,
        created_at=score_record.created_at,
    )


# ========== 获取学生的积分记录 ==========

@router.get("/student/{student_id}", response_model=List[ScoreResponse])
def get_student_scores(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取指定学生的所有积分记录

    按时间倒序排列（最新记录在前）

    参数：
        student_id: 学生 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        List[ScoreResponse]: 积分记录列表
    """
    # 查询该学生的所有积分记录
    scores = (
        db.query(ScoreRecord)
        .filter(ScoreRecord.student_id == student_id)
        .order_by(ScoreRecord.score_at.desc())  # 按时间倒序
        .all()
    )

    return scores


# ========== 获取积分记录列表（多条件筛选） ==========

@router.get("", response_model=List[ScoreDetailResponse])
def list_scores(
    class_id: Optional[int] = Query(None, description="Class ID filter"),
    student_id: Optional[int] = Query(None, description="Student ID filter"),
    course_id: Optional[int] = Query(None, description="Course ID filter"),
    start: Optional[datetime] = Query(None, description="Start datetime filter (ISO format)"),
    end: Optional[datetime] = Query(None, description="End datetime filter (ISO format)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取积分记录列表，支持多条件筛选

    支持的筛选条件：
    - class_id: 班级 ID（通过 StudentClass 关联表筛选）
    - student_id: 学生 ID
    - course_id: 课程 ID
    - start: 开始时间（大于等于）
    - end: 结束时间（小于等于）

    权限说明：
    - 管理员：可以查看所有班级的记录
    - 教师：只能查看被分配班级的记录

    执行流程：
    1. 如果是教师，验证只能查看所关联班级的记录
    2. 构建查询（逐步添加筛选条件）
    3. 执行查询
    4. 关联查询学生、课程、教师信息
    5. 返回详细结果

    参数：
        class_id: 可选，班级 ID
        student_id: 可选，学生 ID
        course_id: 可选，课程 ID
        start: 可选，开始时间（ISO 格式）
        end: 可选，结束时间（ISO 格式）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        List[ScoreDetailResponse]: 积分记录详细列表
    """
    # Step 1: 教师权限验证
    # 教师只能查看被分配到的班级的积分记录
    if current_user["role"] == "teacher":
        teacher_id = current_user["id"]

        # 获取教师关联的所有班级 ID
        teacher_classes = (
            db.query(TeacherClass)
            .filter(TeacherClass.teacher_id == teacher_id)
            .all()
        )
        teacher_class_ids = [tc.class_id for tc in teacher_classes]

        # 如果请求了特定班级但该教师未关联，抛出错误
        if class_id is not None and class_id not in teacher_class_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this class"
            )

    # Step 2: 构建基础查询
    query = db.query(ScoreRecord)

    # Step 3: 添加班级筛选（通过 StudentClass 关联表）
    if class_id is not None:
        query = query.join(
            StudentClass,
            ScoreRecord.student_id == StudentClass.student_id
        ).filter(StudentClass.class_id == class_id)

    # Step 4: 添加学生筛选
    if student_id is not None:
        query = query.filter(ScoreRecord.student_id == student_id)

    # Step 5: 添加课程筛选
    if course_id is not None:
        query = query.filter(ScoreRecord.course_id == course_id)

    # Step 6: 添加时间范围筛选
    if start is not None:
        query = query.filter(ScoreRecord.score_at >= start)

    if end is not None:
        query = query.filter(ScoreRecord.score_at <= end)

    # Step 7: 按时间倒序排列
    query = query.order_by(ScoreRecord.score_at.desc())

    # Step 8: 执行查询
    score_records = query.all()

    # Step 9: 构建详细响应（关联查询学生、课程、教师信息）
    result = []
    for record in score_records:
        # 查询学生信息
        student = db.query(Student).filter(
            Student.id == record.student_id
        ).first()

        # 查询课程信息
        course = db.query(Course).filter(
            Course.id == record.course_id
        ).first()

        # 查询教师信息
        teacher = db.query(Teacher).filter(
            Teacher.id == record.teacher_id
        ).first()

        # 构建详细响应对象
        result.append(ScoreDetailResponse(
            id=record.id,
            student_id=record.student_id,
            student_name=student.name if student else "",
            student_no=student.student_no if student else "",
            value=record.value,
            reason=record.reason or "",
            course_name=course.name if course else "",
            teacher_name=teacher.name if teacher else "",
            score_at=record.score_at,
        ))

    return result
