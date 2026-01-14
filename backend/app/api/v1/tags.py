from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Tag
from app.schemas.tag import TagResponse

router = APIRouter()


@router.get("/tags", response_model=List[TagResponse])
async def get_tags(
    category: Optional[str] = Query(None, description="分类过滤"),
    db: Session = Depends(get_db)
):
    """
    获取所有标签

    - **category**: 可选，按分类过滤标签
    """
    query = db.query(Tag)

    if category:
        query = query.filter(Tag.category == category)

    tags = query.all()
    return tags


@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """获取单个标签详情"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="标签不存在")

    return tag
