import re
import string
from collections import Counter


def normalize(text):
    text = text.lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return text.split()


def exact_match(pred, ref):
    return float(normalize(pred) == normalize(ref))


def f1(pred, ref):
    p, r = normalize(pred), normalize(ref)
    common = sum((Counter(p) & Counter(r)).values())
    if common == 0:
        return 0.0
    precision, recall = common / len(p), common / len(r)
    return 2 * precision * recall / (precision + recall)


def answer_recall(pred, ref):
    p, r = normalize(pred), normalize(ref)
    if not r:
        return 0.0
    return sum((Counter(p) & Counter(r)).values()) / len(r)


def rouge_l(pred, ref):
    p, r = normalize(pred), normalize(ref)
    if not p or not r:
        return 0.0
    table = [[0] * (len(r) + 1) for _ in range(len(p) + 1)]
    for i in range(len(p)):
        for j in range(len(r)):
            table[i + 1][j + 1] = table[i][j] + 1 if p[i] == r[j] else max(table[i][j + 1], table[i + 1][j])
    lcs = table[-1][-1]
    if lcs == 0:
        return 0.0
    precision, recall = lcs / len(p), lcs / len(r)
    return 2 * precision * recall / (precision + recall)


METRICS = {"EM": exact_match, "F1": f1, "Recall": answer_recall, "ROUGE-L": rouge_l}


def score(predictions, dataset):
    totals = {name: 0.0 for name in METRICS}
    for example in dataset:
        pred = predictions.get(example["id"], "")
        for name, fn in METRICS.items():
            totals[name] += max(fn(pred, ref) for ref in example["answers"])
    return {name: round(100 * value / len(dataset), 1) for name, value in totals.items()}
