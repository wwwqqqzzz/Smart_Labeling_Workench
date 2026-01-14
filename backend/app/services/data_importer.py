"""
Excel数据导入服务
"""
import pandas as pd
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Conversation, Tag
from app.database import SessionLocal


class DataImporter:
    """Excel数据导入器"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.db = SessionLocal()
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def import_conversations(
        self,
        sheet_name: str = "打标1月1期",
        batch_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        导入对话数据

        Args:
            sheet_name: Excel工作表名称
            batch_id: 导入批次ID

        Returns:
            导入结果统计
        """
        try:
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            print(f"Excel列名: {df.columns.tolist()}")
            print(f"数据行数: {len(df)}")
            print(f"批次ID: {batch_id}")

            count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # 处理司机标签（可能是列表或字符串）
                    driver_tag = row.get('司机标签')
                    if isinstance(driver_tag, list):
                        driver_tag_str = json.dumps(driver_tag, ensure_ascii=False)
                    else:
                        driver_tag_str = str(driver_tag) if pd.notna(driver_tag) else None

                    conversation = Conversation(
                        raw_text=row.get('转义后的文本内容', ''),
                        driver_tag=driver_tag_str,
                        field_length=int(row.get('字段长度', 0)) if pd.notna(row.get('字段长度')) else None,
                        status='pending',
                        batch_id=batch_id  # 关联批次
                    )
                    self.db.add(conversation)
                    count += 1

                    # 每100条提交一次
                    if count % 100 == 0:
                        self.db.commit()
                        print(f"已导入 {count} 条数据...")

                except Exception as e:
                    error_msg = f"第 {index + 1} 行导入失败: {str(e)}"
                    errors.append(error_msg)
                    print(error_msg)

            # 提交剩余数据
            self.db.commit()

            return {
                "success": True,
                "imported": count,
                "total": len(df),
                "errors": errors
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "imported": 0,
                "total": 0
            }
    
    def import_tags(
        self, 
        sheet_name: str = "标准化标签"
    ) -> Dict[str, Any]:
        """
        导入标签数据
        
        Args:
            sheet_name: Excel工作表名称
            
        Returns:
            导入结果统计
        """
        try:
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            print(f"标签工作表列名: {df.columns.tolist()}")
            print(f"标签数据行数: {len(df)}")
            
            count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    tag = Tag(
                        name=str(row.get('标准化标签', '')),
                        category='其他',
                        definition=str(row.get('备注说明', ''))
                    )
                    self.db.add(tag)
                    count += 1
                    
                except Exception as e:
                    error_msg = f"第 {index + 1} 行标签导入失败: {str(e)}"
                    errors.append(error_msg)
                    print(error_msg)
            
            self.db.commit()
            
            return {
                "success": True,
                "imported": count,
                "total": len(df),
                "errors": errors
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "imported": 0,
                "total": 0
            }
    
    def get_available_sheets(self) -> list[str]:
        """获取Excel中所有工作表名称"""
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            return excel_file.sheet_names
        except Exception as e:
            print(f"读取工作表失败: {str(e)}")
            return []
