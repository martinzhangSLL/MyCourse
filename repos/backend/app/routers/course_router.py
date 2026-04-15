"""
课程管理路由模块 (Course Management Router)

此模块处理与课程管理相关的 API 请求：

【课程管理 /api/courses】
1. GET /api/courses - 获取所有课程列表
2. POST /api/courses - 创建新课程
3. PUT /api/courses/{course_id} - 更新课程信息
4. DELETE /api/courses/{course_id} - 删除课程

【班级-课程关联 /api/class-courses】
1. GET /api/class-courses - 获取班级的课程列表
2. PUT /api/class-courses - 更新班级的课程列表

数据模型关系：
- Course: 课程表，存储课程基本信息
- ClassCourse: 班级-课程关联表（多对多）
- ClassModel: 班级表

课程特点：
- 课程是被动的，不直接关联班级
- 班级通过 ClassCourse 表选择要上的课程
- 一门课程可以属于多个班级（多对多关系）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# 导入数据模型
from app.models.models import Course, ClassCourse, ClassModel
# 导入 Pydantic Schema
from app.schemas.course_schema import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    ClassCourseRequest,
    ClassCourseResponse,
)
# 导入依赖注入函数
from app.dependencies import get_db, get_current_user

# 创建路由实例
router = APIRouter(prefix="/api/courses", tags=["courses"])

# 班级-课程关联路由
class_course_router = APIRouter(prefix="/api/class-courses", tags=["class-courses"])


# ========== 获取课程列表 ==========

@router.get("", response_model=List[CourseResponse])
def list_courses(db: Session = Depends(get_db)):
    """
    获取所有课程列表

    执行流程：
    1. 查询 Course 表，获取所有课程
    2. 返回课程列表

    参数：
        db: 数据库会话

    返回：
        List[CourseResponse]: 课程列表
    """
    courses = db.query(Course).all()
    return courses


# ========== 创建课程 ==========

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db)
):
    """
    创建新课程

    执行流程：
    1. 创建 Course 模型实例
    2. 添加到数据库会话
    3. 提交事务
    4. 返回创建的课程

    参数：
        course: CourseCreate，包含课程名称
        db: 数据库会话

    返回：
        CourseResponse: 创建的课程
    """
    # Step 1: 创建课程模型
    db_course = Course(name=course.name)

    # Step 2: 添加到会话
    db.add(db_course)

    # Step 3: 提交事务
    db.commit()

    # Step 4: 刷新获取数据库生成的信息
    db.refresh(db_course)

    return db_course


# ========== 更新课程 ==========

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course: CourseUpdate,
    db: Session = Depends(get_db)
):
    """
    更新课程信息

    执行流程：
    1. 查询要更新的课程
    2. 如果不存在，抛出 404 错误
    3. 更新课程名称
    4. 提交事务

    参数：
        course_id: 课程 ID
        course: CourseUpdate，包含新的课程名称
        db: 数据库会话

    返回：
        CourseResponse: 更新后的课程

    异常：
        HTTPException 404: 课程不存在
    """
    # Step 1: 查询课程
    db_course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    # Step 2: 验证课程存在
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Step 3: 更新课程名称
    db_course.name = course.name

    # Step 4: 提交事务
    db.commit()
    db.refresh(db_course)

    return db_course


# ========== 删除课程 ==========

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    删除课程

    注意：删除课程会同时删除班级-课程关联
    但不会删除已存在的积分记录

    执行流程：
    1. 查询要删除的课程
    2. 如果不存在，抛出 404 错误
    3. 删除课程（级联删除 ClassCourse 关联）
    4. 提交事务

    参数：
        course_id: 课程 ID
        db: 数据库会话

    返回：
        None（HTTP 204）

    异常：
        HTTPException 404: 课程不存在
    """
    # Step 1: 查询课程
    db_course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    # Step 2: 验证课程存在
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Step 3: 删除课程
    # 注意：由于外键关系，ClassCourse 中对应记录也会被删除
    db.delete(db_course)

    # Step 4: 提交事务
    db.commit()

    return None


# ========== 获取班级的课程列表 ==========

@class_course_router.get("", response_model=List[ClassCourseResponse])
def get_class_courses(
    class_id: int,  # 查询参数
    db: Session = Depends(get_db)
):
    """
    获取指定班级关联的所有课程

    执行流程：
    1. 验证班级存在
    2. 查询 ClassCourse 关联表，获取该班级的所有课程
    3. 返回课程列表

    参数：
        class_id: 班级 ID（查询参数）
        db: 数据库会话

    返回：
        List[ClassCourseResponse]: 课程列表

    异常：
        HTTPException 404: 班级不存在
    """
    # Step 1: 验证班级存在
    class_model = db.query(ClassModel).filter(
        ClassModel.id == class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Step 2: 查询班级关联的课程
    class_courses = db.query(ClassCourse).filter(
        ClassCourse.class_id == class_id
    ).all()

    # Step 3: 返回课程信息
    # ClassCourseResponse 就是 Course 模型
    return [cc.course for cc in class_courses]


# ========== 更新班级的课程列表 ==========

@class_course_router.put("", response_model=dict)
def update_class_courses(
    request: ClassCourseRequest,
    db: Session = Depends(get_db)
):
    """
    更新班级的课程列表

    这是覆盖式更新：先删除旧关联，再添加新关联

    执行流程：
    1. 验证班级存在
    2. 删除该班级所有旧的课程关联
    3. 添加新的课程关联（验证课程存在）
    4. 提交事务

    参数：
        request: ClassCourseRequest，包含 class_id 和 course_ids
        db: 数据库会话

    返回：
        dict: 成功消息

    异常：
        HTTPException 404: 班级或课程不存在
    """
    # Step 1: 验证班级存在
    class_model = db.query(ClassModel).filter(
        ClassModel.id == request.class_id
    ).first()

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Step 2: 删除旧的课程关联
    db.query(ClassCourse).filter(
        ClassCourse.class_id == request.class_id
    ).delete()

    # Step 3: 添加新的课程关联
    for course_id in request.course_ids:
        # 验证课程存在
        course = db.query(Course).filter(
            Course.id == course_id
        ).first()

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with id {course_id} not found"
            )

        # 创建关联记录
        db.add(ClassCourse(
            class_id=request.class_id,
            course_id=course_id
        ))

    # Step 4: 提交事务
    db.commit()

    return {"message": "Class courses updated successfully"}
