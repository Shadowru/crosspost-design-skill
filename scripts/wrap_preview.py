#!/usr/bin/env python3
"""Wrap a built VK/Dzen body in a browser page with a one-click Copy button.

VK and Dzen have no import path — the only way in is pasting *rendered rich
text*. Opening the raw .html file and copying its source pastes tags as
literal characters; this page renders the markup first, so the clipboard
carries real formatting.

The button, the styling and the script live in the wrapper only, never inside
the copied region, so what lands in the editor is the clean fragment.

Usage:
    wrap_preview.py out/post.vk.html [output.html]
    wrap_preview.py out/post.dzen.html

Exit codes: 0 ok; 1 missing file or template.
"""

import os
import sys

TARGETS = {
    ".vk.": "VK article editor",
    ".dzen.": "Dzen editor",
    "telegram-iv": "telegra.ph editor",
    "iv-page": "Instant View source page",
}


def target_label(name):
    lowered = name.lower()
    for key, label in TARGETS.items():
        if key in lowered:
            return label
    return "article editor"


def main():
    if len(sys.argv) < 2:
        print("usage: wrap_preview.py <built.html> [output.html]", file=sys.stderr)
        return 1
    src = sys.argv[1]
    if not os.path.isfile(src):
        print("✗ no such file: %s" % src, file=sys.stderr)
        return 1

    here = os.path.dirname(os.path.abspath(__file__))
    tpl_path = os.path.join(here, "..", "assets", "preview-template.html")
    if not os.path.isfile(tpl_path):
        print("✗ template missing: %s" % tpl_path, file=sys.stderr)
        return 1

    with open(src, encoding="utf-8") as f:
        content = f.read().strip()
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()

    base = os.path.basename(src)
    page = (tpl.replace("{{TITLE}}", os.path.splitext(base)[0])
               .replace("{{TARGET}}", target_label(base))
               .replace("<!--POST_CONTENT-->", content))

    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".preview.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)

    print("✓ preview page: %s" % out)
    print("  open it in a browser → Copy → paste into the %s" % target_label(base))
    print("  validate the original fragment, not this page (it contains style/script)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
