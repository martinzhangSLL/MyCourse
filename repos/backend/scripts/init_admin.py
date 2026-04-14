#!/usr/bin/env python3
"""
管理员初始化脚本 - 用于创建首个管理员账号
"""

import os
import secrets
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models.models import Config
from app.utils.security import hash_password


def generate_random_string(length: int = 16) -> str:
    """生成随机字符串"""
    return secrets.token_hex(length // 2)[:length].upper()


def init_admin():
    """初始化管理员账号"""
    print()
    print("=== 初中班级积分管理系统 - 管理员初始化 ===")
    print()

    # 创建数据库表（如果不存在）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 检查管理员是否已存在
        existing_admin = db.query(Config).filter(Config.key == "admin_password_hash").first()
        if existing_admin:
            print("错误：管理员账号已存在。如需重置，请先删除数据库文件。")
            return False

        # 交互式输入
        username = input("请设置管理员账号（默认: admin）: ").strip()
        if not username:
            username = "admin"

        password = input("请设置管理员密码: ").strip()
        while len(password) < 6:
            print("密码长度至少为 6 位")
            password = input("请设置管理员密码: ").strip()

        confirm_password = input("确认管理员密码: ").strip()
        while password != confirm_password:
            print("两次输入的密码不一致")
            confirm_password = input("确认管理员密码: ").strip()

        print()
        print("正在创建管理员账号...")

        # 生成密码哈希
        password_hash = hash_password(password)

        # 生成随机密钥
        jwt_secret_key = secrets.token_hex(32)

        # 生成随机代码
        settlement_code = generate_random_string(16)
        init_code = generate_random_string(16)

        # 保存配置
        config_items = [
            ("admin_username", username),
            ("admin_password_hash", password_hash),
            ("settlement_code", settlement_code),
            ("init_code", init_code),
        ]

        for key, value in config_items:
            config = Config(key=key, value=value)
            db.add(config)

        db.commit()

        print("管理员账号创建成功！")
        print()
        print(f"JWT_SECRET_KEY: {jwt_secret_key}")
        print("请保存此密钥，后续需要设置到环境变量 JWT_SECRET_KEY")
        print()
        print("运行命令:")
        print(f"  $ export JWT_SECRET_KEY={jwt_secret_key}")
        print("  $ uvicorn app.main:app --host 127.0.0.1 --port 8000")

        return True

    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = init_admin()
    sys.exit(0 if success else 1)
