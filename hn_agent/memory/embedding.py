"""
嵌入模型客户端：封装 text-embedding-3-small 嵌入模型。

EmbeddingClient 基于 langchain_openai.OpenAIEmbeddings 提供文本向量化能力，
用于记忆系统的向量化存储与语义检索。
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Embeddings(Protocol):
    """嵌入模型协议，兼容 langchain_core.embeddings.Embeddings。"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class EmbeddingClient:
    """text-embedding-3-small 嵌入模型客户端。

    封装 langchain_openai.OpenAIEmbeddings，提供批量文本嵌入和单条查询嵌入。

    Parameters
    ----------
    model_name : str
        嵌入模型名称，默认 ``text-embedding-3-small``。
    embeddings : Embeddings | None
        外部注入的嵌入模型实例。为 None 时尝试创建 OpenAIEmbeddings。
    """

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        embeddings: Embeddings | None = None,
    ) -> None:
        self._model_name = model_name
        if embeddings is not None:
            self._embeddings = embeddings
        else:
            self._embeddings = self._create_default_embeddings(model_name)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @staticmethod
    def _create_default_embeddings(model_name: str) -> Embeddings:
        """创建默认的 OpenAIEmbeddings 实例。"""
        try:
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=model_name)  # type: ignore[return-value]
        except ImportError:
            raise ImportError(
                "langchain_openai 未安装。请运行: pip install langchain-openai"
            )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量将文本转换为向量。

        Parameters
        ----------
        texts : list[str]
            待嵌入的文本列表。

        Returns
        -------
        list[list[float]]
            每个文本对应的嵌入向量列表。
        """
        if not texts:
            return []
        return self._embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        """将单条查询文本转换为向量。

        Parameters
        ----------
        query : str
            查询文本。

        Returns
        -------
        list[float]
            查询文本的嵌入向量。
        """
        return self._embeddings.embed_query(query)
