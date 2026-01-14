"""
文本嵌入服务 - 使用OpenAI或本地模型
"""
import os
from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingService:
    """文本嵌入服务"""
    
    def __init__(self):
        """初始化嵌入服务"""
        # 使用本地多语言模型（支持中文）
        # 使用 paraphrase-multilingual-MiniLM-L12-v2，这是一个轻量级的多语言模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.dimension = 384  # 该模型的嵌入维度
    
    def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        # 生成嵌入
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为嵌入向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.dimension


# 全局单例
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
