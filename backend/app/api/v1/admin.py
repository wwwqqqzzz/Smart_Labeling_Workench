from fastapi import APIRouter, HTTPException
from app.database import engine
from app.models.conversation import Base
from app.models.tag import Tag
from app.models.import_batch import ImportBatch
from sqlalchemy import text
import os

router = APIRouter()

@router.post("/init-db")
async def init_database():
    """初始化数据库表（用于生产环境）"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)

        # 验证表是否创建成功
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]

        return {
            "success": True,
            "message": "数据库初始化成功",
            "tables": tables
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")

@router.get("/check-db")
async def check_database():
    """检查数据库状态"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]

        # 检查表是否有数据
        table_info = {}
        for table in tables:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_info[table] = count
            except:
                table_info[table] = 0

        return {
            "success": True,
            "tables": tables,
            "table_info": table_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
