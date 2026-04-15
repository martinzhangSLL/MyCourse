"""
班级管理路由模块 (Class Management Router)

此模块处理与班级管理相关的 API 请求：

1. GET /api/classes - 获取所有班级列表
2. POST /api/classes - 创建新班级
3. GET /api/classes/{class_id} - 获取指定班级详情
4. PUT /api/classes/{class_id} - 更新班级信息
5. DELETE /api/classes/{class_id} - 删除班级（逻辑删除）
6. PUT /api/classes/{class_id}/activate - 激活班级

数据模型关系：
- 班级与教师：多对多关系（通过 TeacherClass 关联表）
- 班级与课程：多对多关系（通过 ClassCourse 关联表）
- 班级与学生：多对多关系（通过 StudentClass 关联表）

逻辑说明：
- 删除班级是"逻辑删除"，实际是将 is_active 设置为 False
- 只有激活的班级，其学生的积分才会生效
"""

from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI 路由组件
from sqlalchemy.orm import Session  # SQLAlchemy 数据库会话
from sqlalchemy import select, delete  # SQLAlchemy SQL 表达式
from typing import List  # 类型提示

# 导入数据模型
from app.models.models import ClassModel, TeacherClass, ClassCourse, StudentClass, Teacher, Course
# 导入 Pydantic Schema
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse, TeacherBasic, CourseBasic
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user

# 创建路由实例
router = APIRouter(prefix="/api/classes", tags=["classes"])


# ========== 辅助函数 ==========

def build_class_response(class_model: ClassModel) -> ClassResponse:
    """
    将 ClassModel 数据库模型转换为 ClassResponse API 响应模型

    此函数处理班级模型的转换，包括关联的教师和课程信息

    执行流程：
    1. 从 class_model.teacher_classes 提取教师信息
    2. 从 class_model.class_courses 提取课程信息
    3. 构建 ClassResponse 对象返回

    参数：
        class_model: ClassModel 数据库模型实例

    返回：
        ClassResponse: 包含班级信息和关联的教师/课程列表
    """
    # Step 1: 提取关联的教师信息
    # teacher_classes 是 TeacherClass 关联表的列表
    # 通过 back_populates 可以访问对应的 Teacher 对象
    teachers = [
        TeacherBasic(id=tc.teacher_id, name=tc.teacher.name)
        for tc in class_model.teacher_classes
        if tc.teacher  # 安全检查，避免孤立的关联记录
    ]

    # Step 2: 提取关联的课程信息
    # class_courses 是 ClassCourse 关联表的列表
    courses = [
        CourseBasic(id=cc.course_id, name=cc.course.name)
        for cc in class_model.class_courses
        if cc.course  # 安全检查
    ]

    # Step 3: 构建响应对象
    return ClassResponse(
        id=class_model.id,
        name=class_model.name,
        code=class_model.code,
        is_active=class_model.is_active,
        teachers=teachers,
        courses=courses,
        created_at=class_model.created_at,
    )


# ========== 获取班级列表 ==========

@router.get("", response_model=List[ClassResponse])
def list_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取所有班级列表

    返回数据库中所有班级，包括关联的教师和课程信息

    执行流程：
    1. 查询 ClassModel 表，获取所有班级
    2. 对每个班级调用 build_class_response 转换为响应格式
    3. 返回班级列表

    参数：
        db: 数据库会话（依赖注入）
        current_user: 当前登录用户（依赖注入，用于权限验证）

    返回：
        List[ClassResponse]: 班级列表
    """
    # 查询所有班级
    classes = db.query(ClassModel).all()

    # 转换为响应格式并返回
    return [build_class_response(c) for c in classes]


# ========== 创建班级 ==========

@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建新班级

    创建一个新班级，并关联指定的教师和课程

    执行流程：
    1. 验证班级编码是否已存在（编码必须唯一）
    2. 创建 ClassModel 记录
    3. 创建 TeacherClass 关联记录（关联教师）
    4. 创建 ClassCourse 关联记录（关联课程）
    5. 提交事务并返回新班级信息

    参数：
        class_data: ClassCreate，包含 name, code, teacher_ids, course_ids
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ClassResponse: 新创建的班级信息

    异常：
        HTTPException 400: 班级编码已存在
    """
    # Step 1: 检查班级编码是否已存在
    existing = db.query(ClassModel).filter(
        ClassModel.code == class_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class code already exists"  # 班级编码已存在
        )

    # Step 2: 创建班级模型
    # 注意：新班级默认 is_active=False（未激活）
    class_model = ClassModel(
        name=class_data.name,
        code=class_data.code,
        is_active=False,
    )
    db.add(class_model)
    db.flush()  # 刷新以获取班级 ID（重要！）

    # Step 3: 关联教师（多对多）
    if class_data.teacher_ids:
        for teacher_id in class_data.teacher_ids:
            # 验证教师是否存在
            teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
            if teacher:
                # 创建关联记录
                teacher_class = TeacherClass(
                    teacher_id=teacher_id,
                    class_id=class_model.id
                )
                db.add(teacher_class)

    # Step 4: 关联课程（多对多）
    if class_data.course_ids:
        for course_id in class_data.course_ids:
            # 验证课程是否存在
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                # 创建关联记录
                class_course = ClassCourse(
                    class_id=class_model.id,
                    course_id=course_id
                )
                db.add(class_course)

    # Step 5: 提交事务
    db.commit()

    # Step 6: 刷新对象，获取数据库生成的时间戳等
    db.refresh(class_model)

    # Step 7: 返回创建的班级信息
    return build_class_response(class_model)


# ========== 获取单个班级 ==========

@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定班级的详细信息

    参数：
        class_id: 班级 ID（URL 路径参数）
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ClassResponse: 班级详细信息

    异常：
        HTTPException 404: 班级不存在
    """
    # 查询班级
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"  # 班级不存在
        )

    return build_class_response(class_model)


# ========== 更新班级 ==========

@router.put("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新班级信息

    可更新班级名称、编码、教师关联、课程关联

    执行流程：
    1. 验证班级是否存在
    2. 更新基本字段（name, code）
    3. 如果提供了 teacher_ids，先删除旧关联，再创建新关联
    4. 如果提供了 course_ids，先删除旧关联，再创建新关联
    5. 提交事务并返回更新后的班级信息

    参数：
        class_id: 班级 ID
        class_data: ClassUpdate，包含要更新的字段
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ClassResponse: 更新后的班级信息

    异常：
        HTTPException 404: 班级不存在
        HTTPException 400: 新编码与已存在的班级冲突
    """
    # Step 1: 获取班级
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Step 2: 更新基本字段
    if class_data.name is not None:
        class_model.name = class_data.name

    if class_data.code is not None:
        # 检查新编码是否与其他班级冲突
        existing = db.query(ClassModel).filter(
            ClassModel.code == class_data.code,
            ClassModel.id != class_id  # 排除自身
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class code already exists"
            )
        class_model.code = class_data.code

    # Step 3: 更新教师关联
    if class_data.teacher_ids is not None:
        # 删除旧关联
        db.query(TeacherClass).filter(
            TeacherClass.class_id == class_id
        ).delete()

        # 创建新关联
        for teacher_id in class_data.teacher_ids:
            teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
            if teacher:
                teacher_class = TeacherClass(
                    teacher_id=teacher_id,
                    class_id=class_id
                )
                db.add(teacher_class)

    # Step 4: 更新课程关联
    if class_data.course_ids is not None:
        # 删除旧关联
        db.query(ClassCourse).filter(
            ClassCourse.class_id == class_id
        ).delete()

        # 创建新关联
        for course_id in class_data.course_ids:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                class_course = ClassCourse(
                    class_id=class_id,
                    course_id=course_id
                )
                db.add(class_course)

    # Step 5: 提交事务
    db.commit()
    db.refresh(class_model)

    return build_class_response(class_model)


# ========== 删除班级 ==========

@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除班级（逻辑删除）

    注意：这是逻辑删除，实际只是将 is_active 设置为 False
    班级的数据仍然保留在数据库中

    为什么使用逻辑删除：
    - 保留历史数据（如班级历史、积分记录）
    - 避免外键关联被破坏
    - 可以通过激活恢复班级

    参数：
        class_id: 班级 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        None（HTTP 204 状态码表示成功但无返回内容）

    异常：
        HTTPException 404: 班级不存在
    """
    # Step 1: 获取班级
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Step 2: 逻辑删除 - 设置为未激活
    # 注意：这里不是物理删除，只是标记 is_active=False
    class_model.is_active = False

    db.commit()

    # HTTP 204 No Content：请求成功，但响应没有内容
    return None


# ========== 激活班级 ==========

@router.put("/{class_id}/activate", response_model=ClassResponse)
def activate_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    激活班级及其所有学生

    激活后：
    - 班级的 is_active 变为 True
    - 班级所有学生的 is_active 变为 True
    - 学生的积分开始生效

    执行流程：
    1. 验证班级是否存在
    2. 设置班级为已激活
    3. 设置班级所有学生为已激活
    4. 提交事务

    参数：
        class_id: 班级 ID
        db: 数据库会话
        current_user: 当前登录用户

    返回：
        ClassResponse: 激活后的班级信息

    异常：
        HTTPException 404: 班级不存在
    """
    # Step 1: 获取班级
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Step 2: 激活班级
    class_model.is_active = True

    # Step 3: 激活班级所有学生
    # 使用 bulk update 提高性能，一次性更新多条记录
    db.query(StudentClass).filter(
        StudentClass.class_id == class_id
    ).update(
        {StudentClass.is_active: True},
        synchronize_session=False  # 不同步会话，直接执行 SQL
    )

    db.commit()
    db.refresh(class_model)

    return build_class_response(class_model)
