import argparse
import json
import re
from pathlib import Path

from tqdm import tqdm

from .chunk import build_chunks, load_documents
from .metrics import score


def cmd_build(args):
    from .retrieve import build_index
    chunks = build_chunks(load_documents(), args.words, args.overlap)
    print(f"{len(chunks)} chunks")
    build_index(chunks, args.index)


REFUSALS = re.compile(r"\b(unknown|not (mentioned|provided|specified|available|listed|stated|found|given)|n/a|tbd|tba|"
                      r"no information|cannot be determined|does not (say|mention|contain|specify))\b", re.I)


def is_refusal(answer):
    text = answer.strip(" .").lower()
    return not text or text == "none" or bool(REFUSALS.search(text))


def cmd_answer(args):
    from .retrieve import Retriever
    from .reader import READER_MODEL, Reader

    questions = json.load(open(args.questions))
    if args.limit:
        questions = questions[:args.limit]
    retriever = Retriever(args.index) if args.mode != "closed" else None
    reader = Reader(args.reader or READER_MODEL, style=args.style)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    trace_path = args.out.replace(".json", ".trace.jsonl")
    progress_path = args.out.replace(".json", ".progress")
    predictions = {}
    with open(trace_path, "w") as trace:
        for done, q in enumerate(tqdm(questions), 1):
            passages = retriever.search(q["question"], args.mode, args.k) if retriever else None
            answer = reader.answer(q["question"], passages)
            if args.fallback and is_refusal(answer) and retriever:
                answer = reader.answer(q["question"], retriever.search(q["question"], args.mode, 2 * args.k))
            if args.fallback and is_refusal(answer):
                answer = reader.answer(q["question"])
            predictions[q["id"]] = answer
            row = {"id": q["id"], "question": q["question"], "prediction": predictions[q["id"]],
                   "answers": q.get("answers"), "urls": [p["url"] for p in passages or []]}
            trace.write(json.dumps(row, ensure_ascii=False) + "\n")
            trace.flush()
            Path(progress_path).write_text(f"{done}/{len(questions)}")

    if args.andrewid:
        predictions = {"andrewid": args.andrewid, **predictions}
    json.dump(predictions, open(args.out, "w"), indent=2, ensure_ascii=False)
    if "answers" in questions[0]:
        config = {k: v for k, v in vars(args).items() if k != "func"}
        print(json.dumps({"config": config, "n": len(questions), **score(predictions, questions)}))


def cmd_retrieval_eval(args):
    from .retrieve import Retriever
    from .metrics import normalize
    questions = json.load(open(args.questions))
    retriever = Retriever(args.index)
    for mode in ["sparse", "dense", "rrf", "weighted", "rerank"]:
        hits = 0
        for q in questions:
            text = " ".join(" ".join(normalize(p["text"])) for p in retriever.search(q["question"], mode, args.k))
            hits += any(" ".join(normalize(a)) in text for a in q["answers"] if len(a.split()) <= 6)
        print(f"{mode:9s} answer-in-top-{args.k}: {hits}/{len(questions)} = {100 * hits / len(questions):.1f}%")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--words", type=int, default=200)
    build.add_argument("--overlap", type=int, default=40)
    build.add_argument("--index", default="data/index/c200")
    build.set_defaults(func=cmd_build)

    answer = sub.add_parser("answer")
    answer.add_argument("--questions", default="public_evaluation_data.json")
    answer.add_argument("--index", default="data/index/c200")
    answer.add_argument("--mode", default="rrf", choices=["sparse", "dense", "rrf", "weighted", "rerank", "closed"])
    answer.add_argument("--k", type=int, default=5)
    answer.add_argument("--limit", type=int, default=0)
    answer.add_argument("--fallback", action="store_true")
    answer.add_argument("--reader", default=None)
    answer.add_argument("--style", default="short", choices=["short", "adaptive", "sentence"])
    answer.add_argument("--andrewid", default=None)
    answer.add_argument("--out", required=True)
    answer.set_defaults(func=cmd_answer)

    retrieval = sub.add_parser("retrieval-eval")
    retrieval.add_argument("--questions", default="public_evaluation_data.json")
    retrieval.add_argument("--index", default="data/index/c200")
    retrieval.add_argument("--k", type=int, default=5)
    retrieval.set_defaults(func=cmd_retrieval_eval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
