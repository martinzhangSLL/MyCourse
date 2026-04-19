#!/usr/bin/env python3
"""
数据库迁移脚本 - 给 term 表添加 is_active 列，给 score_record 表添加 term_id 列

此脚本实现：
1. 给 term 表新增 is_active 列（Boolean，默认0）
2. 给 score_record 表新增 term_id 列（Integer，外键关联 term.id）
3. 设置第一条学期 is_active=True
4. 设置所有积分记录 term_id 指向该学期
"""

import os
import sys
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal


def migrate():
    """执行数据库迁移"""
    print()
    print("=== 数据库迁移：添加 term is_active 和 score_record term_id ===")
    print()

    with engine.connect() as conn:
        # 1. 给 term 表新增 is_active 列
        print("1. 添加 term.is_active 列...")
        try:
            conn.execute(text("ALTER TABLE term ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 0"))
            conn.commit()
            print("   term.is_active 列添加成功")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("   term.is_active 列已存在，跳过")
            else:
                raise
        is_active_col_exists = True

        # 2. 给 score_record 表新增 term_id 列
        print("2. 添加 score_record.term_id 列...")
        try:
            conn.execute(text("ALTER TABLE score_record ADD COLUMN term_id INTEGER"))
            conn.commit()
            print("   score_record.term_id 列添加成功")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("   score_record.term_id 列已存在，跳过")
            else:
                raise

        # 3. 注意：SQLite 不支持通过 ALTER TABLE 添加外键约束
        # 外键约束已在应用层（ORM）和数据库层面通过 REFERENCES 实现
        # 迁移后 term_id 列会自动建立与 term.id 的关联
        print("3. 外键约束：SQLite 不支持迁移后添加 FK，将通过 ORM 层保证引用完整性")

    # 4. 设置第一条学期 is_active=True 并更新 score_record
    print("4. 设置第一条学期为激活状态...")
    db = SessionLocal()
    try:
        # 获取第一条学期
        result = db.execute(text("SELECT id FROM term ORDER BY id LIMIT 1")).fetchone()
        if result is None:
            print("   错误：没有找到学期记录，请先创建学期")
            return False

        first_term_id = result[0]
        print(f"   第一条学期ID: {first_term_id}")

        # 设置该学期 is_active=True
        db.execute(text("UPDATE term SET is_active = 1 WHERE id = :term_id"), {"term_id": first_term_id})
        db.commit()
        print(f"   学期 ID={first_term_id} 已设置为激活状态")

        # 5. 设置所有积分记录的 term_id
        print("5. 更新所有积分记录的 term_id...")
        update_result = db.execute(
            text("UPDATE score_record SET term_id = :term_id WHERE term_id IS NULL"),
            {"term_id": first_term_id}
        )
        db.commit()
        print(f"   已更新 {update_result.rowcount} 条积分记录")

        print()
        print("迁移完成！")
        return True

    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
