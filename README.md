# Journal and conference feeds

Generates daily RSS feeds for 5 ACS journals (JACS, JCIM, JCTC, JMC, JPCL) from
[Crossref](https://api.crossref.org) metadata, since pubs.acs.org now sits
behind a Cloudflare bot challenge that blocks RSS reader backends (this is
almost certainly why the official ACS RSS/e-alerts stopped working).

Each feed item links via `https://doi.org/<DOI>`, which redirects to the real
article page on pubs.acs.org, so opening an entry from your reader takes you
straight to ACS as usual.

## How it runs

A GitHub Actions workflow (`.github/workflows/build-feeds.yml`) runs daily
(~03:17 UTC) and on manual trigger, regenerates `docs/*.xml`, and commits
them back to the repo. GitHub Pages serves the `docs/` folder.

Also included: feeds for ICLR/ICML/NeurIPS main-track papers, built from
arXiv's API (`scripts/build_arxiv_feeds.py`). These venues publish in
annual batches rather than continuously, so freshness depends on when
authors update their arXiv listing's comment field to note acceptance
(e.g. "Accepted at ICML 2026") - this picks that up via arXiv's public
API, sorted by last-updated date. Workshop papers are excluded.

## Feed URLs

Feeds are at `https://blannek.github.io/journal-feeds/<code>.xml`:

```
jacs.xml, jcim.xml, jctc.xml, jmc.xml, jpcl.xml   (ACS journals)
iclr.xml, icml.xml, neurips.xml                    (ML conferences, main track)
```

Subscribe to each URL in Innoreader like any normal RSS feed
(Add Subscription -> paste URL).

## Manually running a build

```
python scripts/build_feeds.py
python scripts/build_arxiv_feeds.py
python scripts/build_index.py
```
