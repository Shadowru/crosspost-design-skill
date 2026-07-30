#!/usr/bin/env python3
"""Russian / English micro-typography linter for canonical Markdown.

The original WeChat skill enforced full-width CJK punctuation. The EN/RU
equivalent is this: proper quotation marks, real dashes, ellipses, no stray
spaces before punctuation, and non-breaking spaces where a line break would
read badly. Platforms preserve all of these characters — they strip CSS, not
Unicode — so this is the one layer of "design" that survives everywhere.

Usage:
    typography_lint.py article.md                 # report only
    typography_lint.py article.md --fix           # rewrite in place
    typography_lint.py article.md --fix -o out.md # write elsewhere
    typography_lint.py article.md --lang ru --nbsp

Language is taken from the `lang:` front-matter key unless --lang is given.
Code fences, inline code, URLs, HTML tags and {{placeholders}} are left alone.

Exit codes: 1 = issues found and not fixed; 0 = clean (or fixed).
"""

import argparse
import io
import re
import sys

NBSP = " "
SHORT_WORDS_RU = ("в", "во", "и", "а", "но", "на", "с", "со", "к", "ко", "о", "об",
                  "от", "до", "из", "за", "по", "у", "не", "ни", "же", "ли", "бы",
                  "для", "как", "что", "это", "при", "под", "над", "без", "чем")
SHORT_WORDS_EN = ("a", "an", "the", "in", "on", "at", "of", "to", "is", "it", "as",
                  "by", "or", "and", "for", "if", "we", "you")

MASK = "\x00%d\x00"
PROTECT = re.compile(
    r"(`[^`]*`)"                       # inline code
    r"|(https?://\S+|www\.\S+)"        # bare URLs
    r"|(\]\([^)]*\))"                  # markdown link targets
    r"|(<[^>]+>)"                      # html tags
    r"|(\{\{[^}]*\}\})"                # {{placeholders}}
)


def mask(line):
    store = []

    def keep(m):
        store.append(m.group(0))
        return MASK % (len(store) - 1)

    return PROTECT.sub(keep, line), store


def unmask(line, store):
    for i, chunk in enumerate(store):
        line = line.replace(MASK % i, chunk)
    return line


# --------------------------------------------------------------------------
# Rules: (name, regex, replacement, explanation)
# --------------------------------------------------------------------------

def rx_rule(name, pattern, repl, why, flags=0):
    rx = re.compile(pattern, flags)
    return (name, lambda s: rx.sub(repl, s), why)


COMMON = [
    rx_rule("ellipsis", r"\.{3,}", "…", "three dots -> …"),
    rx_rule("double-space", r"(?<=\S)  +(?=\S)", " ", "double space -> single"),
    rx_rule("space-before-punct", r"\s+([,.;:!?])(?=\s|$)", r"\1",
            "space before punctuation"),
    rx_rule("missing-space", r"(?<![:\d/])([,;:])(?=[^\s\d)\]:/])", r"\1 ",
            "no space after a comma/colon"),
    rx_rule("number-range", r"(?<=\d)\s?-\s?(?=\d)", "–",
            "hyphen between numbers -> en dash (5–7)"),
    rx_rule("mdash-from-double", r"(?<!-)--(?!-)", "—", "-- -> —"),
]

RU_PAIRS = [("«", "»"), ("„", "“")]
EN_PAIRS = [("“", "”"), ("‘", "’")]


def smart_quotes(text, pairs):
    """Straight " -> nested typographic pairs, decided by the preceding character."""
    out, stack = [], []
    for i, ch in enumerate(text):
        if ch != '"':
            out.append(ch)
            continue
        prev = text[i - 1] if i else ""
        opening = (not prev) or prev.isspace() or prev in "([{-—–…\x00"
        if opening:
            level = min(len(stack), len(pairs) - 1)
            out.append(pairs[level][0])
            stack.append(level)
        else:
            level = stack.pop() if stack else 0
            out.append(pairs[level][1])
    return "".join(out)


RU = [
    ("quotes", lambda s: smart_quotes(s, RU_PAIRS),
     'straight "quotes" -> «ёлочки», nested -> „лапки“'),
    ("dash", lambda s: re.sub(r"(?<=\S)\s+-\s+(?=\S)", " — ", s),
     "hyphen used as a dash -> —"),
    ("hyphen-dash", lambda s: re.sub(r"(?<=\S)\s+–\s+(?=\S)", " — ", s),
     "en dash between words -> em dash (RU uses — )"),
]

_EN_DASH_CTX = r"(?<=[\w»”’)\]])\s+-\s+(?=[\w«“‘(\[])"
EN_EM = ("dash", lambda s: re.sub(_EN_DASH_CTX, "—", s),
         "hyphen used as a dash -> em dash, unspaced (US style)")
EN_EN = ("dash", lambda s: re.sub(_EN_DASH_CTX, " – ", s),
         "hyphen used as a dash -> spaced en dash (UK style)")

EN = [
    ("apostrophe", lambda s: re.sub(r"(?<=\w)'(?=\w)", "’", s),
     "straight apostrophe -> ’"),
    ("quotes", lambda s: smart_quotes(s, EN_PAIRS),
     'straight "quotes" -> “curly”'),
    ("single-quotes",
     lambda s: re.sub(r"(?<![\w’])'([^'\n]+)'(?![\w’])", "‘\\1’", s),
     "straight 'quotes' -> ‘curly’"),
]

WARN_ONLY = [
    ("multi-bang", re.compile(r"[!?]{2,}"), "repeated !/? — one is enough in an article"),
    ("trailing-space", re.compile(r"[ \t]+$"), "trailing whitespace"),
    ("shout", re.compile(r"(?<![\w/])[A-ZА-ЯЁ]{5,}(?![\w/])"),
     "ALL-CAPS word — headings and bold carry emphasis better"),
    ("straight-quote-left", re.compile(r'"'), "unpaired straight quote left over"),
]


def nbsp_rules(lang):
    words = SHORT_WORDS_RU if lang == "ru" else SHORT_WORDS_EN
    alt = "|".join(sorted(words, key=len, reverse=True))
    return [
        rx_rule("nbsp-short-word", r"(?<![\w-])(%s) (?=[\w«“(])" % alt, "\\1" + NBSP,
                "non-breaking space after a short word (it must not end a line)",
                re.I | re.U),
        rx_rule("nbsp-before-dash", r"(?<=\S) (?=—)", NBSP,
                "non-breaking space before an em dash"),
        rx_rule("nbsp-number-unit",
                r"(?<=\d) (?=[%№]|[A-Za-zА-Яа-яЁё]{1,3}(?![\w]))", NBSP,
                "non-breaking space between a number and its unit"),
    ]


def detect_lang(text, override=None):
    if override:
        return override
    m = re.search(r"^lang:\s*([A-Za-z-]+)", text, re.M)
    if m:
        return m.group(1).lower()[:2]
    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    return "ru" if cyr > lat else "en"


def lint(text, lang, dash="em", use_nbsp=False):
    rules = list(COMMON)
    if lang == "ru":
        rules += RU
    else:
        rules += EN + [EN_EM if dash == "em" else EN_EN]
    if use_nbsp:
        rules += nbsp_rules(lang)

    out_lines, findings = [], []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), 1):
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence or re.match(r"^\s{4,}\S", line):
            out_lines.append(line)
            continue

        masked, store = mask(line)
        for name, fn, why in rules:
            new = fn(masked)
            if new != masked:
                findings.append((lineno, name, why, True))
                masked = new
        fixed = unmask(masked, store)

        checked, store2 = mask(fixed)
        for name, rx, why in WARN_ONLY:
            if rx.search(checked):
                findings.append((lineno, name, why, False))
        out_lines.append(fixed)
    return "\n".join(out_lines), findings


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--lang", choices=["ru", "en"])
    ap.add_argument("--dash", choices=["em", "en"], default="em",
                    help="English dash style: unspaced em (default) or spaced en")
    ap.add_argument("--nbsp", action="store_true",
                    help="also bind short words / units with non-breaking spaces")
    ap.add_argument("--fix", action="store_true", help="write the corrected text")
    ap.add_argument("-o", "--out", help="write to this path instead of in place")
    args = ap.parse_args()

    try:
        text = io.open(args.file, encoding="utf-8").read()
    except OSError as e:
        print("✗ %s" % e, file=sys.stderr)
        return 1

    lang = detect_lang(text, args.lang)
    fixed, findings = lint(text, lang, args.dash, args.nbsp)

    fixable = [f for f in findings if f[3]]
    warns = [f for f in findings if not f[3]]

    print("• %s  [lang=%s, dash=%s, nbsp=%s]"
          % (args.file, lang, args.dash, "on" if args.nbsp else "off"))
    seen = set()
    for lineno, name, why, _ in fixable:
        key = (name, why)
        count = sum(1 for f in fixable if f[1] == name)
        if key in seen:
            continue
        seen.add(key)
        print("   ~ %-20s ×%-3d %s (first at line %d)" % (name, count, why, lineno))
    seen = set()
    for lineno, name, why, _ in warns:
        if name in seen:
            continue
        seen.add(name)
        count = sum(1 for f in warns if f[1] == name)
        print("   ! %-20s ×%-3d %s (first at line %d)" % (name, count, why, lineno))

    if not findings:
        print("   ✓ typography is clean")
        return 0

    if args.fix:
        dest = args.out or args.file
        io.open(dest, "w", encoding="utf-8").write(fixed)
        print("   ✓ fixed %d issue(s) -> %s" % (len(fixable), dest))
        if warns:
            print("   ! %d warning(s) need a human decision" % len(warns))
        return 0

    print("   run again with --fix to apply the %d automatic fix(es)" % len(fixable))
    return 1 if fixable else 0


if __name__ == "__main__":
    sys.exit(main())
