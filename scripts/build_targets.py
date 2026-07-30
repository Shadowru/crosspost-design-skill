#!/usr/bin/env python3
"""Canonical Markdown -> Telegram Instant View / VK / Dzen / Habr artifacts.

The design work happens in the canonical source (structure, lede, callouts,
rhythm). This script does the deterministic part: it degrades that single
source into each platform's *whitelisted* markup and reports every loss, so
nothing silently disappears between the draft and the published post.

Usage:
    build_targets.py article.md [-o OUTDIR] [-p telegram,vk,dzen,habr]
    build_targets.py article.md --slug my-post

Outputs (per requested platform):
    {slug}.telegram-iv.html    telegra.ph-compatible body (native Instant View)
    {slug}.iv-page.html        standalone semantic page for a self-hosted IV template
    {slug}.telegram-post.html  channel announcement, HTML parse_mode, <= 4096 chars
    {slug}.vk.html             paste-safe HTML for the VK article editor
    {slug}.dzen.html           content:encoded fragment for Dzen
    {slug}.dzen.rss.xml        ready-to-serve RSS <item> for Dzen ingestion
    {slug}.habr.md             Habr Flavored Markdown
    {slug}.report.md           what each platform dropped + manual steps

Exit codes: 0 ok, 1 input/parse failure.
"""

import argparse
import html as html_mod
import os
import re
import sys
from datetime import datetime, timezone

MAX_TG_POST = 4096
NBSP = "\u00a0"

# --------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------


def parse_frontmatter(text):
    meta, lines = {}, text.split("\n")
    if not lines or lines[0].strip() != "---":
        return meta, text
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", lines[i])
        if m:
            key, raw = m.group(1), m.group(2).strip()
            if raw.startswith("[") and raw.endswith("]"):
                val = [x.strip().strip("\"'") for x in raw[1:-1].split(",") if x.strip()]
            else:
                val = raw.strip("\"'")
            meta[key] = val
        i += 1
    return meta, "\n".join(lines[i + 1:])


# --------------------------------------------------------------------------
# Inline parsing
# --------------------------------------------------------------------------

INLINE = re.compile(
    r"""
      (?P<fence>`+)(?P<code>.+?)(?P=fence)
    | !\[(?P<img_alt>[^\]]*)\]\((?P<img_src>[^)\s]+)(?:\s+"(?P<img_title>[^"]*)")?\)
    | \[\^(?P<fn>[^\]]+)\]
    | \[(?P<l_text>[^\]]*)\]\((?P<l_url>[^)\s]+)(?:\s+"(?P<l_title>[^"]*)")?\)
    | \*\*(?P<b1>.+?)\*\*
    | __(?P<b2>.+?)__
    | (?<![\w*])\*(?P<i1>[^*\n]+?)\*(?![\w*])
    | (?<![\w_])_(?P<i2>[^_\n]+?)_(?![\w_])
    | ~~(?P<st>.+?)~~
    | ==(?P<mark>.+?)==
    | <u>(?P<u1>.*?)</u>
    | \+\+(?P<u2>.+?)\+\+
    | (?P<br><br\s*/?>)
    """,
    re.X | re.S,
)


def _pick(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def parse_inline(text):
    """Markdown inline string -> token list."""
    tokens, pos = [], 0
    if text is None:
        return tokens
    for m in INLINE.finditer(text):
        if m.start() > pos:
            tokens.append({"t": "text", "v": text[pos:m.start()]})
        d = m.groupdict()
        if d["code"] is not None:
            tokens.append({"t": "code", "v": d["code"]})
        elif d["img_src"] is not None:
            tokens.append({"t": "img", "src": d["img_src"],
                           "alt": d["img_alt"] or "", "title": d["img_title"] or ""})
        elif d["fn"] is not None:
            tokens.append({"t": "fnref", "id": d["fn"]})
        elif d["l_url"] is not None:
            tokens.append({"t": "link", "url": d["l_url"],
                           "kids": parse_inline(d["l_text"] or "")})
        elif d["b1"] is not None or d["b2"] is not None:
            tokens.append({"t": "strong", "kids": parse_inline(_pick(d["b1"], d["b2"]))})
        elif d["i1"] is not None or d["i2"] is not None:
            tokens.append({"t": "em", "kids": parse_inline(_pick(d["i1"], d["i2"]))})
        elif d["st"] is not None:
            tokens.append({"t": "del", "kids": parse_inline(d["st"])})
        elif d["mark"] is not None:
            tokens.append({"t": "mark", "kids": parse_inline(d["mark"])})
        elif d["u1"] is not None or d["u2"] is not None:
            tokens.append({"t": "u", "kids": parse_inline(_pick(d["u1"], d["u2"]))})
        elif d["br"] is not None:
            tokens.append({"t": "br"})
        pos = m.end()
    if pos < len(text):
        tokens.append({"t": "text", "v": text[pos:]})
    return tokens


def plain(tokens):
    """Token list -> bare text (for alt text, ASCII tables, post building)."""
    out = []
    for t in tokens:
        k = t["t"]
        if k == "text":
            out.append(t["v"])
        elif k == "code":
            out.append(t["v"])
        elif k == "br":
            out.append(" ")
        elif k == "fnref":
            out.append("[%s]" % t["id"])
        elif k == "img":
            out.append(t["alt"])
        else:
            out.append(plain(t.get("kids", [])))
    return "".join(out)


# --------------------------------------------------------------------------
# Block parsing
# --------------------------------------------------------------------------

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+#.-]*)\s*$")
ITEM = re.compile(r"^(\s*)([-*+]|(\d+)[.)])\s+(.*)$")
HR = re.compile(r"^\s*(\*\s*){3,}$|^\s*(-\s*){3,}$|^\s*(_\s*){3,}$")
CUT = re.compile(r"^\s*<!--\s*cut\s*-->\s*$", re.I)
CONTAINER = re.compile(r"^:::+\s*([\w-]+)\s*(.*)$")
EMBED = re.compile(r"^@\[(?P<kind>[\w-]+)\]\((?P<url>\S+)\)\s*$")
TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def starts_block(line):
    s = line.strip()
    return (not s or s.startswith(("#", ">", ":::"))
            or bool(FENCE.match(line) or ITEM.match(line) or HR.match(line)
                    or CUT.match(line) or EMBED.match(line)))


def parse_list(lines, i, footnotes):
    m = ITEM.match(lines[i])
    base, ordered = len(m.group(1)), m.group(3) is not None
    items, n = [], len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i
            while j < n and not lines[j].strip():
                j += 1
            nxt = ITEM.match(lines[j]) if j < n else None
            if nxt and len(nxt.group(1)) >= base:
                i = j
                continue
            break
        m = ITEM.match(line)
        if not m:
            break
        indent = len(m.group(1))
        if indent < base:
            break
        if indent > base:
            child, i = parse_list(lines, i, footnotes)
            if items:
                items[-1]["children"].append(child)
            continue
        if (m.group(3) is not None) != ordered:
            break
        items.append({"inline": parse_inline(m.group(4).strip()), "children": []})
        i += 1
    return {"type": "list", "ordered": ordered, "items": items}, i


def parse_blocks(text, footnotes=None):
    if footnotes is None:
        footnotes = {}
    lines, blocks, i = text.split("\n"), [], 0
    n = len(lines)
    while i < n:
        line, s = lines[i], lines[i].strip()
        if not s:
            i += 1
            continue

        if CUT.match(line):
            blocks.append({"type": "cut"})
            i += 1
            continue

        m = CONTAINER.match(s)
        if m:
            kind, title, inner = m.group(1).lower(), m.group(2).strip(), []
            i += 1
            while i < n and not re.match(r"^:::+\s*$", lines[i].strip()):
                inner.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "container", "kind": kind, "title": title,
                           "blocks": parse_blocks("\n".join(inner), footnotes)})
            continue

        m = FENCE.match(line)
        if m:
            lang, buf = m.group(2), []
            i += 1
            while i < n and not FENCE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(buf)})
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)),
                           "inline": parse_inline(m.group(2).strip())})
            i += 1
            continue

        if HR.match(line):
            blocks.append({"type": "hr"})
            i += 1
            continue

        m = EMBED.match(s)
        if m:
            blocks.append({"type": "embed", "kind": m.group("kind"), "url": m.group("url")})
            i += 1
            continue

        m = re.match(r"^\[\^([^\]]+)\]:\s*(.*)$", s)
        if m:
            fid, buf = m.group(1), [m.group(2)]
            i += 1
            while i < n and lines[i].startswith(("    ", "\t")) and lines[i].strip():
                buf.append(lines[i].strip())
                i += 1
            footnotes[fid] = parse_inline(" ".join(buf).strip())
            continue

        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            first = buf[0].strip() if buf else ""
            m = re.match(r"^\[!(\w+)\]\s*(.*)$", first)
            if m:
                blocks.append({"type": "callout", "kind": m.group(1).upper(),
                               "title": m.group(2).strip(),
                               "blocks": parse_blocks("\n".join(buf[1:]), footnotes)})
            else:
                blocks.append({"type": "quote",
                               "blocks": parse_blocks("\n".join(buf), footnotes)})
            continue

        if "|" in s and i + 1 < n and TABLE_SEP.match(lines[i + 1]) and "|" in lines[i + 1]:
            head = [parse_inline(c) for c in split_row(s)]
            aligns = []
            for c in split_row(lines[i + 1]):
                aligns.append("right" if c.endswith(":") and not c.startswith(":")
                              else "center" if c.startswith(":") and c.endswith(":")
                              else "left")
            i += 2
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append([parse_inline(c) for c in split_row(lines[i])])
                i += 1
            blocks.append({"type": "table", "head": head, "rows": rows, "align": aligns})
            continue

        if ITEM.match(line):
            block, i = parse_list(lines, i, footnotes)
            blocks.append(block)
            continue

        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not starts_block(lines[i]):
            buf.append(lines[i])
            i += 1
        para = " ".join(x.strip() for x in buf).strip()
        tokens = parse_inline(para)
        only_img = [t for t in tokens if not (t["t"] == "text" and not t["v"].strip())]
        if len(only_img) == 1 and only_img[0]["t"] == "img":
            t = only_img[0]
            blocks.append({"type": "image", "src": t["src"], "alt": t["alt"],
                           "caption": t["title"]})
        else:
            blocks.append({"type": "para", "inline": tokens})
    return blocks


def parse_document(text):
    meta, body = parse_frontmatter(text)
    footnotes = {}
    blocks = parse_blocks(body, footnotes)
    title = meta.get("title")
    if not title:
        for b in blocks:
            if b["type"] == "heading" and b["level"] == 1:
                title = plain(b["inline"])
                blocks.remove(b)
                break
    else:
        blocks = [b for b in blocks
                  if not (b["type"] == "heading" and b["level"] == 1
                          and plain(b["inline"]).strip() == str(title).strip())]
    return {"meta": meta, "title": title or "Untitled", "blocks": blocks,
            "footnotes": footnotes, "lang": (meta.get("lang") or "en").lower()[:2]}


# --------------------------------------------------------------------------
# Localised chrome
# --------------------------------------------------------------------------

L10N = {
    "ru": {"notes": "Примечания", "tldr": "Коротко", "read_full": "Читать целиком",
           "spoiler": "Подробности", "source": "Источник", "table": "Таблица",
           "NOTE": "Заметка", "TIP": "Совет", "IMPORTANT": "Важно",
           "WARNING": "Внимание", "CAUTION": "Осторожно", "EXAMPLE": "Пример",
           "img_todo": "Изображение", "upload": "загрузить в редакторе"},
    "en": {"notes": "Notes", "tldr": "TL;DR", "read_full": "Read in full",
           "spoiler": "Details", "source": "Source", "table": "Table",
           "NOTE": "Note", "TIP": "Tip", "IMPORTANT": "Important",
           "WARNING": "Warning", "CAUTION": "Caution", "EXAMPLE": "Example",
           "img_todo": "Image", "upload": "upload in the editor"},
}


def t(lang, key):
    return L10N.get(lang, L10N["en"]).get(key, L10N["en"].get(key, key))


def esc(s):
    return html_mod.escape(s, quote=True)


# --------------------------------------------------------------------------
# HTML rendering profiles
# --------------------------------------------------------------------------

TELEGRAPH = {
    "id": "telegraph",
    "h": {1: "h3", 2: "h3", 3: "h4", 4: None, 5: None, 6: None},
    "inline": {"strong": "strong", "em": "em", "del": "s", "u": "u",
               "mark": "strong", "code": "code", "link": True},
    "code_block": "pre", "table": "pre", "image": "figure", "iframe": True,
    "callout": "aside", "hr": "<hr>", "quote": "blockquote", "list_inline": True,
    "cut_note": "`<!--cut-->` does not affect the article page — it marks where the "
                "channel announcement stops teasing",
}
IVPAGE = {
    "id": "iv-page",
    "h": {1: "h2", 2: "h2", 3: "h3", 4: "h4", 5: "h5", 6: "h6"},
    "inline": {"strong": "strong", "em": "em", "del": "s", "u": "u",
               "mark": "strong", "code": "code", "link": True},
    "code_block": "pre", "table": "table", "image": "figure", "iframe": True,
    "callout": "aside", "hr": "<hr>", "quote": "blockquote", "list_inline": True,
    "img_alt": True,
    "cut_note": "`<!--cut-->` does not affect the article page — it marks where the "
                "channel announcement stops teasing",
}
VK = {
    "id": "vk",
    "h": {1: "h3", 2: "h3", 3: "h4", 4: None, 5: None, 6: None},
    "inline": {"strong": "b", "em": "i", "del": "s", "u": None,
               "mark": "b", "code": None, "link": True},
    "code_block": "quote-nbsp", "table": "list", "image": "placeholder",
    "iframe": False, "callout": "quote", "hr": "<p>* * *</p>",
    "quote": "blockquote", "list_inline": True,
    "cut_note": "VK articles have no fold — `<!--cut-->` ignored (the teaser lives in the "
                "wall post that links to the article)",
}
DZEN = {
    "id": "dzen",
    "h": {1: "h2", 2: "h2", 3: "h3", 4: "h4", 5: None, 6: None},
    "inline": {"strong": "b", "em": "i", "del": "s", "u": "u",
               "mark": "b", "code": None, "link": True},
    "code_block": "quote-nbsp", "table": "list", "image": "figure",
    "iframe": True, "callout": "quote", "hr": "<p>* * *</p>",
    "quote": "blockquote", "list_inline": False, "img_alt": True,
    "cut_note": "Dzen has no fold — `<!--cut-->` ignored (the feed snippet comes from the "
                "first paragraph)",
}


class HtmlRenderer:
    def __init__(self, profile, doc):
        self.p = profile
        self.doc = doc
        self.lang = doc["lang"]
        self.notes = []
        self.images = []
        self.fn_order = []

    def note(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)

    # -- inline ---------------------------------------------------------
    def inline(self, tokens, strip_format=False):
        cfg = self.p["inline"]
        out = []
        for tok in tokens:
            k = tok["t"]
            if k == "text":
                out.append(esc(tok["v"]))
            elif k == "br":
                out.append("<br>")
            elif k == "code":
                tag = cfg["code"]
                if tag and not strip_format:
                    out.append("<%s>%s</%s>" % (tag, esc(tok["v"]), tag))
                else:
                    if not tag:
                        self.note("inline `code` has no equivalent — rendered as plain text")
                    out.append(esc(tok["v"]))
            elif k == "link":
                inner = self.inline(tok["kids"], strip_format)
                if cfg["link"]:
                    out.append('<a href="%s">%s</a>' % (esc(tok["url"]), inner or esc(tok["url"])))
                else:
                    out.append("%s (%s)" % (inner, esc(tok["url"])))
            elif k == "fnref":
                if tok["id"] not in self.fn_order:
                    self.fn_order.append(tok["id"])
                out.append("[%d]" % (self.fn_order.index(tok["id"]) + 1))
            elif k == "img":
                out.append(esc(tok["alt"] or tok["src"]))
            else:
                tag = cfg.get(k)
                inner = self.inline(tok.get("kids", []), strip_format)
                if tag and not strip_format:
                    out.append("<%s>%s</%s>" % (tag, inner, tag))
                else:
                    if not tag and k in ("u", "mark"):
                        self.note("`%s` has no equivalent — emphasis dropped to plain text" % k)
                    out.append(inner)
        return "".join(out)

    # -- blocks ---------------------------------------------------------
    def blocks(self, blocks):
        return "\n".join(x for x in (self.block(b) for b in blocks) if x)

    def block(self, b):
        kind = b["type"]
        fn = getattr(self, "_" + kind, None)
        return fn(b) if fn else ""

    def _heading(self, b):
        tag = self.p["h"].get(b["level"])
        text = self.inline(b["inline"])
        if tag:
            return "<%s>%s</%s>" % (tag, text, tag)
        self.note("heading level %d is not available — rendered as a bold paragraph"
                  % b["level"])
        strong = self.p["inline"]["strong"]
        return "<p><%s>%s</%s></p>" % (strong, text, strong)

    def _para(self, b):
        return "<p>%s</p>" % self.inline(b["inline"])

    def _hr(self, b):
        return self.p["hr"]

    def _cut(self, b):
        self.note(self.p.get("cut_note", "`<!--cut-->` ignored (platform has no fold)"))
        return ""

    def _quote(self, b):
        inner = self.blocks(b["blocks"])
        if self.p["quote"] == "blockquote":
            return "<blockquote>%s</blockquote>" % self._flatten(inner)
        return inner

    def _flatten(self, html_str):
        """telegra.ph/VK dislike <p> inside <blockquote>: fold to <br>-joined text."""
        parts = re.findall(r"<p>(.*?)</p>", html_str, re.S)
        if parts:
            return "<br>".join(parts)
        return html_str

    def _callout(self, b):
        label = t(self.lang, b["kind"]) if b["kind"] in L10N["en"] else b["kind"].title()
        title = b["title"] or label
        strong = self.p["inline"]["strong"]
        head = "<%s>%s</%s>" % (strong, esc(title), strong)
        rich = any(ib["type"] not in ("para",) for ib in b["blocks"])
        if self.p["callout"] == "aside":
            return "<aside>%s<br>%s</aside>" % (head, self._flatten(self.blocks(b["blocks"])))
        if rich:
            # VK/Dzen quotes do not survive lists or images inside them.
            self.note("a callout with a list/image inside cannot live in a quote — "
                      "rendered as a bold lead-in plus normal blocks")
            return "<p>%s</p>\n%s" % (head, self.blocks(b["blocks"]))
        return "<blockquote>%s<br>%s</blockquote>" % (
            head, self._flatten(self.blocks(b["blocks"])))

    def _container(self, b):
        kind = b["kind"]
        if kind == "tldr":
            return self._callout({"kind": "TLDR", "title": b["title"] or t(self.lang, "tldr"),
                                  "blocks": b["blocks"]})
        if kind in ("spoiler", "details"):
            self.note("spoiler/details is not supported — content shown inline under its title")
            return self._callout({"kind": "SPOILER",
                                  "title": b["title"] or t(self.lang, "spoiler"),
                                  "blocks": b["blocks"]})
        return self.blocks(b["blocks"])

    def _code(self, b):
        if self.p["code_block"] == "pre":
            return "<pre>%s</pre>" % esc(b["text"])
        self.note("code blocks are not supported — rendered as a quote with "
                  "non-breaking-space indentation (check indentation after pasting)")
        lines = []
        for line in b["text"].split("\n"):
            stripped = line.lstrip(" \t")
            pad = len(line) - len(stripped)
            lines.append(NBSP * pad + esc(stripped))
        head = ("<b>%s</b><br>" % esc(b["lang"])) if b["lang"] else ""
        return "<blockquote>%s%s</blockquote>" % (head, "<br>".join(lines))

    def _list(self, b, depth=0):
        tag = "ol" if b["ordered"] else "ul"
        out = ["<%s>" % tag]
        for item in b["items"]:
            body = self.inline(item["inline"], strip_format=not self.p["list_inline"])
            if not self.p["list_inline"]:
                self.note("inline formatting inside lists is not rendered — kept as plain text")
            kids = "".join(self._list(c, depth + 1) for c in item["children"])
            out.append("<li>%s%s</li>" % (body, kids))
        out.append("</%s>" % tag)
        return "".join(out)

    def _image(self, b):
        cap = b["caption"] or b["alt"]
        self.images.append({"src": b["src"], "caption": cap})
        if self.p["image"] == "figure":
            fc = "<figcaption>%s</figcaption>" % esc(cap) if cap else ""
            alt = ' alt="%s"' % esc(b["alt"]) if (b["alt"] and self.p.get("img_alt")) else ""
            return '<figure><img src="%s"%s>%s</figure>' % (esc(b["src"]), alt, fc)
        self.note("images cannot be pasted by URL — upload them in the editor "
                  "in the order listed below")
        n = len(self.images)
        label = "[%s %d] %s" % (t(self.lang, "img_todo"), n, cap or b["src"])
        return "<p><b>%s</b></p>" % esc(label)

    def _embed(self, b):
        if self.p["iframe"]:
            return '<figure><iframe src="%s"></iframe></figure>' % esc(b["url"])
        self.note("embeds cannot be pasted — add the %s block in the editor" % b["kind"])
        return '<p><a href="%s">%s</a></p>' % (esc(b["url"]), esc(b["url"]))

    def _table(self, b):
        mode = self.p["table"]
        if mode == "table":
            head = "".join("<th>%s</th>" % self.inline(c) for c in b["head"])
            rows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % self.inline(c)
                                                   for c in r) for r in b["rows"])
            return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (head, rows)
        if mode == "pre":
            self.note("tables are not supported — rendered as a monospaced block")
            return "<pre>%s</pre>" % esc(ascii_table(b))
        self.note("tables are not supported — flattened into a list of "
                  "«column: value» lines")
        heads = [plain(c) for c in b["head"]]
        out = ["<ul>"]
        for row in b["rows"]:
            cells = [plain(c) for c in row]
            first = cells[0] if cells else ""
            rest = "; ".join("%s: %s" % (h, v)
                             for h, v in zip(heads[1:], cells[1:]) if v)
            out.append("<li>%s</li>" % esc(("%s — %s" % (first, rest)) if rest else first))
        out.append("</ul>")
        return "".join(out)

    def footnotes_html(self, preceded_by_rule=False):
        if not self.fn_order:
            return ""
        strong = self.p["inline"]["strong"]
        items = []
        for fid in self.fn_order:
            items.append("<li>%s</li>" % self.inline(self.doc["footnotes"].get(fid, [])))
        rule = "" if preceded_by_rule else self.p["hr"] + "\n"
        return "%s<p><%s>%s</%s></p>\n<ol>%s</ol>" % (
            rule, strong, esc(t(self.lang, "notes")), strong, "".join(items))


def ascii_table(b):
    heads = [plain(c) for c in b["head"]]
    rows = [[plain(c) for c in r] for r in b["rows"]]
    ncol = max([len(heads)] + [len(r) for r in rows]) if rows else len(heads)
    heads += [""] * (ncol - len(heads))
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    widths = [max(len(heads[i]), *(len(r[i]) for r in rows)) if rows else len(heads[i])
              for i in range(ncol)]
    def line(cells):
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)).rstrip()
    out = [line(heads), "  ".join("-" * w for w in widths)]
    out += [line(r) for r in rows]
    return "\n".join(out)


# --------------------------------------------------------------------------
# Habr Flavored Markdown renderer
# --------------------------------------------------------------------------


class HabrRenderer:
    """Habr: Markdown with h1-h3 only, native code fences, <spoiler>, <anchor>."""

    def __init__(self, doc):
        self.doc = doc
        self.lang = doc["lang"]
        self.notes = []
        self.fn_order = []

    def note(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)

    def inline(self, tokens):
        out = []
        for tok in tokens:
            k = tok["t"]
            if k == "text":
                out.append(tok["v"])
            elif k == "br":
                out.append("  \n")
            elif k == "code":
                out.append("`%s`" % tok["v"])
            elif k == "link":
                out.append("[%s](%s)" % (self.inline(tok["kids"]), tok["url"]))
            elif k == "img":
                out.append("![%s](%s)" % (tok["alt"], tok["src"]))
            elif k == "fnref":
                if tok["id"] not in self.fn_order:
                    self.fn_order.append(tok["id"])
                out.append("<sup>[%d](#note-%d)</sup>"
                           % (self.fn_order.index(tok["id"]) + 1,
                              self.fn_order.index(tok["id"]) + 1))
            elif k == "strong":
                out.append("**%s**" % self.inline(tok["kids"]))
            elif k == "em":
                out.append("*%s*" % self.inline(tok["kids"]))
            elif k == "del":
                out.append("~~%s~~" % self.inline(tok["kids"]))
            elif k == "u":
                out.append("<u>%s</u>" % self.inline(tok["kids"]))
            elif k == "mark":
                self.note("`==highlight==` has no Habr equivalent — rendered as bold")
                out.append("**%s**" % self.inline(tok["kids"]))
        return "".join(out)

    def blocks(self, blocks, depth=0):
        out = []
        for b in blocks:
            out.append(self.block(b, depth))
        return "\n\n".join(x for x in out if x)

    def block(self, b, depth=0):
        k = b["type"]
        if k == "heading":
            lvl = min(b["level"], 3)
            if b["level"] > 3:
                self.note("Habr supports h1-h3 only — deeper headings became bold paragraphs")
                return "**%s**" % self.inline(b["inline"])
            return "#" * lvl + " " + self.inline(b["inline"])
        if k == "para":
            return self.inline(b["inline"])
        if k == "hr":
            return "---"
        if k == "cut":
            return "<cut/>" if self.doc["meta"].get("habr_cut") in ("true", "yes", "1") else ""
        if k == "quote":
            body = self.blocks(b["blocks"])
            return "\n".join("> " + ln for ln in body.split("\n"))
        if k == "callout":
            label = t(self.lang, b["kind"]) if b["kind"] in L10N["en"] else b["kind"].title()
            title = b["title"] or label
            self.note("callouts have no native form — rendered as a quote with a bold label")
            if any(ib["type"] != "para" for ib in b["blocks"]):
                self.note("a callout holding a list/image cannot be quoted on Habr — "
                          "rendered as a bold lead-in plus normal blocks")
                return "**%s**\n\n%s" % (title, self.blocks(b["blocks"]))
            body = self.blocks(b["blocks"])
            lines = ["**%s.** %s" % (title, body.split("\n")[0])] + body.split("\n")[1:]
            return "\n".join("> " + ln for ln in lines)
        if k == "container":
            if b["kind"] in ("spoiler", "details"):
                return "<spoiler title=\"%s\">\n\n%s\n\n</spoiler>" % (
                    (b["title"] or t(self.lang, "spoiler")).replace('"', "'"),
                    self.blocks(b["blocks"]))
            if b["kind"] == "tldr":
                # Habr quotes cannot hold lists — a bold lead-in plus normal blocks.
                return "**%s**\n\n%s" % (b["title"] or t(self.lang, "tldr"),
                                         self.blocks(b["blocks"]))
            return self.blocks(b["blocks"])
        if k == "code":
            fence = "```"
            while fence in b["text"]:
                fence += "`"
            return "%s%s\n%s\n%s" % (fence, b["lang"], b["text"], fence)
        if k == "list":
            return self.render_list(b, depth)
        if k == "image":
            cap = b["caption"] or b["alt"]
            return "![%s](%s%s)" % (b["alt"], b["src"],
                                    ' "%s"' % cap.replace('"', "'") if cap else "")
        if k == "embed":
            return "<oembed>%s</oembed>" % b["url"]
        if k == "table":
            return self.render_table(b)
        return ""

    def render_list(self, b, depth):
        out = []
        for idx, item in enumerate(b["items"], 1):
            marker = "%d." % idx if b["ordered"] else "-"
            out.append("  " * depth + "%s %s" % (marker, self.inline(item["inline"])))
            for child in item["children"]:
                out.append(self.render_list(child, depth + 1))
        return "\n".join(out)

    def render_table(self, b):
        heads = [self.inline(c) for c in b["head"]]
        aligns = b.get("align") or ["left"] * len(heads)
        sep = []
        for a in (aligns + ["left"] * len(heads))[:len(heads)]:
            sep.append(":---:" if a == "center" else "---:" if a == "right" else "---")
        out = ["| " + " | ".join(heads) + " |", "| " + " | ".join(sep) + " |"]
        for r in b["rows"]:
            cells = [self.inline(c) for c in r]
            cells += [""] * (len(heads) - len(cells))
            out.append("| " + " | ".join(cells[:len(heads)]) + " |")
        return "\n".join(out)

    def footnotes_md(self):
        if not self.fn_order:
            return ""
        out = ["### %s" % t(self.lang, "notes"), ""]
        for i, fid in enumerate(self.fn_order, 1):
            out.append("<anchor>note-%d</anchor>%d. %s"
                       % (i, i, self.inline(self.doc["footnotes"].get(fid, []))))
        return "\n".join(out)


# --------------------------------------------------------------------------
# Telegram channel post
# --------------------------------------------------------------------------

TG_INLINE = {"strong": "b", "em": "i", "del": "s", "u": "u",
             "mark": "b", "code": "code", "link": True}


def tg_inline(tokens):
    out = []
    for tok in tokens:
        k = tok["t"]
        if k == "text":
            out.append(esc(tok["v"]))
        elif k == "br":
            out.append("\n")
        elif k == "code":
            out.append("<code>%s</code>" % esc(tok["v"]))
        elif k == "link":
            out.append('<a href="%s">%s</a>' % (esc(tok["url"]), tg_inline(tok["kids"])))
        elif k == "fnref":
            continue
        elif k == "img":
            out.append(esc(tok["alt"]))
        else:
            tag = TG_INLINE.get(k)
            inner = tg_inline(tok.get("kids", []))
            out.append("<%s>%s</%s>" % (tag, inner, tag) if tag else inner)
    return "".join(out)


def build_tg_post(doc, iv_url):
    lang, meta = doc["lang"], doc["meta"]
    parts = ["<b>%s</b>" % esc(doc["title"])]
    lede = meta.get("lede")
    if not lede:
        # Everything before <!--cut--> is the teaser; fall back to the first paragraph.
        teaser = []
        for b in doc["blocks"]:
            if b["type"] == "cut":
                break
            if b["type"] == "para":
                teaser.append(plain(b["inline"]))
        lede = "\n\n".join(teaser[:2]) if teaser else ""
    if lede:
        parts.append(tg_inline(parse_inline(str(lede))))

    bullets = []
    for b in doc["blocks"]:
        if b["type"] == "container" and b["kind"] == "tldr":
            for ib in b["blocks"]:
                if ib["type"] == "list":
                    bullets = [plain(it["inline"]) for it in ib["items"]]
                elif ib["type"] == "para" and not bullets:
                    bullets.append(plain(ib["inline"]))
            break
    if not bullets:
        bullets = [plain(b["inline"]) for b in doc["blocks"]
                   if b["type"] == "heading" and b["level"] == 2][:5]
    if bullets:
        parts.append("\n".join("• " + esc(x) for x in bullets[:5]))

    if iv_url:
        parts.append('<a href="%s">%s →</a>' % (esc(iv_url), esc(t(lang, "read_full"))))
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(",") if x.strip()]
    if tags:
        parts.append(" ".join("#" + re.sub(r"[^\w]+", "_", x, flags=re.U) for x in tags))

    post = "\n\n".join(p for p in parts if p)
    truncated = False
    while len(post) > MAX_TG_POST and len(parts) > 2:
        parts.pop(-2)
        post = "\n\n".join(p for p in parts if p)
        truncated = True
    return post, truncated


# --------------------------------------------------------------------------
# Page wrappers
# --------------------------------------------------------------------------


def iv_page(doc, body, canonical):
    meta = doc["meta"]
    author = meta.get("author", "")
    published = meta.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    head = [
        '<!doctype html>',
        '<html lang="%s">' % doc["lang"],
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>%s</title>' % esc(doc["title"]),
        '<meta property="og:type" content="article">',
        '<meta property="og:title" content="%s">' % esc(doc["title"]),
        '<meta property="og:description" content="%s">' % esc(str(meta.get("lede", ""))),
    ]
    if meta.get("cover"):
        head.append('<meta property="og:image" content="%s">' % esc(str(meta["cover"])))
    if canonical:
        head.append('<link rel="canonical" href="%s">' % esc(canonical))
    head += [
        '</head>',
        '<body>',
        '<article>',
        '<h1>%s</h1>' % esc(doc["title"]),
    ]
    if meta.get("lede"):
        head.append('<p class="lede"><strong>%s</strong></p>' % esc(str(meta["lede"])))
    byline = []
    if author:
        byline.append('<address>%s</address>' % esc(str(author)))
    byline.append('<time datetime="%s">%s</time>' % (esc(published), esc(published)))
    head.append("<p>%s</p>" % "".join(byline))
    return "\n".join(head) + "\n" + body + "\n</article>\n</body>\n</html>\n"


def dzen_rss(doc, body, canonical, slug):
    meta = doc["meta"]
    pub = meta.get("date") or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    guid = canonical or ("urn:post:" + slug)
    cats = meta.get("tags") or []
    if isinstance(cats, str):
        cats = [x.strip() for x in cats.split(",") if x.strip()]
    cat_xml = "".join("\n      <category>%s</category>" % esc(c) for c in cats)
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>%s</title>
    <link>%s</link>
    <description>%s</description>
    <language>%s</language>
    <item>
      <title>%s</title>
      <link>%s</link>
      <guid isPermaLink="false">%s</guid>
      <pubDate>%s</pubDate>
      <author>%s</author>
      <description>%s</description>%s
      <content:encoded><![CDATA[
%s
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""" % (esc(str(meta.get("channel", meta.get("author", "Channel")))),
       esc(canonical or "https://example.com/"),
       esc(str(meta.get("lede", doc["title"]))),
       doc["lang"], esc(doc["title"]), esc(canonical or "https://example.com/" + slug),
       esc(guid), esc(str(pub)), esc(str(meta.get("author", ""))),
       esc(str(meta.get("lede", ""))), cat_xml, body)


# --------------------------------------------------------------------------
# Slug
# --------------------------------------------------------------------------

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya",
}


def slugify(text):
    text = text.lower()
    text = "".join(TRANSLIT.get(ch, ch) for ch in text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text or "post")[:60]


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

ALL_PLATFORMS = ["telegram", "vk", "dzen", "habr"]


def render_html_target(profile, doc):
    r = HtmlRenderer(profile, doc)
    body = r.blocks(doc["blocks"])
    fn = r.footnotes_html(preceded_by_rule=body.rstrip().endswith(profile["hr"]))
    if fn:
        body += "\n" + fn
    return body, r


def build(path, outdir, platforms, slug=None, iv_url=None):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    doc = parse_document(raw)
    meta = doc["meta"]
    slug = slug or meta.get("slug") or slugify(doc["title"]) or \
        os.path.splitext(os.path.basename(path))[0]
    canonical = meta.get("canonical") or ""
    iv_url = iv_url or meta.get("iv_url") or canonical
    os.makedirs(outdir, exist_ok=True)
    written, report = [], []

    def write(name, content):
        p = os.path.join(outdir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.rstrip() + "\n")
        written.append(p)

    if "telegram" in platforms:
        body, r = render_html_target(TELEGRAPH, doc)
        write("%s.telegram-iv.html" % slug, body)
        ivbody, r2 = render_html_target(IVPAGE, doc)
        write("%s.iv-page.html" % slug, iv_page(doc, ivbody, canonical))
        post, truncated = build_tg_post(doc, iv_url)
        write("%s.telegram-post.html" % slug, post)
        notes = list(r.notes)
        if truncated:
            notes.append("the announcement exceeded %d characters — middle blocks were dropped"
                         % MAX_TG_POST)
        if not iv_url:
            notes.append("no `iv_url`/`canonical` in front matter — the announcement has no "
                         "“read in full” link yet")
        if any(b["type"] == "image" for b in doc["blocks"]):
            notes.append("telegra.ph renders reliably only for images hosted on Telegram — "
                         "run scripts/telegraph_publish.py and check every image")
        report.append(("Telegram", "%s.telegram-iv.html / %s.iv-page.html / "
                       "%s.telegram-post.html (%d chars)" % (slug, slug, slug, len(post)),
                       notes))

    if "vk" in platforms:
        body, r = render_html_target(VK, doc)
        write("%s.vk.html" % slug, body)
        notes = list(r.notes)
        if r.images:
            notes.append("upload %d image(s) in the editor, in this order: %s"
                         % (len(r.images),
                            "; ".join("%d) %s" % (i, im["src"])
                                      for i, im in enumerate(r.images, 1))))
        report.append(("VK", "%s.vk.html" % slug, notes))

    if "dzen" in platforms:
        body, r = render_html_target(DZEN, doc)
        write("%s.dzen.html" % slug, body)
        write("%s.dzen.rss.xml" % slug, dzen_rss(doc, body, canonical, slug))
        notes = list(r.notes)
        if r.images:
            notes.append("Dzen wants images at least 700 px wide; the RSS item uses the "
                         "source URLs, the editor needs manual upload")
        report.append(("Dzen", "%s.dzen.html + %s.dzen.rss.xml" % (slug, slug), notes))

    if "habr" in platforms:
        h = HabrRenderer(doc)
        body = h.blocks(doc["blocks"])
        fn = h.footnotes_md()
        if fn:
            body += "\n\n" + fn
        write("%s.habr.md" % slug, "# %s\n\n%s" % (doc["title"], body))
        notes = list(h.notes)
        notes.append("paste into the editor in Markdown mode; the preview text is set on "
                     "the second screen, not with <cut/>")
        report.append(("Habr", "%s.habr.md" % slug, notes))

    lines = ["# Build report — %s" % doc["title"], "",
             "Source: `%s`  ·  lang: `%s`  ·  slug: `%s`" % (path, doc["lang"], slug), ""]
    for name, files, notes in report:
        lines.append("## %s" % name)
        lines.append("")
        lines.append("Files: `%s`" % files)
        lines.append("")
        if notes:
            lines.append("What changed / what you must do by hand:")
            lines += ["- %s" % n for n in notes]
        else:
            lines.append("Nothing was degraded.")
        lines.append("")
    write("%s.report.md" % slug, "\n".join(lines))

    for p in written:
        print("✓ %s" % p)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="canonical Markdown file")
    ap.add_argument("-o", "--outdir", default="out")
    ap.add_argument("-p", "--platforms", default="all",
                    help="comma-separated: telegram,vk,dzen,habr (default all)")
    ap.add_argument("--slug")
    ap.add_argument("--iv-url", help="published Instant View / canonical URL for the "
                                     "“read in full” link")
    args = ap.parse_args()

    if not os.path.isfile(args.source):
        print("✗ no such file: %s" % args.source, file=sys.stderr)
        return 1
    if args.platforms.strip().lower() in ("all", "*"):
        platforms = ALL_PLATFORMS
    else:
        platforms = [x.strip().lower() for x in args.platforms.split(",") if x.strip()]
        bad = [x for x in platforms if x not in ALL_PLATFORMS]
        if bad:
            print("✗ unknown platform(s): %s" % ", ".join(bad), file=sys.stderr)
            return 1
    return build(args.source, args.outdir, platforms, args.slug, args.iv_url)


if __name__ == "__main__":
    sys.exit(main())
