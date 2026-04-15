"""
数据模型定义文件 (Database Models)

此文件定义了所有数据库表的结构（Schema），使用 SQLAlchemy ORM 实现。

模型之间的关联关系（Relationship）说明：
1. Teacher-Class: 多对多关系（一个教师可以教多个班级，一个班级可以有多个教师）
   - 关联表：TeacherClass

2. Class-Course: 多对多关系（一个班级可以选多门课程，一门课程可以属于多个班级）
   - 关联表：ClassCourse

3. Student-Class: 多对多关系（一个学生可以属于多个班级，一个班级可以有多个学生）
   - 关联表：StudentClass
   - 注意：学生有 current_score（当前积分）属性，存在于关联表中

4. ScoreRecord: 积分记录表
   - 关联 Student（一个学生可以有多条积分记录）
   - 关联 Course（一门课程可以有多条积分记录）
   - 关联 Teacher（一个教师可以创建多条积分记录）
"""

from datetime import datetime, date  # datetime: 日期时间，date: 日期
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


# ========== 教师模型 (Teacher) ==========

class Teacher(Base):
    """
    教师表模型

    存储教师的基本信息，包括姓名和密码（哈希存储）

    字段说明：
    - id: 主键，自增长
    - name: 教师姓名，唯一标识，用于登录
    - password: 密码的 bcrypt 哈希值（单向加密存储）
    - created_at: 创建时间，自动设置为当前 UTC 时间

    关联关系：
    - teacher_classes: 关联到 TeacherClass 表（多对多）
    - score_records: 关联到 ScoreRecord 表（一个教师的全部积分记录）
    """
    __tablename__ = "teacher"  # 数据库表名

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)  # nullable=False 表示不能为空
    password = Column(String(255), nullable=False)  # 存储 bcrypt 哈希
    created_at = Column(DateTime, default=datetime.utcnow)  # 自动设置创建时间

    # Relationships（关联关系）
    # back_populates 指定关联的对方模型属性名
    teacher_classes = relationship("TeacherClass", back_populates="teacher")
    score_records = relationship("ScoreRecord", back_populates="teacher")


# ========== 班级模型 (ClassModel) ==========

class ClassModel(Base):
    """
    班级表模型

    存储班级的基本信息，包括班级名称和唯一编码

    注意：类名使用 ClassModel 是因为 Python 内置有 `class` 关键字，
    所以避免命名冲突使用 ClassModel

    字段说明：
    - id: 主键，自增长
    - name: 班级名称，如"初一(1)班"
    - code: 班级编码，唯一，用于系统识别，如"C2025001"
    - is_active: 是否已激活，激活后才能进行积分操作
    - created_at: 创建时间

    关联关系：
    - teacher_classes: 关联到 TeacherClass 表（多对多）
    - class_courses: 关联到 ClassCourse 表（多对多）
    - student_classes: 关联到 StudentClass 表（多对多）
    """
    __tablename__ = "class_table"  # 数据库表名（使用 class_table 而非 class）

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # unique=True 保证编码唯一
    is_active = Column(Boolean, default=False)  # 默认为未激活
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher_classes = relationship("TeacherClass", back_populates="class_model")
    class_courses = relationship("ClassCourse", back_populates="class_model")
    student_classes = relationship("StudentClass", back_populates="class_model")


# ========== 教师-班级关联表 (TeacherClass) ==========

class TeacherClass(Base):
    """
    教师-班级关联表（多对多关系的中间表）

    SQLAlchemy 会自动将此模型作为多对多关系的关联表

    字段说明：
    - teacher_id: 教师ID，外键关联 teacher 表
    - class_id: 班级ID，外键关联 class_table 表
    - 这两个字段联合作为主键（Composite Primary Key）

    关联关系：
    - teacher: 关联到 Teacher 模型
    - class_model: 关联到 ClassModel 模型
    """
    __tablename__ = "teacher_class"

    teacher_id = Column(Integer, ForeignKey("teacher.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="teacher_classes")
    class_model = relationship("ClassModel", back_populates="teacher_classes")


# ========== 课程模型 (Course) ==========

class Course(Base):
    """
    课程表模型

    存储课程的基本信息，如"语文"、"数学"、"英语"等

    字段说明：
    - id: 主键，自增长
    - name: 课程名称

    关联关系：
    - class_courses: 关联到 ClassCourse 表（多对多）
    - score_records: 关联到 ScoreRecord 表（一门课程的所有积分记录）
    """
    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Relationships
    class_courses = relationship("ClassCourse", back_populates="course")
    score_records = relationship("ScoreRecord", back_populates="course")


# ========== 班级-课程关联表 (ClassCourse) ==========

class ClassCourse(Base):
    """
    班级-课程关联表（多对多关系的中间表）

    实现班级与课程之间的多对多关系：
    - 一个班级可以选择多门课程
    - 一门课程可以属于多个班级

    字段说明：
    - class_id: 班级ID，外键关联 class_table 表
    - course_id: 课程ID，外键关联 course 表
    - 这两个字段联合作为主键

    关联关系：
    - class_model: 关联到 ClassModel 模型
    - course: 关联到 Course 模型
    """
    __tablename__ = "class_course"

    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)

    # Relationships
    class_model = relationship("ClassModel", back_populates="class_courses")
    course = relationship("Course", back_populates="class_courses")


# ========== 学生模型 (Student) ==========

class Student(Base):
    """
    学生表模型

    存储学生的基本信息

    字段说明：
    - id: 主键，自增长
    - name: 学生姓名
    - student_no: 学号，唯一标识，如"20250001"
    - created_at: 创建时间

    关联关系：
    - student_classes: 关联到 StudentClass 表（多对多）
    - score_records: 关联到 ScoreRecord 表（一个学生的所有积分记录）

    注意：学生的当前积分（current_score）不存储在此表，
    而是通过 StudentClass 关联表存储（因为学生可能在不同班级有不同积分）
    """
    __tablename__ = "student"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    student_no = Column(String(20), nullable=False)  # 学号，唯一
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_classes = relationship("StudentClass", back_populates="student")
    score_records = relationship("ScoreRecord", back_populates="student")


# ========== 学生-班级关联表 (StudentClass) ==========

class StudentClass(Base):
    """
    学生-班级关联表（多对多关系的中间表）

    实现学生与班级之间的多对多关系，同时存储：
    - is_active: 学生是否在此班级激活（激活后才能有积分）
    - current_score: 学生在此班级的当前积分

    字段说明：
    - student_id: 学生ID，外键关联 student 表
    - class_id: 班级ID，外键关联 class_table 表
    - is_active: 是否激活（积分生效）
    - current_score: 当前积分（在关联表中存储，因为学生在不同班级积分不同）

    关联关系：
    - student: 关联到 Student 模型
    - class_model: 关联到 ClassModel 模型
    """
    __tablename__ = "student_class"

    student_id = Column(Integer, ForeignKey("student.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)
    is_active = Column(Boolean, default=False)  # 默认未激活
    current_score = Column(Integer, default=0)  # 默认积分为0

    # Relationships
    student = relationship("Student", back_populates="student_classes")
    class_model = relationship("ClassModel", back_populates="student_classes")


# ========== 积分记录模型 (ScoreRecord) ==========

class ScoreRecord(Base):
    """
    积分记录表模型

    存储每一次积分变动的详细信息

    字段说明：
    - id: 主键，自增长
    - student_id: 学生ID，外键关联 student 表
    - value: 积分值，正数表示加分，负数表示减分
    - reason: 积分原因，如"考试"、"作业"等
    - course_id: 课程ID，外键关联 course 表（哪门课的积分）
    - teacher_id: 教师ID，外键关联 teacher 表（谁给的积分）
    - score_at: 积分时间（记录实际发生积分的时间点）
    - created_at: 记录创建时间

    关联关系：
    - student: 关联到 Student 模型
    - course: 关联到 Course 模型
    - teacher: 关联到 Teacher 模型
    """
    __tablename__ = "score_record"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    value = Column(Integer, nullable=False)  # 积分值，可正可负
    reason = Column(String(200))  # 积分原因
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=False)
    score_at = Column(DateTime, nullable=False)  # 积分发生的时间
    created_at = Column(DateTime, default=datetime.utcnow)  # 记录创建时间

    # Relationships
    student = relationship("Student", back_populates="score_records")
    course = relationship("Course", back_populates="score_records")
    teacher = relationship("Teacher", back_populates="score_records")


# ========== 学期模型 (Term) ==========

class Term(Base):
    """
    学期表模型

    存储学期的基本信息

    字段说明：
    - id: 主键，自增长
    - name: 学期名称，如"2025-2026学年上学期"
    - year: 学年，如"2025-2026"

    关联关系：
    - term_settings: 关联到 TermSetting 表（一个学期有一个时间段设置）
    """
    __tablename__ = "term"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    year = Column(String(20), nullable=False)

    # Relationships
    term_settings = relationship("TermSetting", back_populates="term")


# ========== 学期设置模型 (TermSetting) ==========

class TermSetting(Base):
    """
    学期设置表模型

    存储每个学期的具体时间安排

    字段说明：
    - id: 主键，自增长
    - term_id: 学期ID，外键关联 term 表
    - start_date: 学期开始日期
    - end_date: 学期结束日期

    关联关系：
    - term: 关联到 Term 模型

    使用方式：通过 TermSetting 可以判断当前是否在学期内，
    以及距离学期结束还有多少天
    """
    __tablename__ = "term_setting"

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey("term.id"), nullable=False)
    start_date = Column(Date, nullable=False)  # 使用 Date 类型（只有日期）
    end_date = Column(Date, nullable=False)

    # Relationships
    term = relationship("Term", back_populates="term_settings")


# ========== 系统配置模型 (Config) ==========

class Config(Base):
    """
    系统配置表模型

    使用 Key-Value 形式存储系统的各种配置项

    字段说明：
    - key: 配置键，主键（唯一）
    - value: 配置值，存储为字符串格式

    存储的配置项包括：
    - admin_password_hash: 管理员密码的哈希值
    - settlement_code: 结算确认码
    - init_code: 初始化确认码
    - reasons: 积分原因列表（JSON 格式字符串）
    - codes: 确认码相关配置（JSON 格式字符串）

    这种设计的优点：可以在不修改代码的情况下修改系统配置
    """
    __tablename__ = "config"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
