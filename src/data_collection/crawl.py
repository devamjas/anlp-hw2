import json
import re
from collections import deque
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from tqdm import tqdm

from .extract import to_doc

SKIP_FILES = re.compile(r"\.(jpe?g|png|gif|svg|webp|ico|css|js|mp3|mp4|mov|zip|xml|json|docx?|xlsx?|pptx?)(\?|$)", re.I)
MIN_CHARS = 200


@dataclass
class Seed:
    name: str
    start_urls: List[str]
    source_type: str
    domains: Optional[List[str]] = None
    allow: Optional[str] = None
    deny: Optional[str] = None
    max_depth: int = 1
    max_pages: int = 100
    follow_links: bool = True


def normalize(url):
    url = url.split("#")[0]
    return url[:-1] if url.endswith("/") and url.count("/") > 3 else url


def host(url):
    name = urlparse(url).netloc.lower()
    return name[4:] if name.startswith("www.") else name


def crawl_seed(seed, fetcher, out_path):
    hosts = set(seed.domains or [host(u) for u in seed.start_urls])
    allow = re.compile(seed.allow) if seed.allow else None
    deny = re.compile(seed.deny) if seed.deny else None

    def wanted(link):
        return (host(link) in hosts
                and not SKIP_FILES.search(link)
                and (allow is None or allow.search(link))
                and (deny is None or not deny.search(link)))

    queue = deque((normalize(u), 0) for u in seed.start_urls)
    seen = {url for url, _ in queue}
    saved = 0

    with open(out_path, "w", encoding="utf-8") as out, tqdm(total=seed.max_pages, desc=seed.name) as bar:
        while queue and saved < seed.max_pages:
            url, depth = queue.popleft()
            response = fetcher.get(url)
            doc = to_doc(*response) if response else None
            if not doc:
                continue

            if len(doc["text"]) >= MIN_CHARS:
                record = {"url": response[1]["final_url"], "title": doc["title"],
                          "source": seed.name, "source_type": seed.source_type,
                          "text": doc["text"]}
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                saved += 1
                bar.update(1)

            if seed.follow_links and depth < seed.max_depth:
                for link in map(normalize, doc["links"]):
                    if link not in seen and wanted(link):
                        seen.add(link)
                        queue.append((link, depth + 1))
    return saved
