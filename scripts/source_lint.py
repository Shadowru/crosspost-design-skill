#!/usr/bin/env python3
"""Design gate for the canonical source, before anything is built.

None of the four target platforms lets you style your way out of a badly
structured article: no CSS survives, so rhythm, hierarchy and restraint are
the whole design. This checks the source for the failure modes that actually
show up after publishing — walls of text, emphasis inflation, headings the
platform cannot render, tables that will collapse into a list.

Usage:
    source_lint.py article.md [article2.md ...] [--strict]

--strict turns warnings into errors.
Exit codes: 1 = errors (or warnings with --strict); 0 = otherwise.
"""

import argparse
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_targets import parse_document, plain  # noqa: E402

SAFE_INLINE_HTML = {"u", "br", "sup", "sub", "abbr", "anchor", "spoiler", "cut"}


class Report:
    def __init__(self, path):
        self.path = path
        self.items = []

    def add(self, level, code, msg):
        self.items.append((level, code, msg))

    def error(self, code, msg):
        self.add("ERROR", code, msg)

    def warn(self, code, msg):
        self.add("WARN", code, msg)

    def info(self, code, msg):
        self.add("INFO", code, msg)


def words(text):
    return len(re.findall(r"[\w’'-]+", text, re.U))


def check(path, raw):
    rep = Report(path)
    doc = parse_document(raw)
    meta, blocks = doc["meta"], doc["blocks"]

    # -- front matter --------------------------------------------------
    if not meta.get("title") and doc["title"] == "Untitled":
        rep.error("no-title", "no title: add `title:` to the front matter or a `# ` line")
    if len(doc["title"]) > 80:
        rep.warn("long-title", "title is %d characters — Dzen and VK truncate around 80"
                 % len(doc["title"]))
    if not meta.get("lang"):
        rep.warn("no-lang", "no `lang:` — typography rules and UI labels are guessed")
    elif str(meta["lang"]).lower()[:2] not in ("ru", "en"):
        rep.warn("odd-lang", "`lang: %s` is neither ru nor en" % meta["lang"])
    lede = str(meta.get("lede", ""))
    if not lede:
        rep.warn("no-lede", "no `lede:` — the Telegram announcement and the Dzen feed "
                            "snippet fall back to the first paragraph")
    elif len(lede) > 300:
        rep.warn("long-lede", "lede is %d characters — keep it under ~300 so it "
                              "survives the feed snippet" % len(lede))
    if not meta.get("tags"):
        rep.info("no-tags", "no `tags:` — the Telegram post gets no hashtags")
    if not meta.get("canonical") and not meta.get("iv_url"):
        rep.info("no-canonical", "no `canonical:`/`iv_url:` — the announcement will "
                                 "have no “read in full” link")

    # -- placeholders --------------------------------------------------
    holes = set(re.findall(r"\{\{([^}]{0,40})\}\}", raw))
    if holes:
        rep.warn("placeholders", "%d unresolved placeholder(s): %s"
                 % (len(holes), ", ".join(sorted(holes)[:5])))

    # -- containers and footnotes --------------------------------------
    opens = len(re.findall(r"^:::+[^\S\n]*[\w-]+", raw, re.M))
    closes = len(re.findall(r"^:::+[^\S\n]*$", raw, re.M))
    if opens != closes:
        rep.error("container", "unbalanced ::: blocks (%d opened, %d closed)"
                  % (opens, closes))
    refs = set(re.findall(r"\[\^([^\]]+)\](?!:)", raw))
    defs = set(doc["footnotes"])
    for missing in sorted(refs - defs):
        rep.error("footnote", "footnote [^%s] is referenced but never defined" % missing)
    for unused in sorted(defs - refs):
        rep.warn("footnote", "footnote [^%s] is defined but never referenced" % unused)

    # -- structure -----------------------------------------------------
    headings = [b for b in blocks if b["type"] == "heading"]
    sections = [h for h in headings if h["level"] == 2]
    if len(sections) < 2:
        rep.warn("few-sections", "%d `##` section(s) — readers scan by heading on every "
                                 "one of these platforms" % len(sections))
    prev = 1
    for h in headings:
        if h["level"] > prev + 1:
            rep.warn("heading-jump", "heading jumps h%d -> h%d at «%s»"
                     % (prev, h["level"], plain(h["inline"])[:40]))
        if h["level"] > 3:
            rep.warn("deep-heading", "h%d at «%s» — Habr and telegra.ph stop at three "
                     "levels; it degrades to bold text"
                     % (h["level"], plain(h["inline"])[:40]))
        prev = h["level"]

    # -- rhythm --------------------------------------------------------
    run = 0
    for b in blocks:
        if b["type"] == "para":
            run += 1
            if run == 5:
                rep.warn("wall-of-text", "5 paragraphs in a row with no heading, list, "
                                         "quote or image — add a break")
        else:
            run = 0
        if b["type"] == "para":
            text = plain(b["inline"])
            if len(text) > 700:
                rep.warn("long-para", "a %d-character paragraph — split it (mobile "
                                      "readers see a grey block)" % len(text))

    prose = re.sub(r"```.*?```", "", raw, flags=re.S)
    prose = re.sub(r"^---\n.*?\n---\n", "", prose, flags=re.S)
    body_words = words(prose)
    strong_n = len(re.findall(r"\*\*[^*]+\*\*", raw))
    if body_words and strong_n > max(3, body_words / 150):
        rep.warn("emphasis-inflation",
                 "%d bold spans over ~%d words — bold everywhere reads as bold nowhere "
                 "(aim for one strong anchor per section)" % (strong_n, body_words))
    if body_words < 200:
        rep.info("short", "~%d words — Dzen ignores items under 300 characters and "
                          "ranks short articles poorly" % body_words)

    # -- elements that degrade badly -----------------------------------
    for b in blocks:
        if b["type"] == "image" and not b["alt"] and not b["caption"]:
            rep.warn("image-alt", "image %s has neither alt text nor a caption"
                     % b["src"][:60])
        if b["type"] == "code" and not b["lang"]:
            rep.warn("code-lang", "a code fence with no language — Habr highlights it, "
                                  "the others need the label as a hint")
        if b["type"] == "table":
            ncol = len(b["head"])
            if ncol > 4:
                rep.warn("wide-table", "a %d-column table — VK and Dzen flatten tables "
                                       "into a list, and wide ones become unreadable"
                         % ncol)
            if len(b["rows"]) > 8:
                rep.info("long-table", "a %d-row table flattens into %d list items on "
                                       "VK/Dzen" % (len(b["rows"]), len(b["rows"])))
        if b["type"] == "list" and len(b["items"]) == 1:
            rep.info("one-item-list", "a one-item list — make it a paragraph")

    has_cut = any(b["type"] == "cut" for b in blocks)
    has_tldr = any(b["type"] == "container" and b["kind"] == "tldr" for b in blocks)
    if not has_cut:
        rep.info("no-cut", "no `<!--cut-->` — the Telegram announcement will guess "
                           "where the teaser ends")
    if not has_tldr:
        rep.info("no-tldr", "no `:::tldr` block — the announcement bullets fall back to "
                            "section titles")

    stray = set(re.findall(r"<\s*/?\s*([a-zA-Z][\w-]*)", re.sub(r"```.*?```", "", raw,
                                                                flags=re.S)))
    for tag in sorted(stray - SAFE_INLINE_HTML):
        rep.warn("raw-html", "<%s> in the source — only %s survive everywhere"
                 % (tag, "/".join(sorted(SAFE_INLINE_HTML))))
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    bad = 0
    for path in args.files:
        if not os.path.isfile(path):
            print("✗ no such file: %s" % path, file=sys.stderr)
            bad += 1
            continue
        rep = check(path, io.open(path, encoding="utf-8").read())
        print("• %s" % path)
        marks = {"ERROR": "✗", "WARN": "!", "INFO": "·"}
        for level, code, msg in rep.items:
            print("   %s %-9s %-20s %s" % (marks[level], level, code, msg))
        if not rep.items:
            print("   ✓ nothing to flag")
        bad += sum(1 for lvl, _, _ in rep.items
                   if lvl == "ERROR" or (args.strict and lvl == "WARN"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
