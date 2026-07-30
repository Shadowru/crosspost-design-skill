#!/usr/bin/env python3
"""Render a Markdown file to plain HTML for the README screenshots.

Reuses the skill's own parser, so the preview of `{slug}.habr.md` and
`{slug}.report.md` is built from the same code path as everything else.
Not part of the skill's runtime — documentation tooling only.

Usage:
    docs/render-md.py out/post.habr.md out/_habr.rendered.html
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from build_targets import IVPAGE, parse_document, render_html_target  # noqa: E402


def main():
    if len(sys.argv) < 3:
        print("usage: render-md.py <in.md> <out.html>", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        doc = parse_document(f.read())
    body, _ = render_html_target(IVPAGE, doc)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write("<h1>%s</h1>\n%s\n" % (doc["title"], body))
    print("✓ %s -> %s" % (sys.argv[1], sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
