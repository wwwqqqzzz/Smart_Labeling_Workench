"""
生成测试对话数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Conversation, Tag
import json
import random
from datetime import datetime, timedelta

# 测试对话模板
TEST_CONVERSATIONS = [
    {
        "raw_text": "司机：你好，我看到你发布的货源信息，从上海到北京的货物。$_$货主：是的，10吨钢材，尾板车，4.2米厢式车。$_$司机：好的，我可以接，明天能装货吗？$_$货主：可以，上午9点，地址是浦东新区XX路XX号。",
        "driver_tag": ["尾板车", "4.2米厢式车", "钢材运输"],
        "category": "车辆类型"
    },
    {
        "raw_text": "司机：您好，请问这个从广州到深圳的货还在吗？$_$货主：在的，水果，需要冷链车。$_$司机：我有冷链车，多少钱一吨？$_$货主：300元/吨，大概5吨。$_$司机：好的，接了。",
        "driver_tag": ["冷链车", "水果运输", "短途"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：老板，你这个杭州到宁波的货，高栏车行吗？$_$货主：不行，要厢式车，怕下雨。$_$司机：厢式车也行，9.6米的那种可以吗？$_$货主：可以，今天下午能到吗？$_$司机：没问题，2小时就能到。",
        "driver_tag": ["厢式车", "9.6米", "短途"],
        "category": "车辆类型"
    },
    {
        "raw_text": "司机：你好，我看到你发的从成都到重庆的设备运输，需要什么车？$_$货主：急转弯路段多，需要经验丰富的司机，大件运输。$_$司机：我跑了10年了，熟悉这条路，用什么车？$_$货主：13米低平板，有特种运输证吗？$_$司机：有的，证件齐全。",
        "driver_tag": ["大件运输", "13米低平板", "特种运输", "山区路段"],
        "category": "特殊运输"
    },
    {
        "raw_text": "司机：您好，这个建材运输，从武汉到长沙，多少钱？$_$货主：散装水泥，需要罐车，280元/吨。$_$司机：有点低，300行不行？$_$货主：那就290吧，不还价了。$_$司机：行，我接了，明天能装货。",
        "driver_tag": ["罐车", "建材运输", "散装水泥", "议价"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：老板，这个快递件，从深圳到广州，多少钱一单？$_$货主：快递运输，需要面包车或小货车，按单算，8元/单。$_$司机：我有一辆4.2米厢式车，一次能拉200单，能不能便宜点？$_$货主：量大的话7.5元/单，你有多少单？$_$司机：大概150-200单每天。",
        "driver_tag": ["快递运输", "4.2米厢式车", "按单结算"],
        "category": "运输类型"
    },
    {
        "raw_text": "司机：您好，这个从北京到上海的冷链货，温控要求多少度？$_$货主：冷冻食品，需要-18度，全程冷链。$_$司机：我有冷机，双机组，保证温度。$_$货主：好的，运输过程中要注意温度记录。$_$司机：放心，有温度监控系统。",
        "driver_tag": ["冷链车", "冷冻食品", "温控-18度", "温度监控"],
        "category": "冷链运输"
    },
    {
        "raw_text": "司机：老板，这个危险品运输，我有押运员证。$_$货主：易燃液体，需要危险品车和押运员，从天津到河北。$_$司机：证件齐全，车辆也符合国标。$_$货主：好，要注意安全，按照危险品运输规定来。$_$司机：明白，会严格遵守。",
        "driver_tag": ["危险品运输", "易燃液体", "押运员", "国标车辆"],
        "category": "危险品运输"
    },
    {
        "raw_text": "司机：你好，这个家具运输，从上海到杭州，需要搬装吗？$_$货主：需要，家具，易碎品，需要小心搬运，有电梯。$_$司机：没问题，我们提供搬运服务，会用气泡膜包装。$_$货主：那好，价格多少？$_$司机：按车算，800元一趟。",
        "driver_tag": ["家具运输", "搬装服务", "易碎品", "包车"],
        "category": "服务类型"
    },
    {
        "raw_text": "司机：您好，这个砂石料运输，从矿山到工地，多远？$_$货主：大概30公里，需要自卸车，每天要拉30车。$_$司机：我有自卸车，按车算还是按吨算？$_$货主：按车算，150元/车。$_$司机：行，我派2辆车过去。",
        "driver_tag": ["自卸车", "砂石料", "短途", "工程运输"],
        "category": "工程运输"
    },
    {
        "raw_text": "司机：老板，这个从西安到兰州的货，什么时间能到？$_$货主：机电设备，3天时间，运费3000元。$_$司机：有点赶，不过可以，走高速。$_$货主：好，要注意防雨防潮。$_$司机：会用雨布盖好。",
        "driver_tag": ["机电设备", "长途", "高速运输", "防潮"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：你好，这个从南京到上海的服装运输，什么要求？$_$货主：服装，需要挂衣车，防止褶皱，总共500件。$_$司机：我有挂衣车，保证服装平整。$_$货主：好的，明天上午装货，下午能到吗？$_$司机：可以，4小时就到。",
        "driver_tag": ["挂衣车", "服装运输", "防褶皱", "短途"],
        "category": "专用车辆"
    },
    {
        "raw_text": "司机：您好，这个粮食运输，从东北到华北，怎么算？$_$货主：玉米，散装，需要粮食运输车，按吨算，200元/吨。$_$司机：量多大？$_$货主：大概30吨，可以分批运。$_$司机：好，我派两辆半挂车。",
        "driver_tag": ["粮食运输", "散装", "半挂车", "长途"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：老板，这个医药品运输，需要什么条件？$_$货主：药品，需要恒温车，2-8度，有GSP认证。$_$司机：我有符合GSP标准的车辆，温度记录完整。$_$货主：好，要注意药品安全，不能有破损。$_$司机：会用专用箱包装。",
        "driver_tag": ["恒温车", "药品运输", "2-8度", "GSP认证"],
        "category": "冷链运输"
    },
    {
        "raw_text": "司机：你好，这个从广州到东莞的汽配运输，需要什么车？$_$货主：汽车配件，需要厢式车，防止雨淋，大概3吨。$_$司机：4.2米厢式车可以吗？$_$货主：可以，价格多少？$_$司机：500元一趟，今天下午能到。",
        "driver_tag": ["汽配运输", "4.2米厢式车", "短途", "防雨"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：您好，这个从上海到宁波的集装箱运输，多少个柜？$_$货主：20尺柜2个，需要集装箱车，走高速。$_$司机：我有集装箱拖车，运费多少？$_$货主：1500元/柜，含装卸费。$_$司机：行，明天能装货。",
        "driver_tag": ["集装箱运输", "20尺柜", "拖车", "含装卸"],
        "category": "集装箱"
    },
    {
        "raw_text": "司机：老板，这个生鲜运输，从批发市场到超市，需要注意什么？$_$货主：蔬菜水果，需要冷链车，早上5点前到店。$_$司机：没问题，我晚上10点出发，保证时间。$_$货主：好，要注意保鲜，不能压坏。",
        "driver_tag": ["生鲜运输", "冷链车", "早市配送", "保鲜"],
        "category": "冷链运输"
    },
    {
        "raw_text": "司机：你好，这个从北京到天津的钢材运输，什么规格？$_$货主：螺纹钢，20吨，需要半挂车，长度13米。$_$司机：有13米半挂，能装，价格？$_$货主：800元，明天装货。$_$司机：行，接了。",
        "driver_tag": ["钢材运输", "半挂车", "13米", "建材"],
        "category": "货物类型"
    },
    {
        "raw_text": "司机：您好，这个展品运输，从展馆到仓库，需要什么服务？$_$货主：精密仪器，需要防震，专业搬运，有木箱包装。$_$司机：我们有气垫车，防震效果好，提供专业搬运团队。$_$货主：好，要小心操作，保险要买足。",
        "driver_tag": ["展品运输", "精密仪器", "气垫车", "防震"],
        "category": "特殊运输"
    }
]

# 标准化标签
TAG_DEFINITIONS = [
    {"name": "尾板车", "category": "车辆类型", "definition": "带有尾板（升降平台）的货车，可以自行装卸货物"},
    {"name": "4.2米厢式车", "category": "车辆类型", "definition": "车长4.2米的厢式货车，适合城市配送"},
    {"name": "冷链车", "category": "车辆类型", "definition": "带有制冷设备的货车，用于运输需要冷藏或冷冻的货物"},
    {"name": "9.6米", "category": "车辆类型", "definition": "车长9.6米的货车，属于中型货车"},
    {"name": "13米低平板", "category": "车辆类型", "definition": "车长13米的低平板货车，用于大件运输"},
    {"name": "罐车", "category": "车辆类型", "definition": "罐式货车，用于运输液体、散装水泥等"},
    {"name": "自卸车", "category": "车辆类型", "definition": "可以自动倾卸的货车，用于砂石料运输"},
    {"name": "半挂车", "category": "车辆类型", "definition": "半挂牵引车，载重量大，适合长途运输"},
    {"name": "挂衣车", "category": "专用车辆", "definition": "专门用于运输服装的货车，配有挂衣架"},
    {"name": "集装箱车", "category": "集装箱", "definition": "用于运输集装箱的拖车"},
    {"name": "气垫车", "category": "特殊运输", "definition": "配有气垫悬挂系统的货车，防震效果好"},
    {"name": "钢材运输", "category": "货物类型", "definition": "运输钢材、螺纹钢等建筑材料"},
    {"name": "水果运输", "category": "货物类型", "definition": "运输水果，通常需要冷链或通风"},
    {"name": "快递运输", "category": "运输类型", "definition": "快递包裹运输，通常按单结算"},
    {"name": "冷冻食品", "category": "冷链运输", "definition": "需要冷冻保存的食品，温度-18°C左右"},
    {"name": "危险品运输", "category": "危险品运输", "definition": "运输易燃、易爆、有毒等危险品"},
    {"name": "家具运输", "category": "服务类型", "definition": "运输家具，通常提供搬装服务"},
    {"name": "粮食运输", "category": "货物类型", "definition": "运输粮食作物，如玉米、小麦等"},
    {"name": "药品运输", "category": "冷链运输", "definition": "运输医药品，需要恒温，符合GSP标准"},
    {"name": "大件运输", "category": "特殊运输", "definition": "运输超宽、超高、超重的货物"},
    {"name": "建材运输", "category": "货物类型", "definition": "运输建筑材料，如砂石、水泥等"},
    {"name": "短途", "category": "距离", "definition": "运输距离在200公里以内"},
    {"name": "长途", "category": "距离", "definition": "运输距离超过500公里"},
]


def generate_test_data(num_conversations: int = 50):
    """生成测试数据"""
    db = SessionLocal()

    try:
        # 1. 先创建标签
        print("📦 创建标准化标签...")
        for tag_def in TAG_DEFINITIONS:
            existing_tag = db.query(Tag).filter(Tag.name == tag_def["name"]).first()
            if not existing_tag:
                tag = Tag(
                    name=tag_def["name"],
                    category=tag_def["category"],
                    definition=tag_def["definition"]
                )
                db.add(tag)

        db.commit()
        print(f"✅ 创建了 {len(TAG_DEFINITIONS)} 个标准化标签")

        # 2. 创建对话
        print(f"\n📝 生成测试对话数据...")

        # 生成多个批次，每个批次状态不同
        status_distribution = ["pending"] * 30 + ["approved"] * 15 + ["skipped"] * 5

        conversations_created = 0
        for i in range(num_conversations):
            # 随机选择模板
            template = random.choice(TEST_CONVERSATIONS)

            # 随机变化对话内容（避免完全重复）
            raw_text = template["raw_text"]
            if i % 3 == 0:  # 每3个对话就换一种表达
                raw_text = raw_text.replace("你好", "您好").replace("好的", "行").replace("可以", "没问题")

            # 随机状态
            status = status_distribution[min(i, len(status_distribution) - 1)]

            # 随机决定是否疑难案例（5%概率）
            is_difficult = random.random() < 0.05
            difficult_note = None
            if is_difficult:
                difficult_note = random.choice([
                    "标签定义不清晰",
                    "对话内容模糊",
                    "涉及多种货物类型",
                    "车辆类型不明确"
                ])

            # 创建对话
            conversation = Conversation(
                raw_text=raw_text,
                driver_tag=json.dumps(template["driver_tag"], ensure_ascii=False),
                manual_tag=json.dumps(template["driver_tag"], ensure_ascii=False) if status == "approved" else None,
                status=status,
                field_length=len(raw_text),
                is_difficult=is_difficult,
                difficult_note=difficult_note,
                created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                updated_at=datetime.now() if status != "pending" else None
            )
            db.add(conversation)
            conversations_created += 1

            if (i + 1) % 10 == 0:
                print(f"   已生成 {i + 1} 条对话...")

        db.commit()
        print(f"\n✅ 成功生成 {conversations_created} 条测试对话")

        # 3. 统计数据
        total = db.query(Conversation).count()
        pending = db.query(Conversation).filter(Conversation.status == "pending").count()
        approved = db.query(Conversation).filter(Conversation.status == "approved").count()
        skipped = db.query(Conversation).filter(Conversation.status == "skipped").count()
        difficult = db.query(Conversation).filter(Conversation.is_difficult == True).count()
        tags = db.query(Tag).count()

        print("\n📊 数据统计:")
        print(f"   总对话数: {total}")
        print(f"   待审核: {pending}")
        print(f"   已通过: {approved}")
        print(f"   已跳过: {skipped}")
        print(f"   疑难案例: {difficult}")
        print(f"   标签数: {tags}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 智能打标便捷器 - 测试数据生成器")
    print("=" * 60)

    # 先确保表存在
    print("\n🔧 检查数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表准备完成")

    # 生成测试数据
    num = 50  # 生成50条测试数据
    if len(sys.argv) > 1:
        num = int(sys.argv[1])

    generate_test_data(num)

    print("\n" + "=" * 60)
    print("✅ 测试数据生成完成！")
    print("=" * 60)
