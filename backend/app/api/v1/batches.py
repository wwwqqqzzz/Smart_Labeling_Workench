"""
导入批次管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ImportBatch, Conversation

router = APIRouter()


@router.get("/batches")
async def get_import_batches(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取导入批次列表

    返回所有Excel导入记录，按时间倒序
    """
    batches = db.query(ImportBatch).order_by(
        ImportBatch.created_at.desc()
    ).offset(skip).limit(limit).all()

    # 获取每个批次的对话统计
    result = []
    for batch in batches:
        # 统计该批次各状态的对话数量
        total = db.query(Conversation).filter(
            Conversation.batch_id == batch.id
        ).count()

        pending = db.query(Conversation).filter(
            Conversation.batch_id == batch.id,
            Conversation.status == 'pending'
        ).count()

        approved = db.query(Conversation).filter(
            Conversation.batch_id == batch.id,
            Conversation.status == 'approved'
        ).count()

        batch_dict = batch.to_dict()
        batch_dict.update({
            'conversation_stats': {
                'total': total,
                'pending': pending,
                'approved': approved,
                'skipped': total - pending - approved
            }
        })
        result.append(batch_dict)

    return {
        "success": True,
        "data": result,
        "total": len(result)
    }


@router.get("/batches/{batch_id}")
async def get_batch_detail(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个批次详情
    """
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 获取该批次的对话
    conversations = db.query(Conversation).filter(
        Conversation.batch_id == batch_id
    ).order_by(Conversation.id).limit(10).all()

    return {
        "success": True,
        "data": {
            "batch": batch.to_dict(),
            "conversations": [
                {
                    "id": c.id,
                    "raw_text": c.raw_text[:100] + "..." if len(c.raw_text) > 100 else c.raw_text,
                    "status": c.status,
                    "manual_tag": c.manual_tag
                }
                for c in conversations
            ]
        }
    }


@router.delete("/batches/{batch_id}")
async def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    删除整个批次及其所有对话

    ⚠️ 警告：此操作将删除该批次的所有对话，不可恢复！
    """
    try:
        # 查找批次
        batch = db.query(ImportBatch).filter(
            ImportBatch.id == batch_id
        ).first()

        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")

        # 删除该批次的所有对话
        deleted_count = db.query(Conversation).filter(
            Conversation.batch_id == batch_id
        ).delete()

        # 删除批次记录
        db.delete(batch)
        db.commit()

        return {
            "success": True,
            "message": f"已删除批次 #{batch_id} 及其 {deleted_count} 条对话"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )
