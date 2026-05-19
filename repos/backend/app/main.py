"""
主应用入口文件 (Main Application Entry Point)

此文件是 FastAPI 应用的启动点，负责：
1. 配置 FastAPI 应用的生命周期（启动/关闭）
2. 初始化数据库表
3. 初始化默认配置数据（管理员密码、结算码、初始化码等）
4. 注册所有路由 routers

架构说明：
- FastAPI 使用异步事件处理器（lifespan）来管理应用启动和关闭
- 所有路由通过 include_router 方法注册到应用
- 数据库使用 SQLite，通过 SQLAlchemy ORM 操作
"""

from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# 从 database.py 导入数据库引擎和 Base 类
# Base: SQLAlchemy ORM 的基类，用于定义所有数据模型
# engine: 数据库连接引擎，管理所有数据库连接
from app.database import Base, engine, SessionLocal

# 导入安全相关的工具函数
# get_default_settlement_code: 获取结算确认码（用于结算操作的身份验证）
# get_default_init_code: 获取初始化确认码（用于系统初始化操作的身份验证）
from app.utils.security import get_default_settlement_code, get_default_init_code

# 配置日志记录
# 日志级别设置为 INFO，可以记录应用的运行状态信息
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    异步上下文管理器，处理 FastAPI 应用的启动和关闭事件

    这个函数在应用启动时执行一次，在应用关闭时执行一次
    使用 yield 语句将代码分为两部分：yield 之前是启动逻辑，yield 之后是关闭逻辑

    执行流程：
    1. 应用启动时：创建数据库表 → 初始化默认配置 → 准备处理请求
    2. 应用关闭时：执行清理工作（如果需要）
    """
    # ========== 启动阶段 ==========

    # Step 1: 创建数据库表
    # Base.metadata.create_all() 会扫描所有继承自 Base 的模型类
    # 如果数据库表不存在，则创建；如果已存在，则跳过
    # bind=engine 指定使用哪个数据库引擎
    Base.metadata.create_all(bind=engine)

    # Step 2: 初始化默认配置数据
    # 打开一个新的数据库会话
    db = SessionLocal()
    try:
        # 导入数据模型和工具函数
        from app.models.models import Config  # 配置表模型
        from app.utils.security import hash_password  # 密码哈希函数
        import os

        # 定义默认配置项列表
        # 每个配置项包含 key（配置键）和 value（配置值）
        default_configs = [
            # settlement_code: 结算确认码，用于验证结算操作的合法性
            # 可以通过环境变量 SETTLEMENT_CODE 设置，否则自动生成随机码
            {"key": "settlement_code", "value": get_default_settlement_code()},

            # init_code: 初始化确认码，用于验证系统初始化操作的合法性
            # 可以通过环境变量 INIT_CODE 设置，否则自动生成随机码
            {"key": "init_code", "value": get_default_init_code()},

            # reasons: 积分原因配置，存储为 JSON 数组格式的字符串
            # 包含：考试、作业、荣誉、其他 四种默认原因
            {"key": "reasons", "value": '["考试","作业","荣誉","其他"]'},
        ]

        # 遍历默认配置，检查是否已存在，如不存在则添加到数据库
        for config_data in default_configs:
            # 查询配置表中是否已存在该键
            existing = db.query(Config).filter(Config.key == config_data["key"]).first()
            # 如果不存在，则添加新配置
            if not existing:
                db.add(Config(**config_data))

        # Step 3: 初始化管理员密码
        # 检查数据库中是否已有管理员密码哈希值
        admin_password_config = db.query(Config).filter(Config.key == "admin_password_hash").first()
        if not admin_password_config:
            # 从环境变量获取管理员密码，默认为 "admin123"
            # 注意：生产环境中应通过环境变量设置强密码
            default_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            # 使用 bcrypt 对密码进行哈希处理（单向加密，不可逆）
            hashed = hash_password(default_password)
            # 将哈希后的密码存储到数据库
            db.add(Config(key="admin_password_hash", value=hashed))

        # 提交事务，将所有更改保存到数据库
        db.commit()

    except Exception as e:
        # 如果发生异常，回滚事务，撤销所有未提交的更改
        db.rollback()
        # 记录警告日志，但不影响应用启动
        logger.warning(f"Config initialization error: {e}")
    finally:
        # 无论是否发生异常，最后都会执行：关闭数据库会话
        # 这是防御性编程，确保数据库连接被正确释放
        db.close()

    # yield 之前的代码在应用启动时执行
    # yield 之后的代码在应用关闭时执行
    yield

    # ========== 关闭阶段 ==========
    # 可以在这里添加应用关闭时的清理逻辑
    # 例如：关闭数据库连接池、关闭缓存连接等


# ========== 创建 FastAPI 应用实例 ==========
# title: API 文档中显示的标题
# lifespan: 指定生命周期管理器
app = FastAPI(
    title="Score Management API",
    lifespan=lifespan
)

# ========== 挂载静态文件目录（图片访问）==========
# 确保上传目录存在
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/pics")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# 挂载 /pics 路径到上传目录
app.mount("/pics", StaticFiles(directory=UPLOAD_DIR), name="pics")


# ========== 注册路由 (Routers) ==========
# 路由负责将 HTTP 请求分发到对应的处理函数
# prefix: 所有该路由下接口的 URL 前缀
# tags: API 文档中的分组标签

# 导入所有路由模块
# 使用 as alias 避免与变量名冲突
from app.routers import (
    auth_router,           # 认证相关路由（登录、获取当前用户）
    course_router,         # 课程管理路由
    class_course_router,   # 班级-课程关联路由
    class_router,          # 班级管理路由
    config_router,         # 系统配置路由
    term_router,           # 学期配置路由
    teacher_router,        # 教师管理路由
    settlement_router,     # 结算相关路由
    student_router,        # 学生管理路由
    score_router,          # 积分记录路由（管理员）
    teacher_score_router,  # 积分记录路由（教师）
    ranking_router,        # 排名相关路由
    rank_router,           # 段位管理路由
    upload_router,         # 图片上传路由
)

# 将各个路由注册到 FastAPI 应用
# 路由顺序不影响匹配，FastAPI 会根据路径选择最具体的匹配

# 认证路由：/api/auth
app.include_router(auth_router)

# 课程路由：/api/courses
app.include_router(course_router)

# 班级-课程关联路由：/api/class-courses
app.include_router(class_course_router)

# 班级路由：/api/classes
app.include_router(class_router)

# 系统配置路由：/api/config
app.include_router(config_router)

# 学期配置路由：/api/terms
app.include_router(term_router)

# 教师路由：/api/teachers
app.include_router(teacher_router)

# 结算路由：/api/settlement
app.include_router(settlement_router)

# 学生路由：/api/students
app.include_router(student_router)

# 积分记录路由（管理员）：/api/scores
app.include_router(score_router)

# 积分记录路由（教师）：/api/teacher/scores
app.include_router(teacher_score_router)

# 排名路由：/api/rankings
app.include_router(ranking_router)

# 段位路由：/api/ranks
app.include_router(rank_router)

# 图片上传路由：/api/upload
app.include_router(upload_router)


# ========== 根路径路由 ==========
@app.get("/")
async def root():
    """
    根路径处理函数

    当用户访问 http://localhost:8001/ 时调用此函数
    返回一个简单的 JSON 消息，确认 API 正在运行

    返回：
        dict: 包含确认消息的字典
    """
    return {"message": "Score Management API is running"}


# ========== 健康检查路由 ==========
@app.get("/health")
async def health_check():
    """
    健康检查处理函数

    用于检查 API 服务是否正常运行
    通常由负载均衡器或监控工具调用

    返回：
        dict: 包含健康状态的字典
    """
    return {"status": "healthy"}
