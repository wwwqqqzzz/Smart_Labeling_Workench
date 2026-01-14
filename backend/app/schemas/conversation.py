from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ConversationBase(BaseModel):
    """对话基础模型"""
    raw_text: str
    driver_tag: Optional[str] = None
    status: str = "pending"


class ConversationCreate(ConversationBase):
    """创建对话"""
    pass


class ConversationUpdate(BaseModel):
    """更新对话"""
    manual_tag: Optional[List[str]] = None
    status: Optional[str] = None
    auditor: Optional[str] = None
    is_difficult: Optional[bool] = None
    difficult_note: Optional[str] = None


class ConversationResponse(ConversationBase):
    """对话响应"""
    id: int
    manual_tag: Optional[str] = None
    field_length: Optional[int] = None
    is_difficult: bool = False
    difficult_note: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    total: int
    page: int
    limit: int
    items: List[ConversationResponse]
