"""
向量数据库服务 - 使用Chroma
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from app.services.rag.embedding_service import get_embedding_service


class VectorStore:
    """向量数据库服务"""
    
    def __init__(self, collection_name: str = "conversations"):
        """
        初始化向量数据库
        
        Args:
            collection_name: 集合名称
        """
        # 创建持久化存储目录
        persist_dir = "/app/data/chroma"
        os.makedirs(persist_dir, exist_ok=True)
        
        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 获取嵌入服务
        self.embedding_service = get_embedding_service()
    
    def add_conversation(
        self,
        conversation_id: int,
        text: str,
        tags: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加对话到向量数据库
        
        Args:
            conversation_id: 对话ID
            text: 对话文本
            tags: 标签列表
            metadata: 额外的元数据
            
        Returns:
            文档ID
        """
        # 生成嵌入
        embedding = self.embedding_service.embed_text(text)
        
        # 准备元数据
        doc_metadata = {
            "conversation_id": conversation_id,
            "tags": ",".join(tags),
            **(metadata or {})
        }
        
        # 添加到集合
        doc_id = f"conv_{conversation_id}"
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[doc_metadata]
        )
        
        return doc_id
    
    def add_conversations_batch(
        self,
        conversations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量添加对话到向量数据库
        
        Args:
            conversations: 对话列表，每个包含 id, text, tags
            
        Returns:
            文档ID列表
        """
        if not conversations:
            return []
        
        # 批量生成嵌入
        texts = [conv["text"] for conv in conversations]
        embeddings = self.embedding_service.embed_texts(texts)
        
        # 准备数据
        ids = [f"conv_{conv['id']}" for conv in conversations]
        documents = texts
        metadatas = [
            {
                "conversation_id": conv["id"],
                "tags": ",".join(conv.get("tags", [])),
                **conv.get("metadata", {})
            }
            for conv in conversations
        ]
        
        # 批量添加
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def search_similar(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似对话
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            相似对话列表，包含 id, text, distance, metadata
        """
        # 生成查询嵌入
        query_embedding = self.embedding_service.embed_text(query_text)
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )
        
        # 格式化结果
        similarities = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                similarities.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'metadata': results['metadatas'][0][i]
                })
        
        return similarities
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功
        """
        try:
            doc_id = f"conv_{conversation_id}"
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """
        清空集合
        
        Returns:
            是否成功
        """
        try:
            # 删除并重新创建集合
            collection_name = self.collection.name
            self.client.delete_collection(collection_name)
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"清空失败: {e}")
            return False
    
    def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        return self.collection.count()


# 全局单例
_vector_store = None

def get_vector_store(collection_name: str = "conversations") -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(collection_name)
    return _vector_store
