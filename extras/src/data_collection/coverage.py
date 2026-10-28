import argparse
import glob
import json
import re


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower().replace("&", " and ")).split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/*.jsonl")
    ap.add_argument("--dev", default="public_evaluation_data.json")
    ap.add_argument("--misses", action="store_true")
    args = ap.parse_args()

    corpus = []
    for path in glob.glob(args.raw):
        for line in open(path, encoding="utf-8"):
            corpus.append(" " + " ".join(norm(json.loads(line)["text"])) + " ")
    big = "".join(corpus)
    print(f"corpus: {len(corpus)} docs, {len(big):,} normalized chars")

    dev = json.load(open(args.dev))
    covered = total = 0
    misses = []
    for ex in dev:
        short = [a for a in ex["answers"] if len(a.split()) <= 6]
        if not short:
            continue
        total += 1
        if any(" " + " ".join(norm(a)) + " " in big for a in short):
            covered += 1
        else:
            misses.append(ex)
    print(f"short-answer questions covered: {covered}/{total} = {covered / max(total, 1):.1%}")
    if args.misses:
        for ex in misses:
            print(f"  MISS: {ex['question']}  ->  {ex['answers'][0]}")


if __name__ == "__main__":
    main()
