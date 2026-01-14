import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import Conversation, Tag, AuditLog


def init_db():
    """初始化数据库，创建所有表"""
    print("🔧 开始创建数据库表...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("✅ 数据库初始化成功！")
    print(f"📍 数据库文件: {engine.url}")
    print("\n📊 已创建的表:")
    print("   - conversations (对话表)")
    print("   - tags (标签表)")
    print("   - audit_logs (审核记录表)")


if __name__ == "__main__":
    init_db()
