---
title: Stop rewriting the same article four times
lang: en
lede: One source, four platforms, no manual re-typing — the setup that gives you back an evening per publication.
author: {{author}}
tags: [publishing, workflow, automation]
slug: one-source-four-targets
canonical: https://example.com/blog/one-source-four-targets
tone: editorial
---

# Stop rewriting the same article four times

:::tldr
- Keep one canonical Markdown source instead of four drafts.
- Each platform’s markup is a whitelist, not a matter of taste.
- Whatever a platform cannot render degrades on purpose, and lands in a report.
:::

An editor running four channels spends more time moving text than writing it. Worse, the time goes into the dullest part: re-adding subheadings, rebuilding lists, re-inserting images.

<!--cut-->

## Why copy-paste fails

Every platform accepts a whitelist of markup, and it is far shorter than people expect. ==Inline CSS survives none of them==, and half the elements you rely on simply vanish on paste.

> The rule is blunt: anything outside the whitelist disappears silently. The editor’s job is to decide on the replacement before publishing, not after.

| Platform | Headings | Code | Tables |
| --- | --- | --- | --- |
| Telegram IV | h3, h4 | yes | no |
| VK | two levels | no | no |
| Dzen | h2–h4 | no | no |
| Habr | h1–h3 | yes | yes |

## What a single source buys you

Canonical Markdown stores **meaning**, not presentation. The builder then decides how that meaning shows up on a given platform.

1. Parse the text into a block tree.
2. Apply each platform’s markup map.
3. Write everything that did not fit into a report.

> [!NOTE] On degradation
> Degrading is not losing. It is choosing the substitute deliberately: a table becomes a list, a code block becomes a quote with non-breaking-space indentation.

Here is the whole build command:

```bash
python3 scripts/build_targets.py article.md -o out -p telegram,vk,dzen,habr
```

![Pipeline diagram: one source, four outputs](https://example.com/img/pipeline.png "One pass, four ready-to-publish artifacts")

### Telegram in particular

Instant View lives on a page, not in a post[^1]. So Telegram gets two artifacts: the page that Instant View renders, and a short announcement that links to it.

:::spoiler What if you have no website
Publish the page to telegra.ph — Instant View works there out of the box, with no template of your own.
:::

## What stays human

No script will write the lede, choose the three claims worth leading with, or notice that a paragraph is dead weight. Everything else is mechanics, and mechanics should not cost you an evening.

[^1]: Instant View is generated from a per-domain template of rules; telegra.ph is the exception, where the template already exists.

---

I am {{author}}, {{one line about yourself}}. If this was useful, pass it to whoever else is running the same four channels.
