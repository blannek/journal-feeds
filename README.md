# ACS journal feeds

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

## Feed URLs

Once GitHub Pages is enabled (Settings -> Pages -> Source: `main` branch,
`/docs` folder), the feeds are at:

```
https://<your-username>.github.io/<repo>/jacs.xml
https://<your-username>.github.io/<repo>/jcim.xml
https://<your-username>.github.io/<repo>/jctc.xml
https://<your-username>.github.io/<repo>/jmc.xml
https://<your-username>.github.io/<repo>/jpcl.xml
```

Subscribe to each URL in Innoreader like any normal RSS feed
(Add Subscription -> paste URL).

## Manually running a build

```
python scripts/build_feeds.py
```
