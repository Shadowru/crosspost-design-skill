#!/usr/bin/env python3
"""Word .docx -> Markdown extractor (no third-party dependencies).

The deterministic half of format normalisation: heading styles, bold,
underline, lists, tables and embedded images become Markdown the rest of the
pipeline understands. Recognises English, Russian and generic style names
(Heading 1 / Заголовок 1 / Title / Название).

Usage:
    extract_docx.py article.docx [-o article.md]
    # embedded images are unpacked next to the output, into images/

Exit codes: 0 ok; 1 missing or malformed file.
"""

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

HEADING_NAME = re.compile(r"(?:heading|заголовок|überschrift|titre)\s*([1-6])", re.I)
LIST_NAME = re.compile(r"list|список|abs|puce", re.I)


def load_styles(z):
    """styleId -> heading level."""
    levels = {}
    try:
        root = ET.fromstring(z.read("word/styles.xml"))
    except KeyError:
        return levels
    for st in root.iter(W + "style"):
        sid = st.get(W + "styleId") or ""
        name_el = st.find(W + "name")
        name = (name_el.get(W + "val") if name_el is not None else "") or ""
        m = HEADING_NAME.search(name) or re.fullmatch(r"([1-6])", sid)
        if m:
            levels[sid] = int(m.group(1))
        elif re.fullmatch(r"(title|название|заголовок)", name.strip(), re.I):
            levels[sid] = 1
    return levels


def load_rels(z):
    rels = {}
    try:
        root = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    except KeyError:
        return rels
    for rel in root:
        target = rel.get("Target") or ""
        if "media/" in target:
            rels[rel.get("Id")] = "word/" + target.lstrip("/").replace("../", "")
    return rels


def para_text(p):
    """Runs -> inline Markdown (bold -> **, underline -> <u>, italic -> *)."""
    out = []
    for run in p.iter(W + "r"):
        rpr = run.find(W + "rPr")

        def on(tag):
            if rpr is None:
                return False
            el = rpr.find(W + tag)
            return el is not None and (el.get(W + "val") or "1") not in ("0", "false", "none")

        text = "".join(t.text or "" for t in run.iter(W + "t"))
        if not text:
            continue
        if on("b"):
            text = "**%s**" % text
        if on("i"):
            text = "*%s*" % text
        if on("u"):
            text = "<u>%s</u>" % text
        out.append(text)
    s = "".join(out)
    s = re.sub(r"\*\*\*\*", "", s)          # adjacent bold runs
    return re.sub(r"(?<!\*)\*\*(?!\*)(\s*)\*\*(?!\*)", r"\1", s)


def extract(docx_path, out_md):
    try:
        z = zipfile.ZipFile(docx_path)
        doc = ET.fromstring(z.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError) as e:
        print("✗ not a readable .docx: %s" % e, file=sys.stderr)
        return 1

    heading_of, media_of = load_styles(z), load_rels(z)
    out_dir = os.path.dirname(os.path.abspath(out_md)) or "."
    img_dir = os.path.join(out_dir, "images")
    lines, img_n, tables = [], 0, 0

    body = doc.find(W + "body")
    for el in body:
        if el.tag == W + "tbl":
            rows = []
            for tr in el.findall(W + "tr"):
                cells = ["".join(t.text or "" for t in tc.iter(W + "t"))
                         .strip().replace("|", "\\|") or " "
                         for tc in tr.findall(W + "tc")]
                rows.append("| " + " | ".join(cells) + " |")
            if rows:
                lines.append(rows[0])
                lines.append("|" + "---|" * (rows[0].count("|") - 1))
                lines.extend(rows[1:])
                lines.append("")
                tables += 1
            continue
        if el.tag != W + "p":
            continue

        for blip in el.iter(A + "blip"):
            src = media_of.get(blip.get(R + "embed"))
            if not src:
                continue
            os.makedirs(img_dir, exist_ok=True)
            img_n += 1
            fname = "%02d-%s" % (img_n, os.path.basename(src))
            with open(os.path.join(img_dir, fname), "wb") as f:
                f.write(z.read(src))
            lines.append("![](images/%s)" % fname)
            lines.append("")

        text = para_text(el).strip()
        if not text:
            continue
        ppr = el.find(W + "pPr")
        style_el = ppr.find(W + "pStyle") if ppr is not None else None
        sid = style_el.get(W + "val") if style_el is not None else ""
        level = heading_of.get(sid)
        numbered = ppr is not None and ppr.find(W + "numPr") is not None
        is_list = numbered or bool(LIST_NAME.search(sid or ""))

        if level:
            lines.append("#" * min(level, 6) + " " + re.sub(r"^\*\*(.*)\*\*$", r"\1", text))
        elif is_list:
            lines.append("- " + text)
        else:
            lines.append(text)
        lines.append("")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print("✓ %s -> %s" % (os.path.basename(docx_path), out_md))
    print("  headings %d · list items %d · images %d · tables %d"
          % (sum(1 for l in lines if l.startswith("#")),
             sum(1 for l in lines if l.startswith("- ")), img_n, tables))
    print("  next: add front matter (title/lang/lede), then run source_lint.py")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("-o", "--out", help="output .md path (default: same name)")
    args = ap.parse_args()
    if not os.path.isfile(args.docx):
        print("✗ no such file: %s" % args.docx, file=sys.stderr)
        return 1
    out = args.out or re.sub(r"\.docx$", "", args.docx, flags=re.I) + ".md"
    return extract(args.docx, out)


if __name__ == "__main__":
    sys.exit(main())
