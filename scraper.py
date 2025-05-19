# scraper.py
import argparse
import logging
import sys
import requests
from requests.adapters import HTTPAdapter, Retry
from newspaper import Article
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from nlp import summarize_text, classify_coin

# ─── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Shared HTTP Session with Retries ────────────────────
session = requests.Session()
retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update({
    "User-Agent": "MyCryptoScraper/1.0 (+https://yourdomain.com/bot)"
})

# ─── 1. Fetcher ───────────────────────────────────────────
def fetch_html(url: str, timeout: float = 10.0) -> str | None:
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"[fetch error] {url} → {e}")
        return None

# ─── 2. Extractor ─────────────────────────────────────────
def extract_article(html: str, url: str) -> tuple[str, str] | None:
    # 2a. Try Newspaper3k first
    art = Article(url)
    art.set_html(html)
    try:
        art.parse()
    except Exception as e:
        logger.warning(f"[newspaper parse failed] {url} → {e}")
        art.text = ""
    if len(art.text or "") > 200:
        title = art.title or "No title found"
        return title, art.text.strip()

    # 2b. Fallback to BeautifulSoup with basic ad removal
    soup = BeautifulSoup(html, "lxml")
    for ad in soup.select(".ad, .advertisement, [class*='promo'], [id*='ad']"):
        ad.decompose()

    blocks = soup.select("article")
    if not blocks:
        main = soup.select_one(".post-content") or soup.body or soup
        blocks = [main]

    paras = []
    for blk in blocks:
        paras.extend(p.get_text(strip=True) for p in blk.find_all("p"))

    boilerplate = ["subscribe", "click here", "advertisement", "promo"]
    kept = [
        p for p in paras
        if len(p) > 50 and not any(phrase in p.lower() for phrase in boilerplate)
    ]

    text = "\n\n".join(kept).strip()
    if not text:
        return None

    title = (soup.title.string or "No title found").strip()
    return title, text

# ─── URL Processor ────────────────────────────────────────
def process_url(url: str) -> dict:
    html = fetch_html(url)
    if html is None:
        return {"url": url, "error": "fetch failed"}

    result = extract_article(html, url)
    if not result:
        return {"url": url, "error": "extract failed"}

    title, text = result

    summary = summarize_text(text)
    coin    = classify_coin(text)

    return {
        "url":     url,
        "title":   title,
        "summary": summary,
        "coin":    coin
    }

# ─── Main / CLI ───────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape, summarize & classify crypto news")
    parser.add_argument("-f", "--file", help="Path to a text file with one URL per line")
    parser.add_argument(
        "-w", "--workers", type=int, default=5,
        help="Number of concurrent worker threads (default: 5)"
    )
    parser.add_argument("urls", nargs="*", help="One or more URLs to process")
    args = parser.parse_args()

    # Gather URLs
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                urls = [line.strip() for line in fh if line.strip()]
        except Exception as e:
            logger.error(f"Could not read file {args.file}: {e}")
            sys.exit(1)
    else:
        urls = args.urls

    if not urls:
        parser.error("Please provide some URLs, or use --file <path>")

    logger.info(f"Starting processing of {len(urls)} URL(s) with {args.workers} workers")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_url = {pool.submit(process_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                res = future.result()
            except Exception as e:
                logger.error(f"[processing error] {url} → {e}")
                res = {"url": url, "error": str(e)}
            results.append(res)

    # Print out results with summary & coin
    for r in results:
        print(f"\n=== Processing: {r['url']} ===")
        if "error" in r:
            print(f"[error] {r['error']}")
        else:
            print(f"Title:   {r['title']}\n")
            print(f"Summary: {r['summary']}\n")
            print(f"Coin:    {r['coin']}\n")


if __name__ == "__main__":
    main()