# Friday 20 November 2026 — The World in One Day

[![Bounty](https://img.shields.io/badge/make.fun-news--image--20261120-red)](https://make.fun/bounty/news-image-20261120)
[![Stories](https://img.shields.io/badge/stories-44-blue)](https://make.fun/bounty/news-image-20261120)
[![Deterministic](https://img.shields.io/badge/render-deterministic-green)](https://make.fun/bounty/news-image-20261120)

A one-page newspaper front page for **Friday 20 November 2026**: 44 stories
(3 heroes + 11 cards + 30 briefs) across 7 regions, 14 original
code-drawn illustrations, a world map pinning the 14 main stories, a
strip of 6 big numbers, a THE DAY IN UTC strip with 4 verified markers,
and a DATE CHECK box listing the stories left out with their real dates.

## How it works

- `render_frontpage.py` (build machine only) draws `entry.png` with Pillow
  + Liberation fonts: 1024×1024, 232,159 bytes, byte-identical on every run.
  Verified sha256: `79817d9bb969763662bc6bdf20fb5eb8c20794faed4c4849e63c162dae278aab`.
- `main.py` is the graded entry point. It uses **only the Python standard
  library** and copies `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png`
  (default `/output/entry.png`). No network, no clock, no randomness.

## Verify

```sh
python3 main.py
python3 main.py
sha256sum /output/entry.png   # identical both runs
```
