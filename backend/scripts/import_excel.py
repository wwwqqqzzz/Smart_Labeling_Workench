"""
Excel数据导入脚本（手动执行）
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_importer import DataImporter


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python scripts/import_excel.py <excel文件路径>")
        print("示例: python scripts/import_excel.py /path/to/your/file.xlsx")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    
    if not os.path.exists(excel_path):
        print(f"错误: 文件不存在 - {excel_path}")
        sys.exit(1)
    
    print(f"开始导入Excel文件: {excel_path}")
    print("=" * 60)
    
    try:
        importer = DataImporter(excel_path)
        
        # 获取可用工作表
        sheets = importer.get_available_sheets()
        print(f"\n✅ 发现工作表: {sheets}")
        
        # 导入对话数据
        print("\n📝 开始导入对话数据...")
        conv_result = importer.import_conversations()
        
        if conv_result["success"]:
            print(f"✅ 对话导入成功: {conv_result['imported']}/{conv_result['total']} 条")
            if conv_result.get("errors"):
                print(f"⚠️  错误数量: {len(conv_result['errors'])}")
        else:
            print(f"❌ 对话导入失败: {conv_result.get('error')}")
        
        # 导入标签数据
        print("\n🏷️  开始导入标签数据...")
        tag_result = importer.import_tags()
        
        if tag_result["success"]:
            print(f"✅ 标签导入成功: {tag_result['imported']}/{tag_result['total']} 条")
        else:
            print(f"⚠️  标签导入失败或不存在该工作表")
        
        print("\n" + "=" * 60)
        print("🎉 导入完成！")
        
    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
