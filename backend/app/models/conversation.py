from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Conversation(Base):
    """对话表"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False, comment="原始对话文本")
    driver_tag = Column(String(500), comment="AI标签，JSON格式")
    manual_tag = Column(String(500), comment="人工标签，JSON格式")
    status = Column(String(20), default="pending", comment="状态: pending/approved/skipped")
    field_length = Column(Integer, comment="对话长度")
    is_difficult = Column(Boolean, default=False, comment="是否为疑难案例")
    difficult_note = Column(Text, comment="疑难案例备注")
    batch_id = Column(Integer, ForeignKey('import_batches.id'), index=True, comment="导入批次ID")
    auditor = Column(String(100), comment="审核人")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 添加索引以优化查询性能
    __table_args__ = (
        Index('ix_conversations_status', 'status'),
        Index('ix_conversations_created_at', 'created_at'),
        Index('ix_conversations_status_updated', 'status', 'updated_at'),
        Index('ix_conversations_is_difficult', 'is_difficult'),
        Index('ix_conversations_batch_id', 'batch_id'),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, status={self.status}, is_difficult={self.is_difficult})>"
