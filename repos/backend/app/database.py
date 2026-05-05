"""
数据库配置文件 (Database Configuration)

此文件负责：
1. 配置 SQLite 数据库路径
2. 创建数据库引擎（engine）
3. 创建会话工厂（SessionLocal）
4. 定义 SQLAlchemy 的基类（Base）

架构说明：
- 使用 SQLite 作为数据库（轻量级，无需单独安装数据库服务器）
- 通过 SQLAlchemy ORM 实现数据库操作（面向对象）
- 数据库文件位于项目根目录的 db/ 文件夹下
"""

import os

# 从 SQLAlchemy 导入创建引擎和会话的工具
from sqlalchemy import create_engine  # 创建数据库引擎
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # 创建会话和基类


# ========== 数据库路径配置 ==========

# 获取当前文件所在的目录路径
# __file__ 是 Python 内置变量，表示当前文件的绝对路径
# 例如：D:\Learning\MyCourse\repos\backend\app\database.py
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 向上两级目录，到达 repos/ 目录
# APP_DIR = D:\Learning\MyCourse\repos\backend\app
# 第一次 dirname = D:\Learning\MyCourse\repos\backend
# 第二次 dirname = D:\Learning\MyCourse\repos
REPOS_DIR = os.path.dirname(os.path.dirname(APP_DIR))

# 拼接数据库文件路径
# db/ 文件夹应该在 repos/ 目录下
# 最终路径：D:\Learning\MyCourse\repos\db\scores.db
DATABASE_PATH = os.path.join(REPOS_DIR, "db", "scores.db")
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 将文件路径转换为 SQLite URL 格式
# sqlite:/// 是 SQLAlchemy 识别 SQLite 的协议前缀
# 三个斜杠表示相对路径（相对于当前工作目录）
# 四个斜杠（file:///）表示绝对路径
# 支持环境变量覆盖
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")


# ========== 创建数据库引擎 ==========

# create_engine() 是 SQLAlchemy 核心函数，用于创建数据库引擎
# 引擎是数据库连接池的管理器，负责：
# 1. 建立与数据库的连接
# 2. 发送 SQL 语句到数据库
# 3. 接收数据库返回的结果

# connect_args={"check_same_thread": False}
# SQLite 默认只允许在创建连接的线程中使用连接
# 设置为 False 允许在不同线程中使用连接（FastAPI 使用多线程）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # 允许多线程访问 SQLite
)


# ========== 创建会话工厂 ==========

# sessionmaker() 创建会话工厂，用于生成数据库会话
# 会话（Session）是与数据库交互的主要接口
# - autocommit=False: 默认不自动提交，需要手动调用 commit()
# - autoflush=False: 默认不自动刷新，需要手动调用 flush()
# - bind=engine: 将会话绑定到指定的数据引擎

SessionLocal = sessionmaker(
    autocommit=False,      # 需要手动提交事务
    autoflush=False,       # 需要手动刷新缓存
    bind=engine            # 使用上面创建的引擎
)


# ========== 定义 SQLAlchemy 基类 ==========

# DeclarativeBase 是 SQLAlchemy 2.0 推荐的基类
# 所有数据模型（如 Teacher, Student）都应继承此类
# 继承后，模型类可以通过 metadata 属性访问所有表定义

class Base(DeclarativeBase):
    """
    SQLAlchemy ORM 基类

    所有数据模型类（如 Teacher, Student, ClassModel）都需要继承此类
    通过继承，模型类自动获得与数据库交互的能力

    使用方式：
        class User(Base):
            __tablename__ = "users"  # 指定对应的表名
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
    """
    pass
