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

# 标签定义
ALL_TAGS = [
    "车辆类型-厢式车", "车辆类型-高栏车", "车辆类型-平板车", "车辆类型-冷藏车",
    "车辆类型-罐车", "车辆类型-特种车", "车辆类型-自卸车",
    "货物类型-普货", "货物类型-生鲜", "货物类型-建材", "货物类型-设备",
    "货物类型-危化品", "货物类型-钢材", "货物类型-纺织品", "货物类型-汽车配件",
    "运输需求-整车", "运输需求-零担", "运输需求-冷链",
    "交易阶段-询价", "交易阶段-议价", "交易阶段-确认", "交易阶段-已成交",
    "其他-装卸服务", "其他-运费垫付", "其他-回程车", "其他-尾板"
]


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


@router.post("/ai/analyze")
async def ai_analyze_tags(request: RecommendationRequest):
    """
    使用GLM-4智能分析对话内容并推荐标签

    直接使用大语言模型理解对话语义，从预定义标签中选择最相关的标签
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

        # 获取API密钥（支持两种环境变量名）
        api_key = os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": "未配置GLM_API_KEY或ZHIPU_API_KEY",
                "recommendations": [],
                "confidence": 0.0
            }

        # 构建提示词
        tags_str = "、".join(ALL_TAGS)
        prompt = f"""你是一个物流对话标注专家。请分析以下司机和货主的对话内容，从预定义标签中选择最相关的3-5个标签。

预定义标签列表：
{tags_str}

对话内容：
{text}

要求：
1. 仔细分析对话中提到的车辆类型、货物类型、运输需求等信息
2. 只能从预定义标签中选择，不能创造新标签
3. 选择最相关、最重要的3-5个标签
4. 返回JSON格式，包含tags数组（标签列表）和reason（选择理由）

示例输出格式：
{{
  "tags": ["车辆类型-厢式车", "货物类型-生鲜", "运输需求-冷链"],
  "reason": "对话中明确提到需要冷链车运输生鲜水果"
}}

请直接返回JSON，不要其他内容。"""

        # 调用GLM API
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

        payload = {
            "model": "glm-4-flash",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"GLM API调用失败: {response.status_code}",
                    "recommendations": [],
                    "confidence": 0.0
                }

            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 解析JSON响应
            try:
                import json
                # 尝试提取JSON（可能包含markdown代码块）
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                ai_result = json.loads(content)
                recommended_tags = ai_result.get("tags", [])
                reason = ai_result.get("reason", "")

                # 过滤掉不在预定义列表中的标签
                valid_tags = [tag for tag in recommended_tags if tag in ALL_TAGS]

                return {
                    "success": True,
                    "recommendations": valid_tags[:5],  # 最多返回5个
                    "confidence": 0.85,  # GLM分析置信度较高
                    "message": reason or "基于GLM-4智能分析",
                    "similar_conversations": []  # AI分析模式不返回相似对话
                }

            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"解析AI响应失败: {str(e)}",
                    "recommendations": [],
                    "confidence": 0.0
                }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"AI分析失败: {str(e)}",
            "recommendations": [],
            "confidence": 0.0
        }
