"""
Excel导出API路由
"""
from fastapi import APIRouter, Query
from fastapi.responses import Response
from typing import Optional
from app.services.data_exporter import DataExporter

router = APIRouter()


@router.get("/excel")
async def export_excel(
    status: Optional[str] = Query(None, description="状态过滤: pending/approved/skipped")
):
    """
    导出对话数据到Excel文件

    - **status**: 可选的状态过滤参数
      - 不传: 导出所有数据
      - pending: 仅导出待审核
      - approved: 仅导出已审核
      - skipped: 仅导出已跳过
    """
    try:
        exporter = DataExporter()
        excel_data = exporter.export_to_excel(status_filter=status)

        # 生成文件名
        filename = f"conversations_{status if status else 'all'}.xlsx"

        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        return Response(
            content=f"导出失败: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )


@router.get("/statistics")
async def get_statistics():
    """获取审核统计信息"""
    try:
        exporter = DataExporter()
        stats = exporter.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
