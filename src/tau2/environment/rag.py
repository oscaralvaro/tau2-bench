"""Minimal ChromaDB-based RAG for policy retrieval in tau2 simulations.

Students use this via RAGToolKit; they do not need to modify this file.
The only choice they make is `strategy` in ChromaPolicyIndex.
"""

from __future__ import annotations

import math
import os
import re
import uuid
from typing import Literal

import chromadb

ChunkingStrategy = Literal["headers", "fixed_200", "fixed_400", "sentence_window"]

THINK_INSTRUCTION = """
## How to use think
Before calling any operation that modifies data or before rejecting a request,
use think() to articulate:
  1. What the customer is asking for exactly
  2. What the policy says about this situation (based on what retrieve_policy returned)
  3. Whether you have all required information to proceed
  4. Which tool to call and with what arguments
"""


def chunk_by_headers(text: str) -> list[str]:
    """Split markdown on ## or # headings; each section becomes one chunk."""
    sections = re.split(r"(?m)^(?=#{1,2} )", text)
    return [section.strip() for section in sections if section.strip()]


def chunk_by_fixed(text: str, words_per_chunk: int = 200) -> list[str]:
    """Split text into chunks of roughly `words_per_chunk` words."""
    words = text.split()
    chunks = []
    for index in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[index : index + words_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks


def chunk_by_sentence_window(text: str, window: int = 3) -> list[str]:
    """Sliding window of `window` sentences, step = window // 2."""
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    step = max(1, window // 2)
    chunks = []
    for index in range(0, len(sentences), step):
        chunk = " ".join(sentences[index : index + window])
        if chunk:
            chunks.append(chunk)
    return chunks


def get_chunks(text: str, strategy: ChunkingStrategy) -> list[str]:
    """Dispatch to the right chunking function."""
    if strategy == "headers":
        return chunk_by_headers(text)
    if strategy == "fixed_200":
        return chunk_by_fixed(text, 200)
    if strategy == "fixed_400":
        return chunk_by_fixed(text, 400)
    if strategy == "sentence_window":
        return chunk_by_sentence_window(text)
    raise ValueError(
        f"Unknown strategy: {strategy!r}. "
        f"Valid options: headers, fixed_200, fixed_400, sentence_window"
    )


DEFAULT_EMBED_MODEL = "gemini-embedding-001"
DEFAULT_EMBED_DIM = 768  # Matryoshka truncation; full model outputs 3072


def _hash_embed_text(text: str, dim: int = 64) -> list[float]:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return [0.0] * dim
    vector = [0.0] * dim
    for word in words:
        vector[hash(word) % dim] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _fallback_embed(texts: list[str]) -> list[list[float]]:
    return [_hash_embed_text(text) for text in texts]


def _make_gemini_embed_fn(
    model: str = DEFAULT_EMBED_MODEL,
    output_dimensionality: int = DEFAULT_EMBED_DIM,
):
    """Return a Gemini embedder, or a deterministic local fallback for tests."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return _fallback_embed

    try:
        from google import genai
        from google.genai import types
    except ImportError:  # pragma: no cover - optional dependency at runtime
        return _fallback_embed

    client = genai.Client(api_key=api_key)

    def embed_fn(texts: list[str]) -> list[list[float]]:
        response = client.models.embed_content(
            model=model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=output_dimensionality,
            ),
        )
        return [list(map(float, embedding.values)) for embedding in response.embeddings]

    return embed_fn


class ChromaPolicyIndex:
    """Indexes policy chunks in an in-memory ChromaDB collection."""

    def __init__(
        self,
        policy_text: str,
        strategy: ChunkingStrategy = "headers",
        _embed_fn=None,
    ):
        self.strategy = strategy
        self._embed_fn = _embed_fn or _make_gemini_embed_fn()

        self.chunks = get_chunks(policy_text, strategy)
        if not self.chunks:
            raise ValueError("Policy text produced zero chunks. Check the policy file.")

        self._client = chromadb.Client()
        collection_name = f"policy_{uuid.uuid4().hex[:8]}"
        self._collection = self._client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        embeddings = self._embed_fn(self.chunks)
        self._collection.add(
            ids=[f"chunk_{index}" for index in range(len(self.chunks))],
            embeddings=embeddings,
            documents=self.chunks,
        )

    def search(self, query: str, k: int = 3) -> str:
        """Return the top-k most relevant policy chunks as a single string."""
        k = min(k, len(self.chunks))
        query_embeddings = self._embed_fn([query])
        result = self._collection.query(query_embeddings=query_embeddings, n_results=k)
        return "\n\n---\n\n".join(result["documents"][0])
