"""
Excel数据导出服务
"""
import pandas as pd
from typing import List
from sqlalchemy.orm import Session
from app.models import Conversation
from app.database import SessionLocal
import io


class DataExporter:
    """Excel数据导出器"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def export_to_excel(self, status_filter: str = None) -> bytes:
        """
        导出对话数据到Excel
        
        Args:
            status_filter: 状态过滤 (pending/approved/skipped/None)
            
        Returns:
            Excel文件的二进制数据
        """
        # 构建查询
        query = self.db.query(Conversation)
        
        if status_filter:
            query = query.filter(Conversation.status == status_filter)
        
        conversations = query.all()
        
        # 转换为DataFrame
        data = []
        for conv in conversations:
            # 解析JSON标签
            try:
                import json
                driver_tag = json.loads(conv.driver_tag) if conv.driver_tag else []
                manual_tag = json.loads(conv.manual_tag) if conv.manual_tag else []
            except:
                driver_tag = []
                manual_tag = []
            
            data.append({
                'ID': conv.id,
                '对话内容': conv.raw_text,
                'AI标签': ', '.join(driver_tag) if isinstance(driver_tag, list) else str(driver_tag),
                '人工标签': ', '.join(manual_tag) if isinstance(manual_tag, list) else str(manual_tag),
                '状态': {
                    'pending': '待审核',
                    'approved': '已审核',
                    'skipped': '已跳过'
                }.get(conv.status, conv.status),
                '字段长度': conv.field_length or '',
                '创建时间': conv.created_at.strftime('%Y-%m-%d %H:%M:%S') if conv.created_at else '',
                '更新时间': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S') if conv.updated_at else ''
            })
        
        df = pd.DataFrame(data)
        
        # 写入Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='已审核对话')
            
            # 获取工作表以设置列宽
            worksheet = writer.sheets['已审核对话']
            
            # 设置列宽
            worksheet.column_dimensions['A'].width = 8   # ID
            worksheet.column_dimensions['B'].width = 50  # 对话内容
            worksheet.column_dimensions['C'].width = 30  # AI标签
            worksheet.column_dimensions['D'].width = 30  # 人工标签
            worksheet.column_dimensions['E'].width = 10  # 状态
            worksheet.column_dimensions['F'].width = 10  # 字段长度
            worksheet.column_dimensions['G'].width = 20  # 创建时间
            worksheet.column_dimensions['H'].width = 20  # 更新时间
        
        output.seek(0)
        return output.read()
    
    def get_statistics(self) -> dict:
        """获取审核统计信息"""
        total = self.db.query(Conversation).count()
        pending = self.db.query(Conversation).filter(Conversation.status == 'pending').count()
        approved = self.db.query(Conversation).filter(Conversation.status == 'approved').count()
        skipped = self.db.query(Conversation).filter(Conversation.status == 'skipped').count()
        
        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'skipped': skipped
        }
