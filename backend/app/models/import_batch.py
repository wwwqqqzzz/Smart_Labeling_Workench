"""
导入批次模型
跟踪每次Excel导入
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ImportBatch(Base):
    """Excel导入批次记录"""
    __tablename__ = 'import_batches'

    id = Column(Integer, primary_key=True, index=True, comment='批次ID')
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    total_rows = Column(Integer, default=0, comment='总行数')
    imported_count = Column(Integer, default=0, comment='成功导入数量')
    status = Column(String(50), default='completed', comment='状态: completed/failed/partial')
    error_message = Column(String(1000), comment='错误信息')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='导入时间')
    uploaded_by = Column(String(100), default='system', comment='上传者')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'total_rows': self.total_rows,
            'imported_count': self.imported_count,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'uploaded_by': self.uploaded_by
        }
