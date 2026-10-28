import json
from pathlib import Path

import bm25s
import faiss
import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "BAAI/bge-reranker-base"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def build_index(chunks, index_dir):
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [c["text"] for c in chunks]

    with open(index_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    bm25 = bm25s.BM25()
    bm25.index(bm25s.tokenize(texts, stopwords="en"))
    bm25.save(str(index_dir / "bm25"))

    encoder = SentenceTransformer(EMBED_MODEL)
    vectors = encoder.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    dense = faiss.IndexFlatIP(vectors.shape[1])
    dense.add(np.asarray(vectors, dtype="float32"))
    faiss.write_index(dense, str(index_dir / "dense.faiss"))


class Retriever:
    def __init__(self, index_dir):
        index_dir = Path(index_dir)
        self.chunks = [json.loads(line) for line in open(index_dir / "chunks.jsonl", encoding="utf-8")]
        self.bm25 = bm25s.BM25.load(str(index_dir / "bm25"))
        self.dense = faiss.read_index(str(index_dir / "dense.faiss"))
        self.encoder = SentenceTransformer(EMBED_MODEL)
        self.reranker = None

    def sparse_search(self, query, k):
        ids, scores = self.bm25.retrieve(bm25s.tokenize([query], stopwords="en", show_progress=False),
                                         k=k, show_progress=False)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0])]

    def dense_search(self, query, k):
        vector = self.encoder.encode([QUERY_PREFIX + query], normalize_embeddings=True)
        scores, ids = self.dense.search(np.asarray(vector, dtype="float32"), k)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0])]

    def search(self, query, mode="rrf", k=5, pool=50, alpha=0.5):
        if mode == "sparse":
            hits = self.sparse_search(query, k)
        elif mode == "dense":
            hits = self.dense_search(query, k)
        elif mode == "rrf":
            hits = reciprocal_rank_fusion([self.sparse_search(query, pool), self.dense_search(query, pool)])[:k]
        elif mode == "weighted":
            hits = weighted_fusion(self.sparse_search(query, pool), self.dense_search(query, pool), alpha)[:k]
        elif mode == "rerank":
            return self.rerank(query, weighted_fusion(self.sparse_search(query, pool), self.dense_search(query, pool), alpha)[:pool], k)
        else:
            raise ValueError(mode)
        return [self.chunks[i] for i, _ in hits]

    def rerank(self, query, candidates, k):
        if self.reranker is None:
            self.reranker = CrossEncoder(RERANK_MODEL, device="mps", max_length=512)
        passages = [self.chunks[i] for i, _ in candidates]
        scores = self.reranker.predict([(query, p["text"]) for p in passages], batch_size=16, show_progress_bar=False)
        order = np.argsort(-scores)[:k]
        return [passages[i] for i in order]


def reciprocal_rank_fusion(rankings, c=60):
    scores = {}
    for ranking in rankings:
        for rank, (chunk_id, _) in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (c + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def min_max(hits):
    if not hits:
        return {}
    values = [s for _, s in hits]
    low, high = min(values), max(values)
    return {i: (s - low) / (high - low) if high > low else 1.0 for i, s in hits}


def weighted_fusion(sparse_hits, dense_hits, alpha):
    sparse, dense = min_max(sparse_hits), min_max(dense_hits)
    scores = {i: alpha * dense.get(i, 0.0) + (1 - alpha) * sparse.get(i, 0.0) for i in set(sparse) | set(dense)}
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
