import argparse
import json
from pathlib import Path

from tqdm import tqdm

from .metrics import score
from .reader import build_messages

JOBS = [
    ("dev", "public_evaluation_data.json", ["adaptive"]),
    ("leaderboard", "leaderboard_queries.json", ["adaptive", "sentence"]),
    ("test", "test_set_day_3.json", ["adaptive", "short"]),
]


def cmd_export(args):
    from .retrieve import Retriever
    retriever = Retriever(args.index)
    with open(args.prompts, "w", encoding="utf-8") as out:
        for name, path, styles in JOBS:
            for q in tqdm(json.load(open(path)), desc=name):
                top_k = retriever.search(q["question"], args.mode, args.k)
                top_2k = retriever.search(q["question"], args.mode, 2 * args.k)
                for style in styles:
                    attempts = [build_messages(q["question"], passages, style)[0] for passages in (top_k, top_2k, None)]
                    max_tokens = build_messages(q["question"], None, style)[1]
                    row = {"key": f"{name}|{style}|{q['id']}", "attempts": attempts, "max_tokens": max_tokens}
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {args.prompts}")


def cmd_import(args):
    answers = json.load(open(args.answers))
    tag = args.tag
    for name, path, styles in JOBS:
        questions = json.load(open(path))
        for style in styles:
            preds = {q["id"]: answers[f"{name}|{style}|{q['id']}"] for q in questions}
            if name == "dev":
                out = f"outputs/dev_{tag}_{style}.json"
                result = {"config": {"out": out, "reader": tag, "style": style}, "n": len(questions), **score(preds, questions)}
                with open("outputs/dev_results.jsonl", "a") as f:
                    f.write(json.dumps(result) + "\n")
                print(json.dumps(result))
            elif name == "leaderboard":
                out = f"leaderboard/leaderboard_devamjas_{tag}_{style}.json"
                preds = {"andrewid": "devamjas", **preds}
            else:
                out = f"system_outputs_{tag}/test_day3_{style}.json"
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(preds, open(out, "w"), indent=2, ensure_ascii=False)
            print("wrote", out)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--index", default="data/index/c100v2")
    export.add_argument("--mode", default="rrf")
    export.add_argument("--k", type=int, default=5)
    export.add_argument("--prompts", default="cloud/prompts.jsonl")
    export.set_defaults(func=cmd_export)
    imp = sub.add_parser("import")
    imp.add_argument("--answers", default="cloud/answers.json")
    imp.add_argument("--tag", default="qwen14b")
    imp.set_defaults(func=cmd_import)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
