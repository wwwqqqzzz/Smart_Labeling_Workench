"""
RAG推荐API路由
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx
from app.services.rag.rag_service import get_rag_recommender
from app.database import SessionLocal
from app.models import Conversation

router = APIRouter()

# 完整的标准化标签定义（包含详细说明）
TAG_DEFINITIONS = {
    # 路线相关
    "不走高速": "路线可经过高速，但货主要求不走高速，司机同意不走",
    "无高速费": "货主不出高速费，司机同意，但走高速",
    "部分过路/桥/船/高速费": "货主承担部分过路/桥/船/高速费，司机同意",
    "过路/桥/船/高速费": "货主承担全部过路/桥/船/高速费",

    # 车辆尺寸
    "车厢长X米": "司机描述自己的车厢长度（如：车厢长4.2米、6.8米等）",
    "车宽X米": "司机描述自己的车厢宽度（如：车宽2米、2.3米等）",
    "车高X米": "司机描述自己的车厢高度（如：车高2.2米、2.5米等）",
    "车容量X方": "司机描述自己的车可以装多少方。拼车场景下剩余空间不算",
    "车载重X吨": "司机描述自己的车可以装多少吨",

    # 车型分类
    "面包车": "优先标注明确的车型，如无表述，再标注非XX。如：司机表达自己不是平板，是厢货，应该打标为厢货；司机表达自己不是平板，没有说具体是什么车型，应该打标为非平板",
    "高栏": "高栏车型",
    "厢货": "厢式货车",
    "平板": "平板车型",
    "依维柯": "依维柯车型",
    "飞翼车": "飞翼车型（侧门像翅膀一样打开）",
    "非平板": "司机明确表示不是平板车",
    "非面包车": "司机明确表示不是面包车",
    "非高栏": "司机明确表示不是高栏车",
    "非厢货": "司机明确表示不是厢货车",

    # 尾板相关
    "尾板车": "车辆装有尾板",
    "尾板费": "有尾板，且司货双方同意了尾板费",
    "无尾板": "车辆没有尾板",

    # 装卸相关
    "装卸费": "需要司机装卸，且司机表示需要装卸费用",
    "搬运装卸": "需要司机自己装卸（司机要了搬运费，但货主拒绝，司机认可不给也行）",
    "搭把手": "有人装卸，司机需要帮忙，且无搬运费用，提到费用的归到装卸费",
    "不搬运": "司机明确拒绝不帮忙搬运",

    # 跟车要求
    "跟车X人": "不能跟车、跟车1人、跟车2人及以上；按照司机描述可跟车的人数打标",

    # 拼车
    "拼车单": "司机自行拼车或者可接受拼车",

    # 装卸要求
    "X装X卸": "货源为X装X卸，司机接受，费用未谈拢也算",

    # 侧门类型
    "侧门单开": "至少有一侧可以开一扇门",
    "侧门双开": "至少有一侧可以开两扇门",
    "侧门全开": "侧边门可以全部打开",
    "侧边栏，侧门全开": "侧边门可以全部打开，但是顶上有栏杆，无法拆卸",
    "双边侧门全开": "两边的侧门都可以全开",
    "非侧开门": "侧边门不能打开，或者司机不愿意打开也算",

    # 时间要求
    "明日卸": "明天卸货",
    "明日装卸": "明天装卸货",
    "固定/上班时间装卸": "在工作时间（8:00-18:00）装卸",
    "夜间运输": "在夜间（18:00-次日8:00）运输或装卸",

    # 车辆动力
    "新能源": "电车也属于新能源",
    "油车": "燃油车",

    # 车门类型
    "双开门": "区别于侧门双开，指尾部双开门",
    "非双开门": "尾部不是双开门",

    # 座位相关
    "无座车": "货运版，本身没有座位；或者客运版，座位都拆了，折叠的不算",

    # 辅助工具
    "小推车": "司机当下有才算，如果说要回家取，那是无小推车",
    "无小推车": "司机当下没有小推车",

    # 车顶类型
    "开顶车厢": "车顶可以全部打开",
    "不可开顶": "车顶不能打开",
    "不可全开顶": "高栏车，滑动雨布，雨布可不拆，因此有一部分无法打开",

    # 雨布绳子
    "雨布": "车上有雨布、雨棚都算",
    "无雨布": "车上没有雨布",
    "有绳子": "车上有绳子、网兜都算",
    "无绳子": "车上没有绳子，或者车辆无法用绳子固定",

    # 费用相关
    "进出场费": "如有提及，且货主愿意出就算",
    "等待费": "提及等待费用",
    "停车费": "提及停车费用",
}

ALL_TAGS = list(TAG_DEFINITIONS.keys())


class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    conversation_id: Optional[int] = None
    text: Optional[str] = None
    top_k: int = Query(3, ge=1, le=10, description="返回最相似的K个对话")


@router.post("/tags")
async def recommend_tags(request: RecommendationRequest):
    """
    基于相似对话推荐标签
    
    - **conversation_id**: 对话ID（如果提供，自动获取文本）
    - **text**: 对话文本（如果不提供conversation_id，则必须提供text）
    - **top_k**: 返回最相似的K个对话
    """
    try:
        # 获取对话文本
        text = request.text
        if request.conversation_id and not text:
            db = SessionLocal()
            try:
                conversation = db.query(Conversation).filter(
                    Conversation.id == request.conversation_id
                ).first()
                
                if not conversation:
                    raise HTTPException(status_code=404, detail="对话不存在")
                
                text = conversation.raw_text
            finally:
                db.close()
        
        if not text:
            raise HTTPException(status_code=400, detail="必须提供conversation_id或text")
        
        # 获取推荐
        recommender = get_rag_recommender()
        result = recommender.recommend_tags(
            conversation_text=text,
            top_k=request.top_k
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"推荐失败: {str(e)}",
            "recommendations": [],
            "confidence": 0.0
        }


@router.post("/index/build")
async def build_index():
    """
    构建或重建向量索引
    
    从所有已审核的对话构建向量索引
    """
    try:
        db = SessionLocal()
        try:
            # 获取所有已审核的对话
            conversations = db.query(Conversation).filter(
                Conversation.status == 'approved'
            ).all()
            
            # 转换为字典列表
            conv_list = []
            for conv in conversations:
                conv_dict = {
                    'id': conv.id,
                    'raw_text': conv.raw_text,
                    'manual_tag': conv.manual_tag
                }
                conv_list.append(conv_dict)
            
            # 构建索引
            recommender = get_rag_recommender()
            result = recommender.build_vector_index(conv_list)
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "message": f"构建索引失败: {str(e)}"
        }


@router.get("/index/stats")
async def get_index_stats():
    """获取向量索引统计信息"""
    try:
        recommender = get_rag_recommender()
        stats = recommender.get_index_stats()
        
        # 获取数据库统计
        db = SessionLocal()
        try:
            total_conv = db.query(Conversation).count()
            approved_conv = db.query(Conversation).filter(
                Conversation.status == 'approved'
            ).count()
            
            stats['database'] = {
                'total_conversations': total_conv,
                'approved_conversations': approved_conv
            }
        finally:
            db.close()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取统计失败: {str(e)}"
        }


async def call_glm_api(prompt: str, max_tokens: int = 2000) -> dict:
    """
    调用智谱GLM API进行AI分析
    """
    from app.config import settings

    api_key = settings.GLM_API_KEY or os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ [AI调用] 未配置GLM_API_KEY")
        return {"success": False, "error": "未配置GLM_API_KEY"}

    print(f"✅ [AI调用] 准备调用GLM API，prompt长度: {len(prompt)}字符")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
            )

            print(f"📡 [AI调用] API响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ [AI调用] 成功获取AI响应，内容长度: {len(content)}字符")
                print(f"📄 [AI响应] 前200字符: {content[:200]}...")
                return {"success": True, "content": content}
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                print(f"❌ [AI调用] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
    except Exception as e:
        print(f"❌ [AI调用] 异常: {str(e)}")
        return {"success": False, "error": str(e)}


async def analyze_initial_tags_with_ai(conversation_text: str, initial_tags: list) -> dict:
    """
    第一层AI分析：验证初始AI标签是否合适

    返回：{
        "appropriate_tags": ["标签1", "标签2"],  # 合适的标签
        "inappropriate_tags": ["标签3"],  # 不合适的标签
        "reasons": {"标签1": "合适理由", "标签3": "不合适理由"}
    }
    """
    if not initial_tags:
        print("⚠️ [第一层AI] 没有初始AI标签需要验证")
        return {"appropriate_tags": [], "inappropriate_tags": [], "reasons": {}}

    print(f"🔍 [第一层AI] 开始验证初始AI标签: {initial_tags}")

    # 构建标签定义说明
    tag_definitions_str = "\n".join([
        f"- {tag}: {TAG_DEFINITIONS.get(tag, '无说明')}"
        for tag in initial_tags
    ])

    prompt = f"""你是一个专业的货运对话标注专家。请分析以下司机与货主的对话内容，验证初始AI推荐的标签是否合适。

## 对话内容：
{conversation_text}

## 初始AI推荐的标签：
{tag_definitions_str}

## 你的任务：
请逐个分析每个初始AI标签，判断是否合适，并给出理由。

## 标签判断标准：
- **合适**：对话内容明确提到或暗示该标签所描述的特征
- **不合适**：对话内容未提及、相反、或不足以支持该标签

## 输出格式（严格按照JSON格式输出）：
{{
    "appropriate_tags": ["标签1", "标签2"],
    "inappropriate_tags": ["标签3"],
    "reasons": {{
        "标签1": "对话中提到xxx，符合该标签定义",
        "标签3": "对话中未提及xxx，不符合该标签定义"
    }}
}}

请只输出JSON，不要输出其他内容。"""

    result = await call_glm_api(prompt, max_tokens=1500)

    if not result.get("success"):
        print(f"❌ [第一层AI] AI调用失败: {result.get('error')}")
        return {"appropriate_tags": [], "inappropriate_tags": initial_tags, "reasons": {}}

    try:
        import json
        content = result["content"]

        # 提取JSON部分（处理可能的markdown代码块）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        analysis = json.loads(content)
        appropriate = analysis.get("appropriate_tags", [])
        inappropriate = analysis.get("inappropriate_tags", [])
        reasons = analysis.get("reasons", {})

        print(f"✅ [第一层AI] 验证完成: {len(appropriate)}个合适, {len(inappropriate)}个不合适")
        print(f"   ✓ 合适: {appropriate}")
        print(f"   ✗ 不合适: {inappropriate}")

        return {
            "appropriate_tags": appropriate,
            "inappropriate_tags": inappropriate,
            "reasons": reasons
        }
    except Exception as e:
        print(f"❌ [第一层AI] JSON解析失败: {str(e)}")
        # 如果解析失败，保留所有标签为不合适
        return {
            "appropriate_tags": [],
            "inappropriate_tags": initial_tags,
            "reasons": {},
            "parse_error": str(e)
        }


async def recommend_tags_from_conversation_with_ai(conversation_text: str, exclude_tags: list = None) -> dict:
    """
    第二层AI分析：深入分析对话内容，推荐合适的标签

    返回：{
        "recommended_tags": ["标签1", "标签2"],
        "reasons": {"标签1": "推荐理由1", "标签2": "推荐理由2"}
    }
    """
    exclude_tags = exclude_tags or []
    print(f"🔍 [第二层AI] 开始分析对话内容，排除标签: {exclude_tags}")

    # 构建所有标签定义
    all_tags_str = "\n".join([
        f"- {tag}: {TAG_DEFINITIONS[tag]}"
        for tag in TAG_DEFINITIONS.keys()
    ])

    exclude_tags_str = ", ".join(exclude_tags) if exclude_tags else "无"

    prompt = f"""你是一个专业的货运对话标注专家。请深入分析以下司机与货主的对话内容，推荐合适的标签。

## 对话内容：
{conversation_text}

## 所有可用的标准化标签及其定义：
{all_tags_str}

## 已排除的标签（不需要再次推荐）：
{exclude_tags_str}

## 你的任务：
根据对话内容，从上述标签列表中选择合适的标签。优先选择明确提及的特征。

## 标签选择标准：
1. 对话中明确提到的特征（如车型、尺寸、费用等）
2. 双方达成一致的要求或约定
3. 司机或货主明确表示的限制或条件
4. 不要选择对话中未提及的标签

## 输出格式（严格按照JSON格式输出）：
{{
    "recommended_tags": ["标签1", "标签2", "标签3"],
    "reasons": {{
        "标签1": "对话中司机明确说xxx，符合该标签定义",
        "标签2": "货主要求xxx，司机同意，符合标签定义"
    }}
}}

请只输出JSON，不要输出其他内容。"""

    result = await call_glm_api(prompt, max_tokens=2000)

    if not result.get("success"):
        print(f"❌ [第二层AI] AI调用失败: {result.get('error')}")
        return {"recommended_tags": [], "reasons": {}}

    try:
        import json
        content = result["content"]

        # 提取JSON部分
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        recommendation = json.loads(content)
        recommended = recommendation.get("recommended_tags", [])
        reasons = recommendation.get("reasons", {})

        print(f"✅ [第二层AI] 分析完成，推荐了 {len(recommended)} 个标签: {recommended}")

        return {
            "recommended_tags": recommended,
            "reasons": reasons
        }
    except Exception as e:
        print(f"❌ [第二层AI] JSON解析失败: {str(e)}")
        return {"recommended_tags": [], "reasons": {}, "parse_error": str(e)}


@router.post("/ai/analyze")
async def ai_analyze_tags(request: RecommendationRequest):
    """
    三层AI深度分析推荐标签：

    第一层：AI分析初始AI标签是否合适，给出详细理由
    第二层：AI深入分析当前对话内容，推荐合适的标签
    第三层：参考历史相似对话作为补充
    """
    try:
        # 获取对话文本和初始标签
        text = request.text
        conversation_id = request.conversation_id
        driver_tags = []

        if conversation_id and not text:
            db = SessionLocal()
            try:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()

                if not conversation:
                    raise HTTPException(status_code=404, detail="对话不存在")

                text = conversation.raw_text

                # 提取初始AI标签
                if conversation.driver_tag:
                    try:
                        import json
                        parsed = json.loads(conversation.driver_tag)
                        driver_tags = parsed if isinstance(parsed, list) else [parsed]
                        driver_tags = [t for t in driver_tags if t]
                    except:
                        if conversation.driver_tag:
                            driver_tags = [conversation.driver_tag]
            finally:
                db.close()

        if not text:
            raise HTTPException(status_code=400, detail="必须提供conversation_id或text")

        # ========== 第一层：AI分析初始AI标签是否合适 ==========
        initial_analysis = await analyze_initial_tags_with_ai(text, driver_tags)

        # ========== 第二层：AI深入分析对话内容，推荐标签 ==========
        # 排除第一层确认合适的标签，让AI推荐新标签
        exclude_from_layer2 = initial_analysis.get("appropriate_tags", [])
        conversation_analysis = await recommend_tags_from_conversation_with_ai(text, exclude_tags=exclude_from_layer2)

        # ========== 第三层：参考历史相似对话 ==========
        rag_recommender = get_rag_recommender()
        rag_result = rag_recommender.recommend_tags(
            conversation_text=text,
            top_k=10,
            min_similarity=0.3
        )

        rag_tags_with_reason = {}
        similar_conversations_enhanced = []

        if rag_result.get("success") and rag_result.get("similar_conversations"):
            # 排除前两层已推荐的标签
            existing_tags = set(initial_analysis.get("appropriate_tags", [])) | \
                           set(conversation_analysis.get("recommended_tags", []))

            for conv in rag_result["similar_conversations"]:
                conv_id = conv.get("conversation_id")
                similarity = conv.get("similarity", 0)

                db = SessionLocal()
                try:
                    conv_detail = db.query(Conversation).filter(
                        Conversation.id == conv_id
                    ).first()

                    if conv_detail and conv_detail.batch_id:
                        from app.models.import_batch import ImportBatch
                        batch = db.query(ImportBatch).filter(
                            ImportBatch.id == conv_detail.batch_id
                        ).first()

                        if conv.get("tags"):
                            for tag in conv["tags"]:
                                # 只推荐尚未推荐的标签
                                if tag not in existing_tags and tag in TAG_DEFINITIONS:
                                    if tag not in rag_tags_with_reason:
                                        rag_tags_with_reason[tag] = []

                                    reason = f"相似度{round(similarity*100)}%"
                                    if batch:
                                        reason += f" - 来自批次: {batch.file_name}"
                                    reason += f" (对话#{conv_id})"

                                    rag_tags_with_reason[tag].append({
                                        "reason": reason,
                                        "similarity": similarity,
                                        "conversation_id": conv_id,
                                        "file_name": batch.file_name if batch else "未知",
                                        "conversation_snippet": conv.get("text", "")[:100] + "..."
                                    })
                                    existing_tags.add(tag)  # 避免重复添加
                finally:
                    db.close()

        # ========== 合并三层推荐结果 ==========
        all_recommendations = {}
        tag_details = {}

        # 第一层：验证合适的初始AI标签（最高优先级）
        for tag in initial_analysis.get("appropriate_tags", []):
            reason = initial_analysis.get("reasons", {}).get(tag, "初始AI推荐，AI验证合适")
            all_recommendations[tag] = {
                "score": 10,
                "source": "initial_ai_verified",
                "reason": f"✓ {reason}"
            }
            tag_details[tag] = all_recommendations[tag]

        # 第二层：从对话内容AI推荐的标签
        for tag in conversation_analysis.get("recommended_tags", []):
            reason = conversation_analysis.get("reasons", {}).get(tag, "AI从对话内容分析推荐")
            all_recommendations[tag] = {
                "score": 8,
                "source": "conversation_ai",
                "reason": reason
            }
            tag_details[tag] = all_recommendations[tag]

        # 第三层：历史相似对话推荐
        for tag, reasons_list in rag_tags_with_reason.items():
            if reasons_list and isinstance(reasons_list, list):
                all_recommendations[tag] = {
                    "score": 5,
                    "source": "historical_similar",
                    "reason": reasons_list[0]["reason"]
                }
                tag_details[tag] = all_recommendations[tag]

        # 按权重排序
        sorted_recommendations = sorted(
            all_recommendations.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        final_tags = [tag for tag, details in sorted_recommendations]

        # ========== 智能自动选择逻辑 ==========
        auto_select_tags = []
        appropriate_initial_tags = initial_analysis.get("appropriate_tags", [])

        if appropriate_initial_tags:
            # 如果有验证合适的初始AI标签，自动选中这些
            auto_select_tags = appropriate_initial_tags
            print(f"✅ [自动选择] 使用验证合适的初始标签: {auto_select_tags}")
        else:
            # 如果初始AI标签都不合适，使用第二层AI推荐的标签
            recommended_conversation_tags = conversation_analysis.get("recommended_tags", [])
            if recommended_conversation_tags:
                auto_select_tags = recommended_conversation_tags
                print(f"✅ [自动选择] 初始标签不合适，使用第二层AI推荐: {auto_select_tags}")
            else:
                print(f"⚠️ [自动选择] 没有可自动选择的标签")

        # 构建相似对话详细信息
        similar_convs_details = []
        for tag, reasons_list in rag_tags_with_reason.items():
            if reasons_list and isinstance(reasons_list, list):
                similar_convs_details.extend(reasons_list[:1])

        print(f"📊 [最终结果] 总共推荐 {len(final_tags)} 个标签，自动选择 {len(auto_select_tags)} 个")

        # 构建响应
        return {
            "success": True,
            "recommendations": final_tags,
            "tag_details": tag_details,
            "auto_select_tags": auto_select_tags,  # 新增：自动选择的标签
            "confidence": min(0.98, 0.7 + len(final_tags) * 0.03),
            "message": f"三层AI分析：验证初始标签({len(initial_analysis.get('appropriate_tags', []))}个合适) + 对话内容分析({len(conversation_analysis.get('recommended_tags', []))}个) + 历史相似({len(rag_tags_with_reason)}个)",
            "similar_conversations": similar_convs_details[:5],
            "initial_ai_tags": driver_tags,
            "initial_ai_analysis": {
                "appropriate": initial_analysis.get("appropriate_tags", []),
                "inappropriate": initial_analysis.get("inappropriate_tags", []),
                "reasons": initial_analysis.get("reasons", {})
            },
            "conversation_analysis": {
                "recommended": conversation_analysis.get("recommended_tags", []),
                "reasons": conversation_analysis.get("reasons", {})
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"智能分析失败: {str(e)}\n{traceback.format_exc()}",
            "recommendations": [],
            "confidence": 0.0
        }
