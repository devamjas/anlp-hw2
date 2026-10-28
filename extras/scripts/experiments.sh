#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

PY=../.venv/bin/python
RESULTS=outputs/dev_results.jsonl
mkdir -p outputs

run() {
  name=$1; shift
  echo "== $name"
  caffeinate -i $PY -m src.rag.run answer --questions public_evaluation_data.json \
      --out "outputs/dev_$name.json" "$@" 2>/dev/null | grep '^{' | tee -a "$RESULTS"
}

run c200_closed            --index data/index/c200 --mode closed
run c200_sparse            --index data/index/c200 --mode sparse   --k 5
run c200_dense             --index data/index/c200 --mode dense    --k 5
run c200_rrf               --index data/index/c200 --mode rrf      --k 5
run c200_weighted          --index data/index/c200 --mode weighted --k 5
run c200_weighted_fallback --index data/index/c200 --mode weighted --k 5 --fallback
run c200_rerank_fallback   --index data/index/c200 --mode rerank   --k 5 --fallback
run c100_rrf_7b            --index data/index/c100 --mode rrf      --k 5 --fallback
run c100_rerank_7b         --index data/index/c100 --mode rerank   --k 5 --fallback
run c100_rerank_k8_7b      --index data/index/c100 --mode rerank   --k 8 --fallback
run c100_rrf_adaptive      --index data/index/c100 --mode rrf      --k 5 --fallback --style adaptive
run c100_rrf_sentence      --index data/index/c100 --mode rrf      --k 5 --fallback --style sentence
