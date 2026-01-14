from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    """审核记录表"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    conv_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    ai_tag = Column(Text, nullable=False, comment="AI标签，JSON")
    manual_tag = Column(Text, comment="人工标签，JSON")
    is_correct = Column(Boolean, comment="是否正确")
    confidence = Column(Float, comment="置信度")
    recommendations = Column(Text, comment="推荐结果，JSON")
    auditor = Column(String(50), comment="审核人")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    conversation = relationship("Conversation", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, conv_id={self.conv_id})>"
