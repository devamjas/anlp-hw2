import argparse
from pathlib import Path

from .crawl import crawl_seed
from .fetch import Fetcher
from .seeds import SEEDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--out", default="data/raw")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=5)
    args = parser.parse_args()

    if args.list:
        for seed in SEEDS:
            print(f"{seed.name:20s} {seed.source_type:8s} depth={seed.max_depth} max={seed.max_pages}")
        return

    Path(args.out).mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(delay=args.delay, retries=args.retries)
    for seed in SEEDS:
        if args.names and seed.name not in args.names:
            continue
        out_path = Path(args.out) / f"{seed.name}.jsonl"
        saved = crawl_seed(seed, fetcher, out_path)
        print(f"[{seed.name}] saved {saved} pages -> {out_path}")

    for url, reason in fetcher.failures.items():
        print(f"FAILED {reason}: {url}")


if __name__ == "__main__":
    main()
