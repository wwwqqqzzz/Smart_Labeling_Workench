from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import json

from app.database import get_db
from app.models import Conversation
from app.schemas.conversation import (
    ConversationResponse,
    ConversationListResponse,
    ConversationUpdate
)

router = APIRouter()


@router.get("/conversations/stats/global")
async def get_global_stats(db: Session = Depends(get_db)):
    """
    获取全局审核统计信息
    返回所有对话的统计数据，不受分页影响
    """
    total = db.query(func.count(Conversation.id)).scalar()

    pending = db.query(func.count(Conversation.id)).filter(
        Conversation.status == 'pending'
    ).scalar()

    approved = db.query(func.count(Conversation.id)).filter(
        Conversation.status == 'approved'
    ).scalar()

    skipped = db.query(func.count(Conversation.id)).filter(
        Conversation.status == 'skipped'
    ).scalar()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "skipped": skipped
    }


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    batch_id: Optional[int] = Query(None, description="批次ID过滤"),
    db: Session = Depends(get_db)
):
    """
    获取对话列表

    - **page**: 页码，从1开始
    - **limit**: 每页数量，1-100
    - **status**: 状态过滤 (pending/approved/skipped)
    - **batch_id**: 批次ID过滤（筛选特定批次的对话）
    """
    # 构建查询
    query = db.query(Conversation)

    if status:
        query = query.filter(Conversation.status == status)

    if batch_id is not None:
        query = query.filter(Conversation.batch_id == batch_id)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * limit
    conversations = query.offset(offset).limit(limit).all()

    return ConversationListResponse(
        total=total,
        page=page,
        limit=limit,
        items=conversations
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """获取单条对话"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    return conversation


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """
    更新对话标签

    - **manual_tag**: 人工标签列表
    - **status**: 状态 (pending/approved/skipped)
    - **auditor**: 审核人
    - **is_difficult**: 是否疑难案例
    - **difficult_note**: 疑难案例备注
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 更新字段
    if conversation_update.manual_tag is not None:
        conversation.manual_tag = json.dumps(
            conversation_update.manual_tag,
            ensure_ascii=False
        )

    if conversation_update.status is not None:
        conversation.status = conversation_update.status

    if conversation_update.is_difficult is not None:
        conversation.is_difficult = conversation_update.is_difficult

    if conversation_update.difficult_note is not None:
        conversation.difficult_note = conversation_update.difficult_note

    db.commit()
    db.refresh(conversation)

    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    删除单条对话

    - **conversation_id**: 对话ID
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.delete(conversation)
    db.commit()

    return {
        "success": True,
        "message": f"对话 #{conversation_id} 已删除"
    }


@router.delete("/conversations")
async def delete_all_conversations(
    db: Session = Depends(get_db)
):
    """
    清空所有对话

    ⚠️ 警告：此操作将删除数据库中的所有对话，不可恢复！
    """
    try:
        # 获取当前总数
        total = db.query(Conversation).count()

        # 删除所有
        db.query(Conversation).delete()
        db.commit()

        return {
            "success": True,
            "message": f"已清空 {total} 条对话"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"清空失败: {str(e)}"
        )


@router.post("/conversations/batch-delete")
async def delete_conversations_batch(
    ids: list[int],
    db: Session = Depends(get_db)
):
    """
    批量删除对话

    - **ids**: 对话ID列表
    """
    try:
        # 查找要删除的对话
        conversations = db.query(Conversation).filter(
            Conversation.id.in_(ids)
        ).all()

        if not conversations:
            raise HTTPException(status_code=404, detail="未找到指定对话")

        deleted_count = len(conversations)

        # 批量删除
        for conv in conversations:
            db.delete(conv)

        db.commit()

        return {
            "success": True,
            "message": f"已删除 {deleted_count} 条对话"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"批量删除失败: {str(e)}"
        )
