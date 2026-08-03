#!/usr/bin/env python3
"""Build per-journal RSS feeds for select ACS journals from Crossref metadata.

Crossref (api.crossref.org) is used instead of scraping pubs.acs.org directly
because ACS now serves pubs.acs.org behind a Cloudflare bot challenge that
blocks non-browser HTTP clients (including RSS reader backends). Crossref is
a free, public, scraping-friendly API; each entry links via DOI, which
redirects straight to the article's real pubs.acs.org page.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

JOURNALS = [
    {"code": "jacs", "name": "Journal of the American Chemical Society", "coden": "jacsat", "issn": "1520-5126"},
    {"code": "jcim", "name": "Journal of Chemical Information and Modeling", "coden": "jcisd8", "issn": "1549-960X"},
    {"code": "jctc", "name": "Journal of Chemical Theory and Computation", "coden": "jctcce", "issn": "1549-9626"},
    {"code": "jmc", "name": "Journal of Medicinal Chemistry", "coden": "jmcmar", "issn": "1520-4804"},
    {"code": "jpcl", "name": "The Journal of Physical Chemistry Letters", "coden": "jpclcd", "issn": "1948-7185"},
]

LOOKBACK_DAYS = 14
ROWS = 60
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
CONTACT_EMAIL = os.environ.get("FEED_CONTACT_EMAIL", "bruce.yang@genscript.com")
USER_AGENT = f"acs-feed-builder/1.0 (personal RSS mirror; mailto:{CONTACT_EMAIL})"


def fetch_works(issn):
    since = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    params = {
        "filter": f"from-created-date:{since},type:journal-article",
        "sort": "created",
        "order": "desc",
        "rows": str(ROWS),
        "select": "DOI,title,author,created,abstract",
    }
    url = f"https://api.crossref.org/journals/{urllib.parse.quote(issn)}/works?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    items = data.get("message", {}).get("items", [])
    # Skip front-matter entries (issue mastheads, TOC pages, etc.) - these
    # have no authors, unlike real articles.
    return [i for i in items if i.get("author")]


def clean_title(item):
    titles = item.get("title") or ["(untitled)"]
    return " ".join(titles[0].split())


def format_authors(item):
    names = []
    for a in item.get("author") or []:
        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if name:
            names.append(name)
    return ", ".join(names)


def rfc822_from_date_parts(container):
    parts = (container or {}).get("date-parts", [[None]])[0]
    try:
        y, m, d = (parts + [1, 1])[:3]
        dt = datetime(y, m or 1, d or 1, tzinfo=timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def build_item_xml(item):
    doi = item["DOI"]
    link = f"https://doi.org/{doi}"
    title = escape(clean_title(item))
    authors = escape(format_authors(item))
    pub_date = rfc822_from_date_parts(item.get("created"))
    description = escape(authors) if authors else ""
    return f"""    <item>
      <title>{title}</title>
      <link>{escape(link)}</link>
      <guid isPermaLink="false">{escape(doi)}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>"""


def build_rss(journal, items):
    channel_link = f"https://pubs.acs.org/journal/{journal['coden']}"
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items_xml = "\n".join(build_item_xml(i) for i in items if i.get("DOI"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(journal['name'])} - New Articles</title>
    <link>{escape(channel_link)}</link>
    <description>Unofficial feed of new {escape(journal['name'])} articles, built from Crossref metadata.</description>
    <lastBuildDate>{now}</lastBuildDate>
{items_xml}
  </channel>
</rss>
"""


def build_index_html(journals):
    rows = "\n".join(
        f'      <li><a href="{j["code"]}.xml">{escape(j["name"])}</a> '
        f'(<code>{j["code"]}.xml</code>)</li>'
        for j in journals
    )
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>ACS Journal Feeds</title></head>
<body>
  <h1>ACS journal feeds (unofficial, Crossref-based)</h1>
  <ul>
{rows}
  </ul>
</body>
</html>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # Tell GitHub Pages to skip its Jekyll build and serve files as-is.
    open(os.path.join(OUT_DIR, ".nojekyll"), "a").close()
    for journal in JOURNALS:
        items = fetch_works(journal["issn"])
        rss = build_rss(journal, items)
        out_path = os.path.join(OUT_DIR, f"{journal['code']}.xml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rss)
        print(f"{journal['code']}: wrote {len(items)} items -> {out_path}")

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index_html(JOURNALS))


if __name__ == "__main__":
    main()
