# 数据流程与 RAG 实现

## 📊 数据流程设计

### 1. 数据导入流程

```
┌─────────────────────────────────────────────────────────────┐
│ Excel 文件 (1.xlsx)                                         │
│  - Sheet1: 打标1月1期 (对话数据)                            │
│  - Sheet2: 标准化标签 (标签定义)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 读取 Excel                                          │
│  - pandas.read_excel()                                      │
│  - 解析对话数据（3500 条）                                  │
│  - 解析标签定义（56 个）                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 数据清洗                                            │
│  - 去除空格、换行符                                         │
│  - 验证 JSON 格式                                          │
│  - 处理异常数据                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 数据库持久化                                        │
│  - 存入 conversations 表                                    │
│  - 存入 tags 表                                             │
│  - 建立索引                                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 构建向量库                                          │
│  - 为每个标签定义生成嵌入向量                               │
│  - 存入 Chroma 向量库                                       │
│  - 建立索引                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2. 审核工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 用户打开界面                                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：加载待审核对话                                         │
│  GET /api/v1/conversations?status=pending&page=1           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：解析对话文本                                          │
│  - 按 $_$ 分割                                             │
│  - 识别司机/货主                                            │
│  - 高亮关键词                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：触发 RAG 推荐（异步）                                 │
│  POST /api/v1/rag/check                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 后端：RAG 引擎处理                                          │
│  1. 向量检索相关标签定义                                    │
│  2. LLM 判断 AI 标签是否正确                               │
│  3. 返回推荐结果                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：显示推荐结果                                          │
│  - 置信度显示                                              │
│  - Top 3 推荐标签                                          │
│  - 推理过程（可展开）                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 用户操作                                                    │
│  - 按空格：确认 AI 标签                                     │
│  - 按 1-3：选择推荐标签                                     │
│  - 点击标签：从速选池选择                                   │
│  - 按 Enter：跳过（存疑）                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：提交审核结果                                          │
│  PUT /api/v1/conversations/:id                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 后端：保存数据                                             │
│  - 更新 conversations 表                                   │
│  - 记录 audit_logs                                         │
│  - 更新缓存                                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 前端：自动加载下一条                                        │
│  预取下一条数据，提升体验                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 RAG 实现细节

### 向量库构建

#### 1. 标签定义向量化

```python
# services/vector_store_builder.py
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from typing import List

class VectorStoreBuilder:
    """向量库构建器"""

    def __init__(self, persist_directory: str = "./data/chroma"):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.persist_directory = persist_directory

    def build_from_tags(self, tags: List[Tag]) -> Chroma:
        """
        从标签列表构建向量库

        Args:
            tags: 标签列表

        Returns:
            Chroma 向量库
        """
        # 1. 构建文档
        documents = []
        for tag in tags:
            # 组合标签名和定义
            content = f"标签名：{tag.name}\n定义：{tag.definition or '暂无定义'}"

            doc = Document(
                page_content=content,
                metadata={
                    "tag_id": tag.id,
                    "tag_name": tag.name,
                    "category": tag.category,
                    "definition": tag.definition
                }
            )
            documents.append(doc)

        # 2. 创建向量库
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="tag_definitions"
        )

        # 3. 持久化
        vector_store.persist()

        return vector_store

    def load_existing(self) -> Chroma:
        """加载已存在的向量库"""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="tag_definitions"
        )
```

#### 2. 向量检索优化

```python
# rag/retriever.py
from typing import List, Optional
from rank_bm25 import BM25Okapi
import jieba

class HybridRetriever:
    """混合检索器（向量 + BM25）"""

    def __init__(
        self,
        vector_store: Chroma,
        tags: List[Tag],
        alpha: float = 0.7  # 向量权重
    ):
        self.vector_store = vector_store
        self.tags = tags
        self.alpha = alpha

        # 构建 BM25 索引
        self._build_bm25_index()

    def _build_bm25_index(self):
        """构建 BM25 索引"""
        corpus = []
        for tag in self.tags:
            # 分词
            tokens = list(jieba.cut(tag.definition or tag.name))
            corpus.append(tokens)

        self.bm25 = BM25Okapi(corpus)
        self.corpus = corpus

    async def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[TagWithScore]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回 Top K

        Returns:
            带分数的标签列表
        """
        # 1. 向量检索
        vector_results = self.vector_store.similarity_search_with_score(
            query, k=top_k * 2
        )
        vector_scores = self._normalize_vector_scores(vector_results)

        # 2. BM25 检索
        query_tokens = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(query_tokens)

        # 3. 混合排序
        final_scores = {}
        for tag_name, vec_score in vector_scores.items():
            bm25_score = bm25_scores.get(tag_name, 0)
            # 加权融合
            final_scores[tag_name] = (
                self.alpha * vec_score +
                (1 - self.alpha) * bm25_score
            )

        # 4. 排序并返回 Top K
        sorted_tags = sorted(
            final_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        return [
            TagWithScore(
                name=tag_name,
                score=score,
                definition=self._get_definition(tag_name)
            )
            for tag_name, score in sorted_tags
        ]
```

### LLM 判断实现

#### Prompt 工程设计

```python
# rag/prompts.py
from jinja2 import Template

CHECK_TAG_TEMPLATE = Template("""
你是一个货运对话标签审核专家。你需要判断 AI 自动打的标签是否正确。

## 对话内容
{{ conversation_text }}

## AI 自动打的标签
{{ ai_tag }}

## 参考标签定义
{% for tag in relevant_tags %}
### {{ tag.name }}
{{ tag.definition or '暂无定义' }}
{% endfor %}

## 判断标准
1. **严格匹配**：对话内容必须明确符合标签定义
2. **宁可漏打，不可打错**：不确定的情况下，判定为不正确
3. **多标签情况**：如果对话涉及多个标签，AI 只打了一个，也算不正确

## 输出格式（JSON）
```json
{
  "is_correct": true/false,
  "confidence": 0.0-1.0,
  "recommendations": [
    {
      "tag": "标签名称",
      "score": 0.0-1.0,
      "reason": "推荐理由"
    }
  ],
  "reasoning": "详细推理过程"
}
```

请根据以上信息进行判断，并输出 JSON 格式结果。
""")

class PromptManager:
    """Prompt 管理器"""

    @staticmethod
    def build_check_tag_prompt(
        conversation_text: str,
        ai_tag: str,
        relevant_tags: List[Tag]
    ) -> str:
        """构建标签检查 Prompt"""
        return CHECK_TAG_TEMPLATE.render(
            conversation_text=conversation_text,
            ai_tag=ai_tag,
            relevant_tags=relevant_tags
        )
```

#### GLM-4 调用

```python
# rag/llm_client.py
from zhipuai import ZhipuAI
from typing import List, Dict
import json

class GLMClient:
    """GLM-4 客户端"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)

    async def check_tag(
        self,
        conversation_text: str,
        ai_tag: str,
        relevant_tags: List[Tag]
    ) -> LLMJudgment:
        """
        使用 GLM-4 判断标签

        Args:
            conversation_text: 对话文本
            ai_tag: AI 标签
            relevant_tags: 相关标签定义

        Returns:
            LLM 判断结果
        """
        # 1. 构建 Prompt
        prompt = PromptManager.build_check_tag_prompt(
            conversation_text=conversation_text,
            ai_tag=ai_tag,
            relevant_tags=relevant_tags
        )

        # 2. 调用 GLM-4 Flash
        response = self.client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # 低温度，保证稳定性
            max_tokens=1000
        )

        # 3. 解析响应
        result_text = response.choices[0].message.content

        # 提取 JSON（可能包含 markdown 代码块）
        json_text = self._extract_json(result_text)

        try:
            result_data = json.loads(json_text)
        except json.JSONDecodeError:
            # 如果解析失败，返回保守结果
            return LLMJudgment(
                is_correct=False,
                confidence=0.0,
                recommendations=[],
                reasoning="LLM 响应解析失败"
            )

        # 4. 构建结果
        return LLMJudgment(
            is_correct=result_data.get("is_correct", False),
            confidence=result_data.get("confidence", 0.0),
            recommendations=[
                TagRecommendation(**rec)
                for rec in result_data.get("recommendations", [])
            ],
            reasoning=result_data.get("reasoning", "")
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """从文本中提取 JSON"""
        # 尝试直接解析
        try:
            json.loads(text)
            return text
        except:
            pass

        # 尝试提取 ```json ... ```
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()

        # 尝试提取 ``` ... ```
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()

        # 提取第一个 { ... }
        start = text.find("{")
        end = text.rfind("}") + 1
        return text[start:end]
```

### RAG 完整流程

```python
# rag/engine.py
from typing import Optional
import hashlib
import json

class RAGEngine:
    """RAG 推荐引擎"""

    def __init__(
        self,
        retriever: HybridRetriever,
        llm_client: GLMClient,
        cache_client: Optional[Redis] = None
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.cache = cache_client

    async def check_tag(
        self,
        conversation_text: str,
        ai_tag: str,
        use_cache: bool = True
    ) -> RAGResult:
        """
        检查 AI 标签是否正确

        Args:
            conversation_text: 对话文本
            ai_tag: AI 标签
            use_cache: 是否使用缓存

        Returns:
            RAG 判断结果
        """
        # 1. 生成缓存键
        cache_key = self._generate_cache_key(
            conversation_text,
            ai_tag
        )

        # 2. 检查缓存
        if use_cache and self.cache:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # 3. 向量检索
        relevant_tags = await self.retriever.retrieve(
            query=conversation_text,
            top_k=5
        )

        # 4. LLM 判断
        llm_judgment = await self.llm_client.check_tag(
            conversation_text=conversation_text,
            ai_tag=ai_tag,
            relevant_tags=relevant_tags
        )

        # 5. 构建结果
        result = RAGResult(
            conversation_text=conversation_text,
            ai_tag=ai_tag,
            is_correct=llm_judgment.is_correct,
            confidence=llm_judgment.confidence,
            recommendations=llm_judgment.recommendations,
            reasoning=llm_judgment.reasoning,
            relevant_tags=relevant_tags
        )

        # 6. 缓存结果
        if use_cache and self.cache:
            await self._save_to_cache(cache_key, result)

        return result

    def _generate_cache_key(
        self,
        conversation_text: str,
        ai_tag: str
    ) -> str:
        """生成缓存键"""
        content = f"{conversation_text}:{ai_tag}"
        hash_value = hashlib.md5(content.encode()).hexdigest()
        return f"rag:result:{hash_value}"

    async def _get_from_cache(
        self,
        cache_key: str
    ) -> Optional[RAGResult]:
        """从缓存获取结果"""
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return RAGResult.parse_raw(cached_data)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None

    async def _save_to_cache(
        self,
        cache_key: str,
        result: RAGResult
    ):
        """保存结果到缓存"""
        try:
            await self.cache.set(
                cache_key,
                result.json(),
                ex=3600  # 1 小时过期
            )
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
```

---

## 🎯 前端数据流

### React Query 数据管理

```typescript
// hooks/useConversation.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useConversation(id: number) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: async () => {
      const res = await fetch(`/api/v1/conversations/${id}`)
      return res.json()
    }
  })
}

export function useRAGCheck() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (params: {
      conversation_id: number
      conversation_text: string
      ai_tag: string
    }) => {
      const res = await fetch('/api/v1/rag/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      return res.json()
    },
    onSuccess: (data) => {
      // 更新缓存
      queryClient.setQueryData(
        ['rag', data.conversation_id],
        data
      )
    }
  })
}

export function useUpdateConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: {
      id: number
      manual_tag?: string[]
      status?: string
      auditor?: string
    }) => {
      const res = await fetch(`/api/v1/conversations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return res.json()
    },
    onSuccess: () => {
      // 使缓存失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    }
  })
}
```

### Zustand 状态管理

```typescript
// stores/auditStore.ts
import { create } from 'zustand'

interface AuditStore {
  // 当前审核的对话 ID
  currentConversationId: number | null

  // RAG 推荐结果
  ragResult: RAGResult | null

  // 操作
  setCurrentConversationId: (id: number | null) => void
  setRAGResult: (result: RAGResult | null) => void

  // 快捷键操作
  approveAI: () => void
  selectRecommendation: (index: number) => void
  skipConversation: () => void
}

export const useAuditStore = create<AuditStore>((set, get) => ({
  currentConversationId: null,
  ragResult: null,

  setCurrentConversationId: (id) => set({ currentConversationId: id }),

  setRAGResult: (result) => set({ ragResult: result }),

  approveAI: () => {
    const { currentConversationId } = get()
    if (!currentConversationId) return

    // 调用更新 API
    updateConversation({
      id: currentConversationId,
      manual_tag: [],  // 使用 AI 标签
      status: 'approved'
    })

    // 加载下一条
    const nextId = currentConversationId + 1
    set({ currentConversationId: nextId })
  },

  selectRecommendation: (index) => {
    const { ragResult, currentConversationId } = get()
    if (!ragResult || !currentConversationId) return

    const selectedTag = ragResult.recommendations[index]?.tag
    if (!selectedTag) return

    // 更新标签
    updateConversation({
      id: currentConversationId,
      manual_tag: [selectedTag],
      status: 'approved'
    })

    // 加载下一条
    const nextId = currentConversationId + 1
    set({ currentConversationId: nextId })
  },

  skipConversation: () => {
    const { currentConversationId } = get()
    if (!currentConversationId) return

    // 标记为跳过
    updateConversation({
      id: currentConversationId,
      status: 'skipped'
    })

    // 加载下一条
    const nextId = currentConversationId + 1
    set({ currentConversationId: nextId })
  }
}))
```

---

**最后更新**: 2025-01-13
**维护者**: Smart Labeling Workbench Team
