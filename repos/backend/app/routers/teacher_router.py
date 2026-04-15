"""
教师管理路由模块 (Teacher Router)

此模块处理与教师管理相关的 API 请求：

1. GET /api/teachers - 获取所有教师列表
2. POST /api/teachers - 创建新教师
3. PUT /api/teachers/{teacher_id} - 更新教师信息
4. DELETE /api/teachers/{teacher_id} - 删除教师

数据模型关系：
- Teacher: 教师表，存储教师基本信息（姓名、密码哈希）
- TeacherClass: 教师-班级关联表（多对多关系）

密码处理：
- 教师密码使用 bcrypt 哈希存储（不可逆）
- 创建和更新时都需要对密码进行哈希处理
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 导入数据模型
from app.models.models import Teacher
# 导入 Pydantic Schema
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate, TeacherResponse
# 导入密码哈希工具
from app.utils.security import hash_password
# 导入依赖注入函数
from app.dependencies import get_db

# 创建路由实例
router = APIRouter(prefix="/api/teachers", tags=["teachers"])


# ========== 获取教师列表 ==========

@router.get("", response_model=list[TeacherResponse])
def list_teachers(db: Session = Depends(get_db)):
    """
    获取所有教师列表

    执行流程：
    1. 查询 Teacher 表的所有记录
    2. 返回教师列表

    参数：
        db: 数据库会话

    返回：
        List[TeacherResponse]: 教师列表
    """
    teachers = db.query(Teacher).all()
    return teachers


# ========== 创建教师 ==========

@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db)
):
    """
    创建新教师

    执行流程：
    1. 对密码进行 bcrypt 哈希处理
    2. 创建 Teacher 记录
    3. 添加到数据库会话
    4. 提交事务
    5. 返回创建的教师信息

    参数：
        teacher_data: TeacherCreate，包含 name 和 password
        db: 数据库会话

    返回：
        TeacherResponse: 创建的教师信息（不包含密码）
    """
    # Step 1: 对密码进行哈希处理
    # 注意：密码绝对不能明文存储
    hashed_password = hash_password(teacher_data.password)

    # Step 2: 创建教师记录
    teacher = Teacher(
        name=teacher_data.name,
        password=hashed_password  # 存储哈希后的密码
    )

    # Step 3: 添加到会话
    db.add(teacher)

    # Step 4: 提交事务
    db.commit()

    # Step 5: 刷新获取数据库生成的信息
    db.refresh(teacher)

    # Step 6: 返回创建的教师
    return teacher


# ========== 更新教师 ==========

@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db)
):
    """
    更新教师信息（仅管理员可操作）

    可更新：姓名、密码

    执行流程：
    1. 查询要更新的教师
    2. 如果不存在，抛出 404
    3. 更新姓名
    4. 对新密码进行哈希并更新
    5. 提交事务

    参数：
        teacher_id: 教师 ID
        teacher_data: TeacherUpdate，包含 name 和 password
        db: 数据库会话

    返回：
        TeacherResponse: 更新后的教师信息

    异常：
        HTTPException 404: 教师不存在
    """
    # Step 1: 查询教师
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id
    ).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    # Step 2: 更新姓名
    teacher.name = teacher_data.name

    # Step 3: 对新密码进行哈希
    hashed_password = hash_password(teacher_data.password)
    teacher.password = hashed_password

    # Step 4: 提交事务
    db.commit()
    db.refresh(teacher)

    # Step 5: 返回更新后的教师
    return teacher


# ========== 删除教师 ==========

@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    """
    删除教师

    注意：
    - 会同时删除教师与班级的关联（TeacherClass）
    - 不会删除教师创建的积分记录（保留历史数据）

    执行流程：
    1. 查询要删除的教师
    2. 如果不存在，抛出 404
    3. 删除教师记录
    4. 提交事务

    参数：
        teacher_id: 教师 ID
        db: 数据库会话

    返回：
        None（HTTP 204）

    异常：
        HTTPException 404: 教师不存在
    """
    # Step 1: 查询教师
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id
    ).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    # Step 2: 删除教师
    # 注意：TeacherClass 中的关联记录会因外键级联删除而被清理
    db.delete(teacher)

    # Step 3: 提交事务
    db.commit()
