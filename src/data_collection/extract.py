import io
import re
from urllib.parse import urljoin, urldefrag

from bs4 import BeautifulSoup
from pypdf import PdfReader

NOISE_TAGS = ["script", "style", "noscript", "svg", "iframe", "nav",
              "footer", "aside", "button"]
NOISE_SELECTORS = [".mw-editsection", "sup.reference", ".reflist", ".references",
                   ".navbox", ".toc", "#toc"]
SOCIAL = re.compile(r"https?://(?:www\.)?(instagram|twitter|x|facebook|tiktok|youtube)\.com/@?([A-Za-z0-9_.]+)/?$", re.I)
SOCIAL_NAMES = {"instagram": "Instagram", "twitter": "X/Twitter", "x": "X/Twitter", "facebook": "Facebook",
                "tiktok": "TikTok", "youtube": "YouTube"}
SOCIAL_SKIP = {"share", "sharer", "sharer.php", "intent", "p", "reel", "watch", "channel", "user", "c", "hashtag"}


def clean_lines(text):
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    kept = []
    for line in lines:
        if line and (not kept or line != kept[-1]):
            kept.append(line)
    return "\n".join(kept)


def get_links(soup, base_url):
    links = []
    for a in soup.find_all("a", href=True):
        url, _ = urldefrag(urljoin(base_url, a["href"]))
        if url.startswith("http"):
            links.append(url)
    return links


def social_handles(links):
    found = {}
    for url in links:
        match = SOCIAL.match(url)
        if match and match.group(2).lower() not in SOCIAL_SKIP:
            found.setdefault(SOCIAL_NAMES[match.group(1).lower()], "@" + match.group(2))
    return "; ".join(f"{site} {handle}" for site, handle in found.items())


def remove_noise(soup):
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    for selector in NOISE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()


def tables_to_rows(soup):
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            cells = [c for c in cells if c]
            if cells:
                rows.append(" | ".join(cells))
        table.replace_with(soup.new_string("\n" + "\n".join(rows) + "\n"))


def html_to_doc(html, base_url):
    soup = BeautifulSoup(html, "lxml")

    links = get_links(soup, base_url)
    title_tag = soup.title or soup.find("h1")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""
    meta = soup.find("meta", attrs={"name": "description"})
    description = meta["content"].strip() if meta and meta.get("content") else ""
    if description and description not in title:
        title = f"{title} | {description}"

    remove_noise(soup)
    tables_to_rows(soup)
    root = soup.find("main") or soup.body or soup
    text = clean_lines(root.get_text("\n"))
    handles = social_handles(links)
    if handles:
        text += f"\nSocial media: {handles}"

    return {"title": title, "text": text, "links": links}


def pdf_to_doc(data, url):
    try:
        pages = [page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages]
    except Exception:
        return None
    return {"title": url.rsplit("/", 1)[-1], "text": clean_lines("\n".join(pages)), "links": []}


def to_doc(body, meta):
    url = meta["final_url"]
    content_type = meta["content_type"]
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return pdf_to_doc(body, url)
    if "html" in content_type:
        return html_to_doc(body.decode("utf-8", errors="ignore"), url)
    return None
