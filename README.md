# RAG for Pittsburgh and CMU

Retrieval-augmented question answering over a self-collected knowledge base about Pittsburgh and Carnegie Mellon University (11-711 Advanced NLP, HW2). The original assignment handout is in `HANDOUT.md`.

## Pipeline

```
seeds.py ─► run.py ─► crawl.py ─┬─► fetch.py    (download, cache, retry)
                                └─► extract.py  (HTML/PDF -> text + links)
                                        │
cmoa.py (CMOA open collection data) ────┤
                                        ▼
                               data/raw/*.jsonl
                                        │
                     chunk.py ─► retrieve.py (BM25 + FAISS, fusion, rerank) ─► reader.py (Qwen2.5-7B)
                                        │
                              metrics.py (EM, F1, recall, ROUGE-L)
```

| Path | Role |
|---|---|
| `src/data_collection/fetch.py` | HTTP with `requests-cache` (SQLite), per-request delay, retries with backoff, `Retry-After` handling, failure log |
| `src/data_collection/extract.py` | HTML and PDF to text; tables rendered as `a \| b \| c` rows; page title + meta description kept as the document title |
| `src/data_collection/crawl.py` | Breadth-first, domain-restricted crawl with per-site depth, page cap, allow/deny regexes |
| `src/data_collection/seeds.py` | Sites to crawl |
| `src/data_collection/cmoa.py` | Carnegie Museum of Art collection CSV (CC0) to one document per artwork |
| `src/data_collection/coverage.py` | Share of dev answers present anywhere in the corpus |
| `src/rag/chunk.py` | Line-aware chunks with overlap, title prepended, duplicates removed |
| `src/rag/retrieve.py` | BM25 (`bm25s`), dense (`BAAI/bge-small-en-v1.5` + FAISS), reciprocal rank fusion, weighted score fusion, cross-encoder rerank (`BAAI/bge-reranker-base`) |
| `src/rag/reader.py` | `Qwen2.5-7B-Instruct` (4-bit, MLX); short answers, or one sentence for descriptive questions when adaptive |
| `src/rag/run.py` | `build`, `answer`, `retrieval-eval` commands |
| `src/rag/remote.py`, `cloud/cloud_reader.ipynb` | Export prompts, run a larger reader on Colab, import its answers |
| `scripts/experiments.sh` | All dev-set runs |
| `scripts/progress.py` | Live progress bars for running jobs |

## Setup

```
conda create -p ./.venv python=3.11
./.venv/bin/pip install -r requirements.txt
```

Apple Silicon is required for the MLX reader.

## Build the knowledge base

```
./.venv/bin/python -m src.data_collection.run
mkdir -p data/external/cmoa
curl -L -o data/external/cmoa/cmoa.csv https://raw.githubusercontent.com/roll/collection/master/cmoa.csv
./.venv/bin/python -m src.data_collection.cmoa
./.venv/bin/python -m src.data_collection.coverage
```

## Index, evaluate, predict

```
./.venv/bin/python -m src.rag.run build --words 100 --overlap 20 --index data/index/c100v2
./.venv/bin/python -m src.rag.run build --words 200 --overlap 40 --index data/index/c200
./.venv/bin/python -m src.rag.run retrieval-eval --index data/index/c100v2
bash scripts/experiments.sh
./.venv/bin/python -m src.rag.run answer --questions test_set_day_3.json --index data/index/c100v2 \
    --mode rrf --k 5 --fallback --style adaptive --out system_outputs_day3/system_output_1.json
```

## Corpus

30,184 documents: 28,269 Carnegie Museum of Art artworks, 60 Wikipedia articles, and about 1,850 pages from city, tax, events, museum, culture, food-festival, pro-sports and college-athletics sites. Answer coverage on the dev set: 106/121 short-answer questions (87.6%).

## Dev results

`public_evaluation_data.json`, n = 157.

| Configuration | EM | F1 | Recall | ROUGE-L |
|---|---|---|---|---|
| Closed-book | 4.5 | 11.3 | 10.5 | 11.2 |
| 200w, BM25 | 42.7 | 52.2 | 52.5 | 52.1 |
| 200w, dense | 38.9 | 48.0 | 47.9 | 48.0 |
| 200w, RRF | 41.4 | 50.4 | 49.7 | 50.3 |
| 200w, weighted (alpha 0.5) | 43.3 | 53.3 | 53.1 | 53.2 |
| 200w, weighted + fallback | 43.3 | 53.9 | 53.7 | 53.8 |
| 200w, rerank + fallback | 43.9 | 53.9 | 54.2 | 53.8 |
| 100w, RRF + fallback | 45.2 | 56.8 | 56.1 | 56.7 |
| 100w, rerank + fallback | 45.9 | 55.2 | 55.7 | 55.1 |
| 100w, rerank k=8 + fallback | 45.9 | 55.7 | 55.9 | 55.6 |
| 100w, RRF + fallback, adaptive style | 44.6 | 59.2 | 59.9 | 58.9 |
| 100w, RRF + fallback, sentence style | 0.6 | 26.1 | 64.7 | 25.1 |
| final corpus, 100w, RRF + fallback, adaptive | 45.2 | 60.6 | 60.7 | 60.0 |
| same, Qwen2.5-14B reader with 7B backup | 47.8 | 61.5 | 63.3 | 60.6 |

The final corpus adds 1,172 Wikipedia articles (category and list pages), Arcade Comedy Theater, Pittsburgh Savoyards, college coaches pages and social-media handles (index `data/index/c100v2`).

## Test outputs

| File | Configuration |
|---|---|
| `system_outputs_day3/system_output_1.json` | final corpus, RRF + fallback, adaptive |
| `system_outputs_day3/system_output_2.json` | final corpus, RRF + fallback, short |
| `system_outputs_day3/system_output_3.json` | final corpus, weighted + rerank + fallback, adaptive |
| `system_outputs/system_output_{1,2}.json` | day-2 test set, earlier 200-word systems |

Fallback: when the reader answers "unknown" or similar, retry with twice as many chunks, then closed-book.

Answer style: `short` returns a bare answer; `sentence` always returns one sentence; `adaptive` returns a sentence only for descriptive questions (definitions, significance, "what is X") and a bare answer for lookups (artworks, dates, times, names, counts).

## Leaderboard

| Submission | Configuration | Total | F1 | Recall | ROUGE | LLM judge |
|---|---|---|---|---|---|---|
| devamjas_1 | 100w, RRF + fallback, adaptive | 41.71 | 40.54 | 38.14 | 34.01 | 3.167 |
| devamjas_2 | final corpus, 100w, RRF + fallback, adaptive | 46.16 | 44.22 | 42.26 | 36.98 | 3.447 |
| devamjas_3 | final corpus, 100w, RRF + fallback, sentence | 56.27 | 49.42 | 69.14 | 43.84 | 3.507 |
| devamjas_4 | same, Qwen2.5-14B reader with 7B backup | 54.99 | 46.33 | 70.16 | 40.81 | 3.507 |

## Larger reader on a cloud GPU

`src/rag/remote.py export` writes the retrieved prompts to `cloud/prompts.jsonl`; `cloud/cloud_reader.ipynb` answers them with Qwen2.5-14B-Instruct (4-bit) on a Colab T4, saving progress to Google Drive; `src/rag/remote.py import` scores the answers, using the 7B outputs for any question the 14B model left unanswered or refused.
