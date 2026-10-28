import glob
import json


def split_long_line(line, max_words):
    words = line.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def chunk_text(text, max_words, overlap):
    units = []
    for line in text.split("\n"):
        units.extend(split_long_line(line, max_words))

    chunks, current, size = [], [], 0
    for unit in units:
        words = len(unit.split())
        if current and size + words > max_words:
            chunks.append("\n".join(current))
            tail, tail_size = [], 0
            for line in reversed(current):
                tail_size += len(line.split())
                if tail_size > overlap:
                    break
                tail.insert(0, line)
            current, size = tail, sum(len(line.split()) for line in tail)
        current.append(unit)
        size += words
    if current:
        chunks.append("\n".join(current))
    return chunks


def load_documents(pattern="data/raw/*.jsonl"):
    docs, seen_urls = [], set()
    for path in sorted(glob.glob(pattern)):
        for line in open(path, encoding="utf-8"):
            doc = json.loads(line)
            if doc["url"] not in seen_urls:
                seen_urls.add(doc["url"])
                docs.append(doc)
    return docs


def build_chunks(docs, max_words, overlap):
    chunks, seen_texts = [], set()
    for doc in docs:
        for piece in chunk_text(doc["text"], max_words, overlap):
            text = f"{doc['title']}\n{piece}"
            if text in seen_texts:
                continue
            seen_texts.add(text)
            chunks.append({"id": len(chunks), "url": doc["url"], "source": doc["source"], "text": text})
    return chunks
