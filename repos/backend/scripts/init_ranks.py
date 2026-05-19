#!/usr/bin/env python3
"""
段位初始化脚本 - 用于初始化6个默认段位数据
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models.models import Rank


def init_ranks():
    """初始化段位数据"""
    print()
    print("=== 初中班级积分管理系统 - 段位初始化 ===")
    print()

    # 创建数据库表（如果不存在）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing = db.query(Rank).count()
        if existing > 0:
            print(f"段位表已有 {existing} 条数据，跳过初始化")
            return True

        ranks = [
            {"name": "启灵境", "min_score": 0, "max_score": 50, "image_url": "/pics/1.png", "display_order": 1},
            {"name": "凝光境", "min_score": 51, "max_score": 100, "image_url": "/pics/2.png", "display_order": 2},
            {"name": "逐风境", "min_score": 101, "max_score": 200, "image_url": "/pics/3.png", "display_order": 3},
            {"name": "凌云境", "min_score": 201, "max_score": 300, "image_url": "/pics/4.png", "display_order": 4},
            {"name": "摘星境", "min_score": 301, "max_score": 400, "image_url": "/pics/5.png", "display_order": 5},
            {"name": "扶摇境", "min_score": 401, "max_score": 500, "image_url": "/pics/6.png", "display_order": 6},
            {"name": "筑基境", "min_score": 501, "max_score": None, "image_url": "/pics/7.png", "display_order": 7},
        ]

        for r in ranks:
            db.add(Rank(**r))

        db.commit()
        print("段位初始化成功")
        return True

    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = init_ranks()
    sys.exit(0 if success else 1)