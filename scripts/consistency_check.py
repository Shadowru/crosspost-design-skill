#!/usr/bin/env python3
"""Consistency gate: does the skill still agree with its own reference library?

The failure this catches is the boring one that breaks a skill silently — a
reference file renamed and the link in SKILL.md left dangling, a platform added
to the index but never given a build profile, a trigger phrase dropped from the
description so the skill stops firing.

None of that shows up when you run the pipeline: the build works fine and the
skill simply never activates, or the agent reads a file that no longer exists.

Usage:
    consistency_check.py [--root DIR]

Exit codes: 1 = at least one inconsistency; 0 = clean.
"""

import argparse
import io
import os
import re
import sys

FAIL, WARN = [], []


def fail(msg):
    FAIL.append(msg)


def warn(msg):
    WARN.append(msg)


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def strip_code(text):
    """Drop fenced blocks and inline code — the markdown in there is an example,
    not a link. Without this, `![alt](url "caption")` reads as a broken link."""
    text = re.sub(r"^\s*(`{3,}|~{3,}).*?^\s*\1", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


DESC_LIMIT = 1024          # claude.ai rejects the upload above this
NAME_RX = re.compile(r"^[a-z0-9-]+$")


def check_frontmatter(root):
    """Limits the upload enforces but nothing local warns about."""
    head = read(os.path.join(root, "SKILL.md")).split("---")[1]
    name = re.search(r"^name:\s*(.*)$", head, re.M)
    desc = re.search(r"^description:\s*(.*)$", head, re.M)
    if not name or not NAME_RX.match(name.group(1).strip()):
        fail("SKILL.md `name` must be lowercase letters, digits and hyphens")
    if not desc:
        fail("SKILL.md has no `description` — the skill will never be selected")
        return
    n = len(desc.group(1).strip())
    if n > DESC_LIMIT:
        fail("SKILL.md description is %d characters, claude.ai rejects the upload "
             "above %d — trim it by %d" % (n, DESC_LIMIT, n - DESC_LIMIT))
    elif n > DESC_LIMIT * 0.92:
        warn("SKILL.md description is %d of %d characters — little room left"
             % (n, DESC_LIMIT))


def check_links(root):
    """Every relative markdown link in SKILL.md and references/ resolves."""
    targets = [os.path.join(root, "SKILL.md")]
    ref_dir = os.path.join(root, "references")
    targets += [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))
                if f.endswith(".md")]
    for path in targets:
        base = os.path.dirname(path)
        for m in re.finditer(r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)",
                             strip_code(read(path))):
            link = m.group(1).strip()
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(base, link))):
                fail("%s links to a missing file: %s"
                     % (os.path.relpath(path, root), link))


def check_platform_wiring(root):
    """platform-index.md, the build profiles and the validator agree."""
    index = read(os.path.join(root, "references", "platform-index.md"))
    build = read(os.path.join(root, "scripts", "build_targets.py"))
    valid = read(os.path.join(root, "scripts", "validate_post.py"))

    # Files column of the second table: references/platform-*.md
    listed = set(re.findall(r"\((platform-[\w-]+\.md)\)", index))
    on_disk = {f for f in os.listdir(os.path.join(root, "references"))
               if f.startswith("platform-") and f != "platform-index.md"}
    for missing in sorted(on_disk - listed):
        warn("references/%s exists but platform-index.md never links it" % missing)
    for ghost in sorted(listed - on_disk):
        fail("platform-index.md links references/%s, which does not exist" % ghost)

    # Every validator key named in the index is really defined.
    keys = set(re.findall(r"`([a-z-]+)`", index.split("## Choosing targets")[0]))
    defined = set(re.findall(r'^\s{4}"([a-z-]+)":\s*\{', valid, re.M))
    defined |= {"habr"}                      # handled by check_habr, not RULES
    for key in sorted(k for k in keys if k in
                      {"telegraph", "iv-page", "tg-post", "vk", "dzen", "habr"}):
        if key not in defined:
            fail("platform-index.md names validator key `%s`, "
                 "validate_post.py has no such rule set" % key)

    # Every build profile has a matching validator rule set.
    for profile in re.findall(r'^\s{4}"id":\s*"([a-z-]+)"', build, re.M):
        if profile not in defined:
            fail("build_targets.py emits profile `%s` with no validator rules"
                 % profile)


def check_l10n(root):
    """Both languages carry the same UI keys — a missing one ships in English."""
    build = read(os.path.join(root, "scripts", "build_targets.py"))
    block = build.split("L10N = {", 1)[1].split("\n}", 1)[0]
    marks = [(m.group(1), m.end(), m.start())
             for m in re.finditer(r'"(ru|en)":\s*\{', block)]
    langs = {}
    for i, (lang, start, _) in enumerate(marks):
        end = marks[i + 1][2] if i + 1 < len(marks) else len(block)
        langs[lang] = block[start:end]
    if set(langs) != {"ru", "en"}:
        fail("L10N should define exactly ru and en, found: %s" % sorted(langs))
        return
    keys = {lang: set(re.findall(r'"(\w+)":', body)) for lang, body in langs.items()}
    for missing in sorted(keys["en"] - keys["ru"]):
        fail("L10N key `%s` exists in en but not ru — Russian output falls back "
             "to English" % missing)
    for extra in sorted(keys["ru"] - keys["en"]):
        warn("L10N key `%s` exists in ru but not en" % extra)


def check_triggers(root):
    """Trigger phrases in the eval cases are actually covered by the description."""
    desc = read(os.path.join(root, "SKILL.md")).split("---")[1].lower()
    cases = read(os.path.join(root, "references", "eval-cases.md"))
    section = cases.split("## A. Should trigger")[1].split("## B.")[0]

    # Content words of each case prompt must be findable in the description.
    stop = {"эту", "этот", "для", "под", "и", "в", "на", "не", "вот", "как",
            "this", "the", "for", "and", "of", "a", "an", "out", "it", "me",
            "make", "want", "i", "to", "as", "post", "статью", "текст", "статьи"}
    for row in re.findall(r"^\|\s*(A\d)\s*\|\s*(.+?)\s*\|", section, re.M):
        cid, prompt = row
        words = [w for w in re.findall(r"[\w-]{4,}", prompt.lower())
                 if w not in stop]
        if not words:
            continue
        hit = [w for w in words if w in desc]
        if not hit:
            fail("eval case %s («%s») shares no trigger word with the "
                 "description — the skill may never fire for it" % (cid, prompt[:48]))


def check_scripts_referenced(root):
    """Every script is mentioned somewhere in the docs, and vice versa."""
    docs = "\n".join(read(os.path.join(root, p)) for p in
                     ("SKILL.md", "README.md", "README.en.md"))
    for f in sorted(os.listdir(os.path.join(root, "scripts"))):
        if f.endswith((".py", ".sh")) and f not in docs:
            warn("scripts/%s is not mentioned in SKILL.md or either README" % f)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    for check in (check_frontmatter, check_links, check_platform_wiring, check_l10n,
                  check_triggers, check_scripts_referenced):
        try:
            check(root)
        except Exception as e:                       # a broken check is a finding
            fail("%s crashed: %s" % (check.__name__, e))

    print("• consistency check: %s" % root)
    for m in FAIL:
        print("   ✗ %s" % m)
    for m in WARN:
        print("   ! %s" % m)
    if not FAIL and not WARN:
        print("   ✓ skill, references, build profiles and validators agree")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
