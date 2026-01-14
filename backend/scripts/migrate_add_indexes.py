"""
数据库迁移脚本：添加性能索引

运行方式：
docker exec smartlabelingworkbench-backend-1 python scripts/migrate_add_indexes.py
"""
from app.database import engine, Base
from app.models import Conversation, Tag
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """添加数据库索引"""
    logger.info("开始数据库迁移：添加性能索引...")

    try:
        # 重新创建表结构（会添加索引）
        # 注意：这不会删除现有数据
        Base.metadata.create_all(bind=engine, checkfirst=True)

        logger.info("✅ 索引创建成功！")

        # 验证索引
        from sqlalchemy import inspect
        inspector = inspect(engine)

        indexes = inspector.get_indexes('conversations')
        logger.info(f"conversations 表的索引: {[idx['name'] for idx in indexes]}")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    migrate()
