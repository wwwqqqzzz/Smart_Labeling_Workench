"""
RAG推荐服务 - 基于相似对话推荐标签
"""
from typing import List, Dict, Any, Optional
from app.services.rag.vector_store import get_vector_store
from app.services.rag.embedding_service import get_embedding_service
import json


class RAGRecommender:
    """RAG推荐服务"""
    
    def __init__(self):
        """初始化RAG推荐服务"""
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()
    
    def recommend_tags(
        self,
        conversation_text: str,
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> Dict[str, Any]:
        """
        基于相似对话推荐标签
        
        Args:
            conversation_text: 当前对话文本
            top_k: 返回最相似的K个对话
            min_similarity: 最小相似度阈值（0-1，基于余弦距离转换）
            
        Returns:
            推荐结果，包含推荐标签、相似对话、置信度
        """
        # 搜索相似对话
        similar_conversations = self.vector_store.search_similar(
            query_text=conversation_text,
            top_k=top_k
        )
        
        # 过滤低相似度结果（Chroma使用余弦距离，越小越相似）
        # 余弦距离范围 [0, 2]，0表示完全相同，2表示完全相反
        # 转换为相似度：相似度 = 1 - 距离/2
        filtered_results = []
        for conv in similar_conversations:
            similarity = 1 - conv['distance'] / 2
            if similarity >= min_similarity:
                conv['similarity'] = similarity
                filtered_results.append(conv)
        
        # 如果没有找到相似的对话
        if not filtered_results:
            return {
                "success": True,
                "recommendations": [],
                "similar_conversations": [],
                "confidence": 0.0,
                "message": "未找到相似的已审核对话"
            }
        
        # 提取标签并统计频率
        tag_frequency = {}
        for conv in filtered_results:
            tags_str = conv['metadata'].get('tags', '')
            if tags_str:
                tags = tags_str.split(',')
                for tag in tags:
                    if tag:
                        tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
        
        # 按频率排序标签
        recommended_tags = sorted(
            tag_frequency.items(),
            key=lambda x: (x[1], x[0]),
            reverse=True
        )
        
        # 计算置信度（基于最高相似度和结果数量）
        max_similarity = max(conv['similarity'] for conv in filtered_results)
        confidence = min(0.95, max_similarity * (1 + len(filtered_results) * 0.1))
        
        # 格式化相似对话（去掉嵌入向量）
        similar_convs = []
        for conv in filtered_results[:3]:  # 最多返回3个相似对话
            similar_convs.append({
                "conversation_id": conv['metadata'].get('conversation_id'),
                "text": conv['text'][:200] + "..." if len(conv['text']) > 200 else conv['text'],
                "tags": conv['metadata'].get('tags', '').split(','),
                "similarity": round(conv['similarity'], 3)
            })
        
        return {
            "success": True,
            "recommendations": [tag for tag, count in recommended_tags],
            "tag_scores": {tag: count for tag, count in recommended_tags},
            "similar_conversations": similar_convs,
            "confidence": round(confidence, 3),
            "message": f"基于 {len(filtered_results)} 条相似对话推荐"
        }
    
    def build_vector_index(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建向量索引
        
        Args:
            conversations: 对话列表，每个包含 id, text, manual_tag
            
        Returns:
            构建结果
        """
        try:
            # 清空现有索引
            self.vector_store.clear_collection()
            
            # 过滤有标签的对话
            tagged_conversations = []
            for conv in conversations:
                if conv.get('manual_tag'):
                    try:
                        tags = json.loads(conv['manual_tag'])
                        if tags:  # 只添加有标签的对话
                            tagged_conversations.append({
                                'id': conv['id'],
                                'text': conv['raw_text'],
                                'tags': tags if isinstance(tags, list) else []
                            })
                    except:
                        continue
            
            if not tagged_conversations:
                return {
                    "success": False,
                    "message": "没有找到已标注的对话"
                }
            
            # 批量添加到向量数据库
            self.vector_store.add_conversations_batch(tagged_conversations)
            
            return {
                "success": True,
                "message": f"成功构建向量索引，共 {len(tagged_conversations)} 条对话",
                "count": len(tagged_conversations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"构建索引失败: {str(e)}"
            }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """获取向量索引统计信息"""
        count = self.vector_store.get_collection_count()
        
        return {
            "total_documents": count,
            "embedding_dimension": self.embedding_service.get_dimension(),
            "collection_name": self.vector_store.collection.name
        }


# 全局单例
_rag_recommender = None

def get_rag_recommender() -> RAGRecommender:
    """获取RAG推荐服务单例"""
    global _rag_recommender
    if _rag_recommender is None:
        _rag_recommender = RAGRecommender()
    return _rag_recommender
