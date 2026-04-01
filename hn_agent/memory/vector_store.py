"""
向量存储：可插拔的向量数据库接口与 ChromaDB 实现。

VectorStoreProvider 定义了向量存储的 Protocol 接口，
ChromaVectorStore 基于 ChromaDB 提供具体实现。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from hn_agent.exceptions import VectorStoreError
from hn_agent.memory.prompt import MemoryChunk

logger = logging.getLogger(__name__)


@runtime_checkable
class VectorStoreProvider(Protocol):
    """向量存储 Provider 协议接口。

    支持在不同向量数据库实现之间切换。
    """

    async def add_memories(self, memories: list[MemoryChunk]) -> None:
        """将记忆片段添加到向量存储。"""
        ...

    async def search(self, query: str, top_k: int = 5) -> list[MemoryChunk]:
        """基于语义相似度搜索记忆片段。"""
        ...


class ChromaVectorStore:
    """基于 ChromaDB 的向量存储实现。

    Parameters
    ----------
    collection_name : str
        ChromaDB 集合名称。
    embedding_client : object
        嵌入模型客户端，需提供 ``embed_texts`` 和 ``embed_query`` 方法。
    persist_directory : str | None
        ChromaDB 持久化目录。为 None 时使用内存存储。
    """

    def __init__(
        self,
        collection_name: str = "hn_agent_memories",
        embedding_client: object | None = None,
        persist_directory: str | None = None,
    ) -> None:
        self._collection_name = collection_name
        self._embedding_client = embedding_client
        self._persist_directory = persist_directory
        self._collection = None
        self._client = None

    def _ensure_collection(self) -> None:
        """延迟初始化 ChromaDB 客户端和集合。"""
        if self._collection is not None:
            return

        try:
            import chromadb
        except ImportError:
            raise ImportError(
                "chromadb 未安装。请运行: pip install chromadb"
            )

        try:
            if self._persist_directory:
                self._client = chromadb.PersistentClient(
                    path=self._persist_directory
                )
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            raise VectorStoreError(
                f"ChromaDB 初始化失败: {exc}"
            ) from exc

    async def add_memories(self, memories: list[MemoryChunk]) -> None:
        """将记忆片段添加到 ChromaDB。

        Parameters
        ----------
        memories : list[MemoryChunk]
            待存储的记忆片段列表。
        """
        if not memories:
            return

        try:
            self._ensure_collection()
        except (ImportError, VectorStoreError):
            raise
        except Exception as exc:
            raise VectorStoreError(f"ChromaDB 连接失败: {exc}") from exc

        ids: list[str] = []
        documents: list[str] = []
        embeddings: list[list[float]] | None = None
        metadatas: list[dict] = []

        # 检查是否需要生成嵌入向量
        needs_embedding = any(not m.embedding for m in memories)

        if needs_embedding and self._embedding_client is not None:
            texts_to_embed = [m.content for m in memories]
            try:
                computed_embeddings = self._embedding_client.embed_texts(texts_to_embed)
            except Exception as exc:
                raise VectorStoreError(f"嵌入向量生成失败: {exc}") from exc
            embeddings = []
            for i, memory in enumerate(memories):
                if memory.embedding:
                    embeddings.append(memory.embedding)
                else:
                    embeddings.append(computed_embeddings[i])

        elif not needs_embedding:
            embeddings = [m.embedding for m in memories]

        for memory in memories:
            mem_id = memory.id or str(uuid.uuid4())
            ids.append(mem_id)
            documents.append(memory.content)

            meta = dict(memory.metadata)
            if memory.user_id:
                meta["user_id"] = memory.user_id
            if memory.thread_id:
                meta["thread_id"] = memory.thread_id
            if memory.created_at:
                meta["created_at"] = memory.created_at.isoformat()
            metadatas.append(meta if meta else None)

        try:
            kwargs: dict = {
                "ids": ids,
                "documents": documents,
            }
            # ChromaDB 不接受空 dict 作为 metadata，仅在有非空 metadata 时传入
            if any(m is not None for m in metadatas):
                kwargs["metadatas"] = metadatas
            if embeddings is not None:
                kwargs["embeddings"] = embeddings

            self._collection.upsert(**kwargs)  # type: ignore[union-attr]
        except Exception as exc:
            raise VectorStoreError(f"ChromaDB 写入失败: {exc}") from exc

    async def search(self, query: str, top_k: int = 5) -> list[MemoryChunk]:
        """基于语义相似度搜索记忆片段。

        Parameters
        ----------
        query : str
            查询文本。
        top_k : int
            返回的最大结果数量。

        Returns
        -------
        list[MemoryChunk]
            按相似度排序的记忆片段列表。
        """
        try:
            self._ensure_collection()
        except (ImportError, VectorStoreError):
            raise
        except Exception as exc:
            raise VectorStoreError(f"ChromaDB 连接失败: {exc}") from exc

        query_embedding: list[float] | None = None
        if self._embedding_client is not None:
            try:
                query_embedding = self._embedding_client.embed_query(query)
            except Exception as exc:
                raise VectorStoreError(f"查询嵌入生成失败: {exc}") from exc

        try:
            if query_embedding is not None:
                results = self._collection.query(  # type: ignore[union-attr]
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "embeddings"],
                )
            else:
                results = self._collection.query(  # type: ignore[union-attr]
                    query_texts=[query],
                    n_results=top_k,
                    include=["documents", "metadatas", "embeddings"],
                )
        except Exception as exc:
            raise VectorStoreError(f"ChromaDB 查询失败: {exc}") from exc

        chunks: list[MemoryChunk] = []
        if not results or not results.get("ids"):
            return chunks

        result_ids = results["ids"][0] if results["ids"] else []
        result_docs = results["documents"][0] if results.get("documents") else []
        result_metas = results["metadatas"][0] if results.get("metadatas") else []
        result_embeds = (
            results["embeddings"][0] if results.get("embeddings") else []
        )

        for i, doc_id in enumerate(result_ids):
            meta = result_metas[i] if i < len(result_metas) else {}
            if meta is None:
                meta = {}
            else:
                meta = dict(meta)  # 复制以避免修改原始数据
            content = result_docs[i] if i < len(result_docs) else ""
            embedding = result_embeds[i] if i < len(result_embeds) else []

            created_at = None
            if "created_at" in meta:
                try:
                    created_at = datetime.fromisoformat(meta.pop("created_at"))
                except (ValueError, TypeError):
                    pass

            user_id = meta.pop("user_id", "")
            thread_id = meta.pop("thread_id", "")

            chunks.append(
                MemoryChunk(
                    id=doc_id,
                    content=content,
                    user_id=user_id,
                    thread_id=thread_id,
                    embedding=list(embedding) if len(embedding) > 0 else [],
                    created_at=created_at,
                    metadata=meta,
                )
            )

        return chunks
