import argparse
import json
from pathlib import Path

from tqdm import tqdm

from .metrics import score
from .reader import build_messages
from .run import is_refusal

JOBS = [
    ("leaderboard", "leaderboard_queries.json", ["sentence"]),
    ("dev", "public_evaluation_data.json", ["adaptive"]),
    ("test", "test_set_day_3.json", ["adaptive"]),
]

BACKUP = {
    "leaderboard|sentence": "leaderboard/leaderboard_devamjas_v3_sentence.json",
    "dev|adaptive": "outputs/dev_c100v2_rrf_adaptive.json",
    "test|adaptive": "../system_outputs/system_output_1.json",
}


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
    answers = answers.get("answers", answers)
    tag = args.tag
    for name, path, styles in JOBS:
        questions = json.load(open(path))
        for style in styles:
            backup = json.load(open(BACKUP[f"{name}|{style}"]))
            preds, used = {}, 0
            for q in questions:
                a = answers.get(f"{name}|{style}|{q['id']}", "")
                if is_refusal(a):
                    a, used = backup[q["id"]], used + 1
                preds[q["id"]] = a
            print(f"{name} {style}: {len(questions) - used} from {tag}, {used} from backup")
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
                out = f"outputs/test_day3_{tag}_{style}.json"
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
