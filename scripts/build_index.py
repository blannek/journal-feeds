#!/usr/bin/env python3
"""Generate docs/index.html listing whatever feed XML files currently exist.

Run this after all other build_*.py scripts, so it picks up every feed
regardless of which script produced it.
"""
import os
from xml.sax.saxutils import escape

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def main():
    xml_files = sorted(f for f in os.listdir(DOCS_DIR) if f.endswith(".xml"))
    rows = "\n".join(
        f'      <li><a href="{f}">{escape(f[:-4].upper())}</a> (<code>{f}</code>)</li>'
        for f in xml_files
    )
    html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Feeds</title></head>
<body>
  <h1>Feeds</h1>
  <ul>
{rows}
  </ul>
</body>
</html>
"""
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html: listed {len(xml_files)} feeds")


if __name__ == "__main__":
    main()
