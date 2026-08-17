#!/usr/bin/env python3
"""Build RSS feeds for ICLR/ICML/NeurIPS main-track papers from arXiv.

These conferences don't publish continuously like a journal - accepted
papers get their arXiv listing updated (often months after original
submission) with a note like "Accepted at ICML 2026" in the arXiv
"comment" field. This searches that field via arXiv's own public API
(export.arxiv.org) and sorts by last-updated date, so a paper shows up
here right around when its acceptance note was added, not when it was
first posted. Workshop papers are excluded (much less selective than the
main conference track) by skipping any comment mentioning "workshop".

This only catches papers where the authors added such a note - it's not
a complete list of everything accepted, but it's the fastest legitimate
signal available (venue sites like OpenReview block automated access).
"""
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
NS = {"a": ATOM_NS, "arxiv": ARXIV_NS}

VENUES = [
    {"code": "iclr", "name": "ICLR", "keywords": ["ICLR"]},
    {"code": "icml", "name": "ICML", "keywords": ["ICML"]},
    {"code": "neurips", "name": "NeurIPS", "keywords": ["NeurIPS", "NIPS"]},
]

LOOKBACK_DAYS = 14
MAX_RESULTS = 200
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
CONTACT_EMAIL = os.environ.get("FEED_CONTACT_EMAIL", "bruce.yang@genscript.com")
USER_AGENT = f"arxiv-venue-feed-builder/1.0 (personal RSS mirror; mailto:{CONTACT_EMAIL})"
API_DELAY_SECONDS = 3  # arXiv's requested minimum gap between requests
MAX_ATTEMPTS = 5
RETRY_BACKOFF_SECONDS = 10  # doubles each retry: 10, 20, 40, 80


def fetch_entries(keywords):
    query = " OR ".join(f"co:{k}" for k in keywords)
    params = {
        "search_query": query,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
        "max_results": str(MAX_RESULTS),
    }
    url = f"https://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    delay = RETRY_BACKOFF_SECONDS
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            return ET.fromstring(body).findall("a:entry", NS)
        except (urllib.error.URLError, ET.ParseError) as e:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"  attempt {attempt} failed ({e}), retrying in {delay}s")
            time.sleep(delay)
            delay *= 2


def parse_dt(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def build_item(entry):
    entry_id = entry.findtext("a:id", default="", namespaces=NS).strip()
    title = " ".join(entry.findtext("a:title", default="", namespaces=NS).split())
    updated = parse_dt(entry.findtext("a:updated", default="", namespaces=NS))
    authors = [
        a.findtext("a:name", default="", namespaces=NS).strip()
        for a in entry.findall("a:author", NS)
    ]
    return {
        "id": entry_id,
        "title": title,
        "updated": updated,
        "authors": ", ".join(n for n in authors if n),
    }


def build_item_xml(item):
    pub_date = item["updated"].strftime("%a, %d %b %Y %H:%M:%S +0000")
    return f"""    <item>
      <title>{escape(item['title'])}</title>
      <link>{escape(item['id'])}</link>
      <guid isPermaLink="true">{escape(item['id'])}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{escape(item['authors'])}</description>
    </item>"""


def build_rss(venue, items):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items_xml = "\n".join(build_item_xml(i) for i in items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(venue['name'])} - New Main-Track Papers (via arXiv)</title>
    <link>https://arxiv.org</link>
    <description>Unofficial feed of arXiv papers whose comment field notes acceptance at {escape(venue['name'])} (main track only, workshops excluded).</description>
    <lastBuildDate>{now}</lastBuildDate>
{items_xml}
  </channel>
</rss>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    for i, venue in enumerate(VENUES):
        if i > 0:
            time.sleep(API_DELAY_SECONDS)
        entries = fetch_entries(venue["keywords"])

        items = []
        for entry in entries:
            comment = entry.findtext("arxiv:comment", default="", namespaces=NS) or ""
            if "workshop" in comment.lower():
                continue
            item = build_item(entry)
            if item["updated"] < cutoff:
                continue
            items.append(item)

        rss = build_rss(venue, items)
        out_path = os.path.join(OUT_DIR, f"{venue['code']}.xml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rss)
        print(f"{venue['code']}: wrote {len(items)} items -> {out_path}")


if __name__ == "__main__":
    main()
