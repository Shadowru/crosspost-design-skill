#!/usr/bin/env python3
"""Package the skill for upload to claude.ai (Customize → Skills → Upload a skill).

claude.ai wants a ZIP whose root is the skill *folder*, not the loose files:

    crosspost-design.zip
    └── crosspost-design/
        ├── SKILL.md
        ├── references/
        ├── scripts/
        └── assets/

Getting that wrong is the usual reason an upload bounces, so this builds it
instead of leaving you to zip by hand, and verifies the result before printing
success. README screenshots, git history, the eval suite and the plugin
manifests are left out: they do nothing in the web sandbox and only inflate the
archive.

Usage:
    make_web_zip.py [-o crosspost-design.zip]

Exit codes: 0 ok; 1 the skill name is invalid or the archive failed to verify.
"""

import argparse
import io
import os
import re
import sys
import zipfile

INCLUDE_FILES = ("SKILL.md", "LICENSE", "NOTICE")
INCLUDE_DIRS = ("references", "scripts", "assets")
SKIP_NAMES = {"__pycache__", ".DS_Store"}
SKIP_SUFFIX = (".pyc", ".zip")


def skill_name(root):
    head = io.open(os.path.join(root, "SKILL.md"), encoding="utf-8").read()
    m = re.search(r"^name:\s*(\S+)", head, re.M)
    return m.group(1) if m else ""


def collect(root):
    """(absolute path, path inside the archive) for everything worth shipping."""
    for name in INCLUDE_FILES:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            yield path, name
    for folder in INCLUDE_DIRS:
        base = os.path.join(root, folder)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
            for fn in sorted(filenames):
                if fn in SKIP_NAMES or fn.endswith(SKIP_SUFFIX):
                    continue
                full = os.path.join(dirpath, fn)
                yield full, os.path.relpath(full, root)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", help="output .zip (default: <name>.zip beside the skill)")
    ap.add_argument("--root", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    name = skill_name(root)
    if not re.fullmatch(r"[a-z0-9-]+", name or ""):
        print("✗ the `name:` in SKILL.md must be lowercase letters, digits and "
              "hyphens; found %r" % name, file=sys.stderr)
        return 1

    out = os.path.abspath(args.out or os.path.join(root, name + ".zip"))
    if os.path.exists(out):
        os.remove(out)

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for full, rel in collect(root):
            z.write(full, os.path.join(name, rel))
            count += 1

    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    if os.path.join(name, "SKILL.md") not in names:
        print("✗ %s/SKILL.md is missing from the archive" % name, file=sys.stderr)
        return 1

    print("✓ %s" % out)
    print("  %d files · %.0f KB" % (count, os.path.getsize(out) / 1024))
    print()
    print("  Upload it in claude.ai:")
    print("    Settings → Capabilities → turn on code execution")
    print("    Customize → Skills → + → Upload a skill → pick this file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
