"""
段位路由模块 (Rank Router)

此模块处理与段位(Rank)相关的 API 请求：
1. GET /api/ranks - 获取段位列表
2. GET /api/ranks/{rank_id} - 获取指定段位
3. POST /api/ranks - 创建段位
4. PUT /api/ranks/{rank_id} - 更新段位
5. DELETE /api/ranks/{rank_id} - 删除段位

数据模型：Rank
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.models import Rank
from app.schemas.rank_schema import RankCreate, RankUpdate, RankResponse

router = APIRouter(prefix="/api/ranks", tags=["ranks"])


@router.get("", response_model=List[RankResponse])
def list_ranks(db: Session = Depends(get_db)):
    """获取所有段位列表，按 display_order 排序"""
    ranks = db.query(Rank).order_by(Rank.display_order).all()
    return ranks


@router.get("/{rank_id}", response_model=RankResponse)
def get_rank(rank_id: int, db: Session = Depends(get_db)):
    """获取指定段位"""
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    return rank


@router.post("", response_model=RankResponse)
def create_rank(rank_data: RankCreate, db: Session = Depends(get_db)):
    """创建新段位"""
    rank = Rank(**rank_data.model_dump())
    db.add(rank)
    db.commit()
    db.refresh(rank)
    return rank


@router.put("/{rank_id}", response_model=RankResponse)
def update_rank(rank_id: int, rank_data: RankUpdate, db: Session = Depends(get_db)):
    """更新指定段位"""
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    update_data = rank_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rank, key, value)
    db.commit()
    db.refresh(rank)
    return rank


@router.delete("/{rank_id}")
def delete_rank(rank_id: int, db: Session = Depends(get_db)):
    """删除指定段位"""
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    db.delete(rank)
    db.commit()
    return {"message": "删除成功"}
