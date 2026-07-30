---
name: crosspost-design
description: Article formatting engine for Telegram Instant View, VK, Dzen and Habr, in English and Russian. Turns one canonical Markdown source into each platform's whitelisted markup — telegra.ph/IV page plus channel announcement, paste-safe VK article, Dzen content:encoded and RSS item, Habr Flavored Markdown — with automatic section rhythm, TL;DR block, callouts, footnotes, EN/RU micro-typography (« », — , …, non-breaking spaces) and a report of everything each platform degrades. Accepts Markdown / Word (.docx) / PDF / plain text (non-Markdown is normalised first). Triggers when the user mentions Telegram Instant View / telegra.ph, VK articles, Дзен, Habr/Хабр, "cross-posting", "оформить статью", "вёрстка поста", "разложить по площадкам", "adapt this post for", or wants one text published on several Russian/English platforms. Not for building web pages, landing pages or slide decks (use a frontend or PPT skill).
---

# Multi-platform post design — Telegram IV · VK · Dzen · Habr

Turn one article into four published artifacts without rewriting it four times.

**The central fact these platforms share: none of them lets you style anything.**
Telegram, VK, Dzen and Habr each accept a short whitelist of tags and delete the
rest — inline CSS, classes, custom fonts, colours, all gone. So the design work
is not decoration. It is *structure*: section rhythm, one clear anchor per
section, a lede that survives as a feed snippet, and typography (« », — , …,
non-breaking spaces) that platforms preserve because it is Unicode, not style.

The pipeline is: **canonical Markdown → deterministic build → validation.**
You do the editorial work in the canonical source. Scripts do the mechanical
degradation and tell you exactly what each platform lost.

## Workflow

### 0. Input and normalisation

The user may bring Markdown or a `.md` path (go straight to step 1), `.docx`,
`.pdf`, `.txt`, plain unstructured text, or pasted rich text. **Anything that is
not Markdown must first go through [references/format-normalize.md](references/format-normalize.md)**
(`.docx` via `scripts/extract_docx.py`, PDF read page by page and de-noised,
plain text structured by heuristics), then get a structure confirmation from the
user. If nothing was supplied, ask for the text.

If the user says "just do it / no questions / one shot", enter **auto mode**:
skip the structure confirmation and the platform question, infer everything,
and attach a decision note to the delivery (sections found, headings you wrote
yourself, platforms chosen and why).

### 1. Choose the target platforms

Read [references/platform-index.md](references/platform-index.md) — the single
source of truth for what each platform accepts.

- **User named the platforms** → use them, do not ask.
- **User named a genre but no platform** → recommend from the index's "best fit"
  column and confirm in one question. Technical/long-form with code → Habr +
  Telegram. Mass-audience Russian narrative → Dzen + VK. Channel-first, short
  attention → Telegram IV + a post. English-language → Telegram IV + Habr.
- **No signal** → build all four; it costs one command and the report tells the
  user what suffers where.

### 2. Pick a voice profile and a structure recipe

Read [references/structure-recipes.md](references/structure-recipes.md). Decide
the **article type** (tutorial, roundup, analysis, interview, data/report,
essay, case study) and take that type's section recipe. The recipe fixes the
skeleton — lede, TL;DR, section count, where callouts and images belong, how the
piece ends — which is what keeps articles of the same type feeling consistent.
Do not improvise a structure per article.

### 3. Write the canonical source

One file, one truth. Front matter plus body, using only the conventions in
[references/common-components.md](references/common-components.md):

```markdown
---
title: …
lang: ru            # ru | en — drives typography and UI labels
lede: one sentence that must work as a feed snippet
author: {{author}}
tags: [a, b, c]
slug: latin-slug
canonical: https://…      # or iv_url: after publishing to telegra.ph
---

:::tldr
- three bullets, the article's actual conclusions
:::

opening paragraphs

<!--cut-->

## Section
…
```

Element conventions — `> [!NOTE]` callouts, `:::spoiler`, `[^1]` footnotes,
`@[youtube](url)` embeds, `==highlight==`, `<!--cut-->` — are all defined in
common-components.md together with what each one becomes on each platform.

**Apply the typography of the language as you write**, do not "fix it later":
[references/typography-ru.md](references/typography-ru.md) for Russian
(«ёлочки», em dash with a non-breaking space, `…`, `–` in numeric ranges),
[references/typography-en.md](references/typography-en.md) for English (curly
quotes, em dash, `…`).

### 4. Lint the source before building

```bash
<SKILL_ROOT>/scripts/source_lint.py <article.md>
<SKILL_ROOT>/scripts/typography_lint.py <article.md> --fix
```

`source_lint.py` is the design gate: walls of text, emphasis inflation,
headings deeper than the platforms render, tables that will collapse, missing
lede, unresolved `{{placeholders}}`. Fix every ERROR; read every WARN and either
fix it or be able to say why not. `typography_lint.py --fix` applies the
language's punctuation rules; add `--nbsp` to bind short words and units.

### 5. Build

```bash
<SKILL_ROOT>/scripts/build_targets.py <article.md> -o out -p telegram,vk,dzen,habr
```

Outputs, per platform: `{slug}.telegram-iv.html` (telegra.ph body),
`{slug}.iv-page.html` (self-hosted IV source page), `{slug}.telegram-post.html`
(channel announcement, ≤ 4096 chars), `{slug}.vk.html`, `{slug}.dzen.html` +
`{slug}.dzen.rss.xml`, `{slug}.habr.md`, and `{slug}.report.md`.

**Read the report.** It lists every degradation (table → list, code → quote,
spoiler → inline) and every manual step (which images to upload in which order).
If a degradation is unacceptable, change the *source* — e.g. replace a 6-column
table with two 3-column ones — and rebuild. Never hand-patch the outputs: the
next build overwrites them.

### 6. Validate

```bash
<SKILL_ROOT>/scripts/validate_post.py --auto out/*
```

Zero ERRORs is the definition of done. Warnings need a human decision.

### 7. Deliver

For Telegram, offer to publish the IV page:

```bash
<SKILL_ROOT>/scripts/telegraph_publish.py out/{slug}.telegram-iv.html --title "…" --author "…"
```

then rebuild the announcement with `--iv-url <published url>` so the "read in
full" link is real.

For VK and Dzen, generate the one-click copy page:

```bash
<SKILL_ROOT>/scripts/wrap_preview.py out/{slug}.vk.html
```

Open it in a browser, press **Copy**, paste into the editor (rich text survives
the clipboard; raw HTML does not).

Tell the user, per platform: the file, how to get it in (paste / RSS / publish),
what was degraded, and what they must do by hand. Include the validator verdict.

## What this skill does on top of plain conversion

These are the editorial moves. They are the reason the output does not read like
a dumped Markdown file.

1. **Lede that works as a snippet.** One sentence, ≤ 300 characters, stating the
   payoff — it becomes the Telegram announcement's opening, the Dzen feed
   snippet and the VK preview. Never "In this article we will look at…".
2. **TL;DR block.** Three bullets that are the article's actual conclusions, not
   a table of contents. They become the announcement bullets automatically.
3. **Anchor per section.** At most one bold anchor per section, five in the whole
   piece. Bold is the only emphasis every platform keeps, so spending it
   everywhere spends it nowhere. `source_lint.py` counts them.
4. **Section numbering and length.** 3–7 `##` sections; every section gets a
   heading that says something (`Почему копипаст не работает`, not `Раздел 2`).
   No more than four consecutive paragraphs without a break.
5. **Callouts carry the asides.** Move parentheticals and "note that…" sentences
   into `> [!NOTE]` / `> [!WARNING]` blocks. They render as `<aside>` on
   telegra.ph and as a labelled quote everywhere else — visible structure that
   costs no CSS.
6. **`<!--cut-->` marks the teaser boundary.** Everything above it is what the
   Telegram announcement may show. Place it after the hook, before the first
   `##`.
7. **Author block, placeholders not names.** End with `{{author}}` /
   `{{one-line bio}}` unless the user gave their own; remind them to replace it.
   If the source already ends with the author's own sign-off, keep theirs — do
   not add a second one.
8. **Images always carry a caption or alt text.** VK and Dzen strip pasted
   images entirely; the caption is what tells the author which upload goes where.
9. **Language-correct typography, written in as you type.** Not a post-pass.

## Hierarchy that survives everywhere (three levels)

| Level | Role | Frequency | Means available on all four platforms |
|---|---|---|---|
| Anchor | the one thing to remember per section | ≤ 5 per article | **bold** |
| Structure | navigation, scanning | every section | `##` headings, lists, dividers |
| Container | asides, quotes, examples | as needed | blockquote, callout, spoiler, code |

There is no colour layer, no underline layer, no font layer. Asking for one is
the most common way to lose a day.

## Platform red lines (the whole list is enforced by validate_post.py)

- **Forbidden everywhere**: `style=` attributes, `class`/`id`, `<div>`, `<span>`
  (except Telegram's spoiler), `<style>`, `<script>`, web fonts, colours.
- **telegra.ph** accepts exactly: `a aside b blockquote br code em figcaption
  figure h3 h4 hr i iframe img li ol p pre s strong u ul video`, attributes
  `href` and `src` only. No `h1`/`h2`, **no tables**.
- **Telegram posts** accept `b i u s a code pre blockquote tg-spoiler tg-emoji`
  and nothing block-level; 4096 characters, 1024 in a caption.
- **VK** keeps two heading levels, bold/italic/strike, links, lists and quotes.
  No code, no tables, no pasted images, no underline.
- **Dzen** takes `p h1–h4 b i u s a ul ol li blockquote figure figcaption img
  video source iframe`; **no formatting inside list items**; no code, no tables.
- **Habr** is Markdown with `#`–`###` only, real code fences with a language,
  tables, `<spoiler title="">`, `<anchor>`, `<abbr>`, formulas. No CSS.

## Gotchas (the ones that actually bite)

- **Writing HTML by hand for a platform.** Always go through the canonical
  source and rebuild; the outputs are build artifacts.
- **Silent degradation.** A table pasted into VK simply vanishes. If the report
  says something degraded, either accept it explicitly or restructure the source.
- **Headings deeper than `###`.** telegra.ph has two body levels, Habr three.
  An `####` becomes a bold paragraph and the outline flattens.
- **Formatting inside Dzen list items.** Bold inside `<li>` is dropped by Dzen —
  put the emphasis in the sentence before the list.
- **Code blocks on VK/Dzen.** They have no code element. Short commands become a
  quote with non-breaking-space indentation; anything longer belongs in a
  screenshot or a link to a gist, and you should say so.
- **Images on VK.** Never assume a pasted `<img>` works. The build emits a
  numbered placeholder and an upload list — follow it in order.
- **Telegram announcement length.** 4096 characters is the hard cap; the builder
  drops middle blocks to fit and says so. Check that what remains still sells
  the piece.
- **telegra.ph and external images.** Images hosted elsewhere often fail to
  render. Verify every image on the published page before sharing the link.
- **`<cut/>` on Habr.** The current editor sets the preview text on a separate
  screen; do not expect the marker to fold the article.
- **Straight quotes.** `"` and `'` in Russian or English body text are the EN/RU
  equivalent of half-width punctuation in Chinese — always wrong, always fixable
  by `typography_lint.py --fix`.
- **Emphasis inflation.** More than one bold anchor per ~150 words and the page
  reads as noise. The linter warns; take it seriously.
- **Dropping content.** Every paragraph, image and list from the source must
  appear in every target, degraded but present. Do not silently trim to fit.

## Adding a platform

New platforms go in `references/platform-{name}.md` and must document:

1. **Accepted tags and attributes** (with the source you verified it against).
2. **Ingestion path** — paste, HTML, Markdown, RSS, API.
3. **Element map** — what each canonical element becomes, and what it degrades to.
4. **Hard limits** — lengths, image sizes, heading depth.
5. **Editorial conventions** — what the audience there expects.

Then register a row in `references/platform-index.md`, add a profile to
`scripts/build_targets.py` (`RULES`-style dict: heading map, table mode, code
mode, image mode, inline map) and a rule set to `scripts/validate_post.py`.
Rebuild the sample article and check the report before considering it done.

> Regression cases for triggering and platform choice live in
> `references/eval-cases.md`.
