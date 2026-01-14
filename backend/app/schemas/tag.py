from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TagBase(BaseModel):
    """标签基础模型"""
    name: str
    category: str
    definition: Optional[str] = None


class TagCreate(TagBase):
    """创建标签"""
    pass


class TagResponse(TagBase):
    """标签响应"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
