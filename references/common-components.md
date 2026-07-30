# Component library — source syntax and what it becomes

This is the equivalent of a theme's component library, except that the
"components" cannot carry colour, spacing or type. They carry *semantics*, and
each platform renders them with whatever it has. Write the source
using only what is documented here — anything else is guesswork at build time.

Every example below is real input for `scripts/build_targets.py`.

---

## 1. Front matter

```markdown
---
title: The title as readers see it
lang: ru                      # ru | en — typography + UI labels
lede: One sentence that states the payoff. Under 300 characters.
author: {{author}}
tags: [tag, tag, tag]
slug: latin-slug              # file names; auto-transliterated if absent
canonical: https://…          # permanent home of the article
iv_url: https://telegra.ph/…  # set after publishing, for the "read in full" link
date: 2026-07-30
channel: Channel name         # used in the Dzen RSS envelope
habr_cut: false               # legacy <cut/>; leave off
---
```

`title`, `lang` and `lede` are the three that change the output everywhere else.
`source_lint.py` complains when they are missing, and it is right to.

---

## 2. Structure

### Headings

```markdown
## Section that says something
### Subsection
```

`#` is the article title and is normally taken from front matter. **Do not go
deeper than `###`** — telegra.ph has two body levels, Habr three, Dzen four, VK
two. `####` degrades to a bold paragraph everywhere and the outline flattens.

### TL;DR

```markdown
:::tldr
- The first conclusion, stated as a conclusion.
- The second.
- The third.
:::
```

| Platform | Renders as |
|---|---|
| telegra.ph | `<aside>` with a bold label and the list |
| Telegram post | the `•` bullets of the announcement |
| VK / Dzen | bold lead-in paragraph + the list |
| Habr | `**Коротко**` / `**TL;DR**` + the list |

Three bullets. They must be conclusions, not a table of contents.

### Teaser boundary

```markdown
<!--cut-->
```

Everything above it is what the Telegram announcement may show. Place it after
the hook and before the first `##`. Ignored by VK, Dzen and Habr (Habr sets its
preview text on a separate screen).

### Divider

```markdown
---
```

`<hr>` on telegra.ph, a `* * *` paragraph on VK and Dzen, `---` on Habr.

---

## 3. Emphasis

| Source | Meaning | telegra.ph | TG post | VK | Dzen | Habr |
|---|---|---|---|---|---|---|
| `**bold**` | the anchor of a section | `<strong>` | `<b>` | `<b>` | `<b>` | `**` |
| `*italic*` | a term, a title, a voice shift | `<em>` | `<i>` | `<i>` | `<i>` | `*` |
| `~~strike~~` | a correction | `<s>` | `<s>` | `<s>` | `<s>` | `~~` |
| `==highlight==` | there is no highlight anywhere | `<strong>` | `<b>` | `<b>` | `<b>` | `**` |
| `<u>underline</u>` | avoid — reads as a link | `<u>` | `<u>` | dropped | `<u>` | `<u>` |
| `` `code` `` | identifiers, flags, paths | `<code>` | `<code>` | plain | plain | `` ` `` |

**Budget: five bold anchors in the whole article, at most one per section.**
Bold is the only emphasis all five renderers keep, so spending it everywhere
spends it nowhere. `source_lint.py` counts and warns.

`==highlight==` exists so the source can record *intent* ("this is the sentence
that matters") even though every platform flattens it to bold.

---

## 4. Containers

### Quote

```markdown
> A sentence worth setting apart, or a real quotation.
```

`<blockquote>` everywhere. Do not nest — Habr forbids it and the rest render it
inconsistently.

### Callout

```markdown
> [!NOTE] Optional title
> The aside, the caveat, the "note that…" sentence that was cluttering
> the paragraph above.
```

Kinds: `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`, `EXAMPLE`. The label is
localised from `lang:` when no title is given.

| Platform | Renders as |
|---|---|
| telegra.ph | `<aside>` with a bold label — the closest native form |
| VK / Dzen | quote with a bold label; a bold lead-in + blocks if it holds a list |
| Habr | `> **Label.** …` |
| TG post | not carried |

Callouts are the main way to create visible structure without CSS. Use them for
asides, prerequisites, warnings and worked examples — not for ordinary text.

### Spoiler / details

```markdown
:::spoiler What if you have no website
Long logs, configs, derivations, the boring middle of a proof.
:::
```

Native `<spoiler title="">` on Habr. Everywhere else the title is shown as a
bold lead-in and the content stays visible — so **never hide anything essential
in a spoiler**; assume it is always open.

---

## 5. Lists

```markdown
- item
- item
  - nested item

1. step
2. step
```

- **Dzen strips formatting inside list items.** Put the emphasis in the sentence
  that introduces the list, not in the bullets.
- Two-level nesting is the practical maximum.
- A one-item list is a paragraph; the linter says so.

---

## 6. Code

````markdown
```bash
python3 scripts/build_targets.py article.md -o out
```
````

**Always name the language** — Habr highlights it, and elsewhere the label
becomes the only signal that this is code.

| Platform | Result |
|---|---|
| telegra.ph | `<pre>`, monospaced, no highlighting |
| TG post | `<pre>` |
| Habr | fenced block with highlighting |
| VK / Dzen | quote block, indentation rebuilt with non-breaking spaces |

Consequence: **anything longer than a few lines does not belong in the VK or
Dzen version.** Either the piece is not for those platforms, or the code goes in
as a screenshot with a link to the real source. Decide in the source, not after
the paste.

---

## 7. Images and media

```markdown
![alt text](https://example.com/pipeline.png "Caption shown under the image")
```

| Platform | Result |
|---|---|
| telegra.ph | `<figure><img src><figcaption>` — **no `alt` attribute**, it is not in the whitelist |
| Dzen | `<figure><img alt><figcaption>`; the image must be ≥ 700 px wide |
| Habr | `![alt](url "caption")` |
| VK | a numbered placeholder plus an ordered upload list in the report |

Always give a caption or alt text: on VK it is the only thing telling the author
which upload goes where.

### Embeds

```markdown
@[youtube](https://www.youtube.com/watch?v=…)
```

`<figure><iframe src>` on telegra.ph and Dzen, `<oembed>` on Habr, a link
paragraph on VK (add the block through the editor's **+** menu).

### Placeholder for material that does not exist yet

```markdown
> [!NOTE] Материал
> Здесь будет запись экрана: сборка статьи в четыре артефакта.
```

There is no dashed-box component to reach for — a callout is the honest way to
mark "to be added", and it survives everywhere.

---

## 8. Tables

```markdown
| Platform | Code | Tables |
| --- | --- | --- |
| Habr | yes | yes |
| VK | no | no |
```

**Only Habr has tables.** telegra.ph renders a monospaced ASCII block; VK and
Dzen flatten each row into `first cell — column: value; column: value`.

So: keep tables to **three columns and eight rows** in the source. A six-column
table is unreadable in every degraded form. If the comparison genuinely needs
width, split it into two tables or write it as a list of short paragraphs.

---

## 9. Footnotes

```markdown
Instant View lives on the page, not in the post[^1].

[^1]: Templates are per-domain; telegra.ph is the exception.
```

Rendered as `[1]` in the text plus a **Notes / Примечания** list at the end;
on Habr as `<sup>[1](#note-1)</sup>` with `<anchor>note-1</anchor>`. Dropped
from the Telegram announcement.

Use them for provenance, not for jokes — a footnote no one can click is a
sentence you should have cut.

---

## 10. The sign-off

```markdown
---

Я — {{автор}}, {{одна строка о себе}}. Если материал оказался полезным,
поделитесь им с тем, кому он пригодится.
```

- **Never hard-code a name.** Leave `{{author}}` / `{{bio}}` and tell the user to
  replace them; `source_lint.py` warns while placeholders remain.
- If the source already ends with the author's own sign-off, keep theirs and do
  not add a second one.
- One sign-off, at the end, and never in the middle.

---

## Quick reference

| In the article | Use |
|---|---|
| the article's conclusions up front | `:::tldr` |
| an aside, caveat, prerequisite | `> [!NOTE]` / `> [!WARNING]` |
| a real quotation | `> …` |
| long logs, optional depth | `:::spoiler` (Habr folds it; others show it) |
| a command, config, snippet | fenced block with a language |
| a comparison | table (≤ 3 columns) — or a list if VK/Dzen matter |
| the one point of a section | `**bold**`, once |
| provenance | `[^1]` |
| where the teaser ends | `<!--cut-->` |
