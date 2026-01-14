"""
Excel导入API路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
from datetime import datetime
from typing import Dict, Any
from app.services.data_importer import DataImporter
from app.database import get_db
from app.models import ImportBatch

router = APIRouter()


@router.post("/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    导入Excel文件

    上传Excel文件并导入对话和标签数据到数据库
    自动创建导入批次记录
    """
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="只支持 .xlsx 或 .xls 格式的Excel文件"
        )

    # 创建导入批次记录
    batch = ImportBatch(
        file_name=file.filename,
        total_rows=0,
        imported_count=0,
        status='in_progress',
        uploaded_by='user'
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    print(f"✅ 创建导入批次: #{batch.id} - {file.filename}")

    # 保存到临时文件
    temp_path = f"/tmp/{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 获取可用的工作表
        importer = DataImporter(temp_path)
        sheets = importer.get_available_sheets()

        if not sheets:
            raise HTTPException(
                status_code=400,
                detail="无法读取Excel工作表，请检查文件格式"
            )

        print(f"发现工作表: {sheets}")

        # 导入对话数据（传入批次ID）
        conv_result = {"imported": 0, "total": 0, "success": False, "batch_id": batch.id}
        if "打标1月1期" in sheets:
            conv_result = importer.import_conversations("打标1月1期", batch_id=batch.id)
        elif any("打标" in s for s in sheets):
            # 查找包含"打标"的工作表
            sheet = next(s for s in sheets if "打标" in s)
            conv_result = importer.import_conversations(sheet, batch_id=batch.id)
        else:
            # 使用第一个工作表
            conv_result = importer.import_conversations(sheets[0], batch_id=batch.id)

        # 导入标签数据
        tag_result = {"imported": 0, "total": 0, "success": False}
        if "标准化标签" in sheets:
            tag_result = importer.import_tags("标准化标签")

        # 更新批次状态
        batch.total_rows = conv_result.get('total', 0)
        batch.imported_count = conv_result.get('imported', 0)
        batch.status = 'completed' if conv_result.get('success') else 'failed'
        if not conv_result.get('success'):
            batch.error_message = conv_result.get('error', '导入失败')
        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "batch_id": batch.id,
                    "batch_info": {
                        "id": batch.id,
                        "file_name": batch.file_name,
                        "imported_count": batch.imported_count,
                        "created_at": batch.created_at.isoformat()
                    },
                    "conversations": conv_result,
                    "tags": tag_result,
                    "available_sheets": sheets
                }
            }
        )

    except HTTPException:
        # 更新批次状态为失败
        batch.status = 'failed'
        batch.error_message = '导入请求失败'
        db.commit()
        raise
    except Exception as e:
        print(f"导入失败: {str(e)}")
        # 更新批次状态为失败
        batch.status = 'failed'
        batch.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"导入失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/sheets")
async def get_excel_sheets():
    """
    获取Excel文件中的所有工作表名称（用于测试）
    """
    return {
        "message": "请使用 POST /api/v1/import/excel 上传文件",
        "note": "工作表信息将在导入时自动检测"
    }
