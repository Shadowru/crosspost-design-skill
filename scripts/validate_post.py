#!/usr/bin/env python3
"""Platform markup compliance checker for Telegram / VK / Dzen / Habr output.

Every one of these platforms accepts a *whitelist* of markup and silently drops
the rest. This turns that whitelist into a deterministic gate: run it on the
built artifacts before publishing, fix every ERROR, read every WARNING.

Usage:
    validate_post.py --platform telegraph  post.telegram-iv.html
    validate_post.py --platform tg-post    post.telegram-post.html [--limit 1024]
    validate_post.py --platform vk         post.vk.html
    validate_post.py --platform dzen       post.dzen.html
    validate_post.py --platform habr       post.habr.md
    validate_post.py --auto out/*.html out/*.md      # guess from the file name

Exit codes: 1 = at least one ERROR, 0 = clean or warnings only.
"""

import argparse
import glob
import os
import re
import sys
from html.parser import HTMLParser

# --------------------------------------------------------------------------
# Platform rules
# --------------------------------------------------------------------------

RULES = {
    # telegra.ph node whitelist (telegra.ph/api). Attributes: href, src only.
    "telegraph": {
        "label": "Telegram Instant View (telegra.ph body)",
        "tags": {"a", "aside", "b", "blockquote", "br", "code", "em", "figcaption",
                 "figure", "h3", "h4", "hr", "i", "iframe", "img", "li", "ol", "p",
                 "pre", "s", "strong", "u", "ul", "video"},
        "attrs": {"href", "src"},
        "hints": {
            "h1": "telegra.ph has no h1/h2 — the page title is a separate field, "
                  "body headings are h3/h4",
            "h2": "telegra.ph has no h1/h2 — use h3/h4",
            "table": "telegra.ph has no tables — degrade to <pre> or a list",
            "div": "not in the node whitelist — use <p>/<figure>/<aside>",
            "span": "not in the node whitelist — the wrapper is dropped and the "
                    "styling with it",
        },
    },
    "iv-page": {
        "label": "self-hosted Instant View source page",
        "tags": None,  # full HTML is fine; IV rules do the extraction
        "attrs": None,
        "require": [("<article", "no <article> element — IV templates key off it"),
                    ("<h1", "no <h1> — IV takes the title from it"),
                    ('property="og:title"', "no og:title meta")],
        "forbid": [("<script", "WARNING", "IV ignores scripts; keep the page static"),
                   ("<iframe", "WARNING", "iframes need an explicit @inline/embed rule "
                                          "in the IV template")],
    },
    # Bot API "HTML style".
    "tg-post": {
        "label": "Telegram post (parse_mode=HTML)",
        "tags": {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
                 "a", "code", "pre", "blockquote", "span", "tg-spoiler", "tg-emoji", "br"},
        "attrs": {"href", "class", "emoji-id", "expandable"},
        "limit": 4096,
        "hints": {
            "p": "Telegram messages have no block tags — use blank lines",
            "ul": "no lists in messages — use • bullets as plain text",
            "ol": "no lists in messages — number the lines yourself",
            "h1": "no headings in messages — use <b> on its own line",
            "h2": "no headings in messages — use <b> on its own line",
            "h3": "no headings in messages — use <b> on its own line",
            "img": "images are attachments, not markup — send as photo with a caption",
            "br": "<br> is not a Telegram tag — use a real newline",
        },
    },
    "vk": {
        "label": "VK article editor (pasted rich text)",
        "tags": {"p", "h1", "h2", "h3", "h4", "b", "strong", "i", "em", "s", "del",
                 "a", "ul", "ol", "li", "blockquote", "br"},
        "attrs": {"href"},
        "hints": {
            "img": "VK does not accept pasted images — upload them in the editor",
            "figure": "dropped on paste — the image must be uploaded separately",
            "pre": "VK has no code block — degrade to a quote",
            "code": "VK has no code style — degrade to plain text or a quote",
            "table": "VK has no tables — degrade to a list",
            "iframe": "embeds are inserted through the editor's + menu, not pasted",
            "u": "the VK editor has no underline — it is dropped on paste",
            "hr": "the divider is an editor block, not markup — use a * * * line",
        },
    },
    "dzen": {
        "label": "Dzen article (content:encoded / editor paste)",
        "tags": {"p", "h1", "h2", "h3", "h4", "b", "i", "u", "s", "a", "ul", "ol",
                 "li", "blockquote", "figure", "figcaption", "img", "video",
                 "source", "iframe", "br"},
        "attrs": {"href", "src", "alt", "id", "type", "poster"},
        "hints": {
            "h5": "Dzen supports h1-h4 only",
            "h6": "Dzen supports h1-h4 only",
            "pre": "Dzen has no code block — degrade to a quote",
            "code": "Dzen has no code style — degrade to plain text",
            "table": "Dzen has no tables — degrade to a list",
            "strong": "use <b> — Dzen's whitelist names b/i/u/s",
            "em": "use <i> — Dzen's whitelist names b/i/u/s",
        },
    },
}

HABR_HTML_OK = {"u", "sup", "sub", "abbr", "anchor", "spoiler", "details", "summary",
                "oembed", "cut", "br", "img", "a", "b", "i", "s", "strong", "em",
                "code", "pre", "persona", "table", "thead", "tbody", "tr", "td", "th",
                "ul", "ol", "li", "blockquote", "p", "hr", "video", "source", "iframe",
                "font", "del", "ins"}


class TagAudit(HTMLParser):
    def __init__(self, rule):
        super().__init__(convert_charrefs=True)
        self.rule = rule
        self.bad_tags = {}
        self.bad_attrs = {}
        self.tags_seen = set()
        self.li_format = 0
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.tags_seen.add(tag)
        allowed = self.rule.get("tags")
        if allowed is not None and tag not in allowed:
            self.bad_tags[tag] = self.bad_tags.get(tag, 0) + 1
        ok_attrs = self.rule.get("attrs")
        if ok_attrs is not None:
            for name, _ in attrs:
                if name not in ok_attrs:
                    self.bad_attrs[name] = self.bad_attrs.get(name, 0) + 1
        if tag in ("b", "i", "u", "s", "strong", "em", "code") and "li" in self.stack:
            self.li_format += 1
        if tag not in ("br", "hr", "img", "source"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag:
                del self.stack[i:]
                break


def check_html(text, platform):
    rule = RULES[platform]
    errors, warnings = [], []

    if rule.get("tags") is not None or rule.get("attrs") is not None:
        audit = TagAudit(rule)
        try:
            audit.feed(text)
        except Exception as e:
            warnings.append("HTML parsing stopped early: %s" % e)
        for tag, n in sorted(audit.bad_tags.items()):
            hint = rule.get("hints", {}).get(tag, "not in this platform's whitelist")
            errors.append("<%s> ×%d — %s" % (tag, n, hint))
        for attr, n in sorted(audit.bad_attrs.items()):
            if platform == "tg-post" and attr == "class":
                continue
            errors.append('attribute %s="…" ×%d — not in this platform\'s attribute '
                          "whitelist; it is stripped on import" % (attr, n))
        if platform == "dzen" and audit.li_format:
            warnings.append("%d formatted span(s) inside <li> — Dzen does not render "
                            "formatting inside lists" % audit.li_format)
        if platform == "vk" and "hr" in audit.tags_seen:
            warnings.append("<hr> is dropped on paste — use a '* * *' paragraph")

    for needle, msg in rule.get("require", []):
        if needle.lower() not in text.lower():
            errors.append(msg)
    for needle, level, msg in rule.get("forbid", []):
        if needle.lower() in text.lower():
            (errors if level == "ERROR" else warnings).append(msg)

    if "style=" in text.lower():
        errors.append("inline style attributes — every one of these platforms "
                      "strips CSS; carry meaning with structure instead")
    if re.search(r"<(script|style)[\s>]", text, re.I):
        errors.append("<script>/<style> blocks are removed")

    limit = rule.get("limit")
    if limit:
        plain_len = len(re.sub(r"<[^>]+>", "", text))
        if plain_len > limit:
            errors.append("message is %d characters, the limit is %d "
                          "(captions are 1024)" % (plain_len, limit))
        elif plain_len > limit * 0.9:
            warnings.append("message is %d characters — close to the %d limit"
                            % (plain_len, limit))
    return errors, warnings


def check_habr(text):
    errors, warnings = [], []

    fences = re.findall(r"^\s*(`{3,})", text, re.M)
    if len(fences) % 2:
        errors.append("unbalanced ``` code fence")

    for m in re.finditer(r"^(#{4,})\s", text, re.M):
        errors.append("heading level %d — Habr supports # ## ### only"
                      % len(m.group(1)))

    opens = len(re.findall(r"<spoiler\b", text, re.I))
    closes = len(re.findall(r"</spoiler>", text, re.I))
    if opens != closes:
        errors.append("unbalanced <spoiler> (%d open, %d closed)" % (opens, closes))
    for m in re.finditer(r"<spoiler(?![^>]*title=)", text, re.I):
        warnings.append("<spoiler> without title= — the fold gets no label")

    masked = re.sub(r"```.*?```", "", text, flags=re.S)
    masked = re.sub(r"`[^`]*`", "", masked)
    for m in re.finditer(r"<\s*/?\s*([a-zA-Z][\w-]*)", masked):
        tag = m.group(1).lower()
        if tag not in HABR_HTML_OK:
            errors.append("<%s> is not accepted by Habr's sanitiser" % tag)
    if re.search(r'\sstyle\s*=', masked, re.I):
        errors.append("style attributes are stripped by Habr")
    if re.search(r'\sclass\s*=', masked, re.I):
        warnings.append("class attributes are stripped by Habr")

    for idx, m in enumerate(re.finditer(r"^\s*`{3,}(.*)$", text, re.M)):
        if idx % 2 == 0 and not m.group(1).strip():   # opening fences only
            warnings.append("code fence without a language — Habr highlights 20+ "
                            "languages, name yours")
            break

    if not re.search(r"^##?\s", text, re.M):
        warnings.append("no ## sections — long Habr posts need navigable headings")
    return errors, warnings


def guess_platform(path):
    name = os.path.basename(path).lower()
    for key, plat in (("telegram-iv", "telegraph"), ("iv-page", "iv-page"),
                      ("telegram-post", "tg-post"), (".vk.", "vk"),
                      (".dzen.", "dzen"), (".habr.", "habr")):
        if key in name:
            return plat
    return None


def run(path, platform, limit=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if path.lower().endswith(".rss.xml"):
        # Only the CDATA payload is article markup; the RSS envelope is not.
        m = re.search(r"<content:encoded>\s*<!\[CDATA\[(.*?)\]\]>\s*</content:encoded>",
                      text, re.S)
        if not m:
            print("• %s\n   ✗ ERROR   no <content:encoded><![CDATA[…]]> payload" % path)
            return 1
        text = m.group(1)
    if platform == "habr":
        errors, warnings = check_habr(text)
        label = "Habr Flavored Markdown"
    else:
        if limit:
            RULES[platform]["limit"] = limit
        errors, warnings = check_html(text, platform)
        label = RULES[platform]["label"]

    print("• %s  [%s]" % (path, label))
    for e in errors:
        print("   ✗ ERROR   %s" % e)
    for w in warnings:
        print("   ! WARN    %s" % w)
    if not errors and not warnings:
        print("   ✓ clean")
    return len(errors)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--platform", choices=sorted(list(RULES) + ["habr"]))
    ap.add_argument("--auto", action="store_true",
                    help="infer the platform from each file name")
    ap.add_argument("--limit", type=int, help="override the character limit (tg-post)")
    args = ap.parse_args()

    paths = []
    for pattern in args.files:
        hits = glob.glob(pattern)
        paths.extend(hits or [pattern])

    total = 0
    checked = 0
    for path in paths:
        if not os.path.isfile(path):
            print("✗ no such file: %s" % path, file=sys.stderr)
            total += 1
            continue
        platform = args.platform or guess_platform(path)
        if not platform:
            if args.auto:
                continue
            print("✗ cannot infer the platform for %s — pass --platform" % path,
                  file=sys.stderr)
            total += 1
            continue
        total += run(path, platform, args.limit)
        checked += 1

    print("\n%s %d file(s) checked, %d error(s)"
          % ("✓" if not total else "✗", checked, total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
