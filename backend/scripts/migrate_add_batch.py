"""
数据库迁移脚本：添加导入批次功能
添加 import_batches 表和 batch_id 字段
"""
import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


def migrate():
    """执行数据库迁移"""
    # 从 DATABASE_URL 中提取 SQLite 文件路径
    db_path = settings.DATABASE_URL.replace('sqlite:///', '')

    print(f"📁 数据库路径: {db_path}")

    # 使用 sqlite3 直接操作
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n🔄 开始迁移...")

        # 1. 创建 import_batches 表
        print("  ▶ 创建 import_batches 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name VARCHAR(255) NOT NULL,
                total_rows INTEGER DEFAULT 0,
                imported_count INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'completed',
                error_message VARCHAR(1000),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploaded_by VARCHAR(100) DEFAULT 'system'
            )
        """)

        # 2. 检查并添加 batch_id 列到 conversations 表
        print("  ▶ 检查 conversations 表字段...")
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'batch_id' not in columns:
            print("  ▶ 添加 batch_id 列...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN batch_id INTEGER REFERENCES import_batches(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_batch_id ON conversations(batch_id)")
        else:
            print("  ✓ batch_id 列已存在")

        if 'auditor' not in columns:
            print("  ▶ 添加 auditor 列...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN auditor VARCHAR(100)")
        else:
            print("  ✓ auditor 列已存在")

        # 提交更改
        conn.commit()
        print("\n✅ 迁移完成！")

        # 显示表结构
        print("\n📊 import_batches 表结构:")
        cursor.execute("PRAGMA table_info(import_batches)")
        for col in cursor.fetchall():
            print(f"  - {col[1]}: {col[2]}")

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
