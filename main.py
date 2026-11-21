#!/usr/bin/env python3
"""Entry point for the news-image-20261120 bounty.

Stdlib-only: copies the pre-rendered front page (entry.png, built by
render_frontpage.py on the build machine) to the grader output dir.
No network, no clock, no randomness — byte-identical on every run.

Usage: python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png)
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    src = os.path.join(HERE, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    n = os.path.getsize(dst)
    assert n == os.path.getsize(src), "copy size mismatch"
    print("wrote", dst, n, "bytes")


if __name__ == "__main__":
    main()
