import glob
import json
import os
import time

WIDTH = 40


def bar(done, total):
    filled = int(WIDTH * done / total) if total else 0
    return "#" * filled + "-" * (WIDTH - filled)


def results():
    rows = {}
    if os.path.exists("outputs/dev_results.jsonl"):
        for line in open("outputs/dev_results.jsonl"):
            r = json.loads(line)
            rows[r["config"]["out"]] = r
    return rows


def main():
    while True:
        scores = results()
        lines = [time.strftime("%H:%M:%S") + "  (Ctrl+C to exit)", ""]
        for path in sorted(glob.glob("outputs/*.progress") + glob.glob("../system_outputs/*.progress"),
                           key=os.path.getmtime):
            done, total = map(int, open(path).read().split("/"))
            name = os.path.basename(path).replace(".progress", "")
            out = path.replace(".progress", ".json")
            score = scores.get(out)
            tail = f"F1 {score['F1']:5.1f}  EM {score['EM']:5.1f}" if score else ("done" if done == total else "")
            lines.append(f"{name:28s} [{bar(done, total)}] {done:3d}/{total}  {tail}")
        os.system("clear")
        print("\n".join(lines))
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
