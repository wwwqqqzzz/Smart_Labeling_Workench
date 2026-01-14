from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Tag(Base):
    """标签表"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="标签名称")
    category = Column(String(50), nullable=False, comment="分类")
    definition = Column(Text, comment="标签定义")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"
