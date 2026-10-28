import time
from pathlib import Path

import requests
from requests_cache import CachedSession

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 CMU-ANLP-HW2-student-crawler"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
WIKIMEDIA_HEADERS = {"User-Agent": "anlp-hw2-crawler/1.0 (https://github.com/devamjas/anlp-hw2) python-requests"}


class Fetcher:
    def __init__(self, cache_path="data/cache/http", delay=1.0, timeout=25, retries=5):
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.failures = {}
        self.session = CachedSession(cache_path, backend="sqlite", expire_after=-1,
                                     allowable_codes=(200,))
        self.session.headers.update(HEADERS)

    def get(self, url):
        for attempt in range(self.retries):
            try:
                headers = WIKIMEDIA_HEADERS if "wikipedia.org" in url else None
                r = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 200:
                    self.failures.pop(url, None)
                    if not r.from_cache:
                        time.sleep(self.delay)
                    meta = {"final_url": r.url,
                            "content_type": r.headers.get("Content-Type", "").lower()}
                    return r.content, meta
                self.failures[url] = r.status_code
                if r.status_code in (403, 404, 410):
                    return None
                if r.status_code == 429:
                    ra = r.headers.get("Retry-After", "")
                    time.sleep(min(int(ra), 60) if ra.isdigit() else 5 * (attempt + 1))
            except requests.RequestException as e:
                self.failures[url] = type(e).__name__
            time.sleep(2 ** attempt)
        return None
