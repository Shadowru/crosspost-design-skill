# crosspost-design · Telegram IV · VK · Dzen · Habr

**One canonical Markdown source → four published articles, in English or Russian.**

An agent skill (Claude Code / Codex / Cursor …) that formats an article for
Telegram Instant View, VK, Dzen and Habr — platforms that all strip CSS and
each accept a different, short whitelist of markup. It builds every target
deterministically, applies the typography of the language, and reports exactly
what each platform degraded.

[Русский](README.md) · English

Adapted from [gzh-design-skill](https://github.com/isjiamu/gzh-design-skill)
(WeChat / 公众号, Chinese). AGPL-3.0 — see [NOTICE](NOTICE) for what was kept,
adapted and replaced.

---

## One run

Lint the source, build, check compliance. Zero ERRORs means it is ready to ship.

![Pipeline run: source_lint, typography_lint, build_targets, validate_post](docs/screenshots/pipeline.png)

## The premise

WeChat lets you paste arbitrary inline CSS, so a WeChat skill can ship colour
themes. **Telegram, VK, Dzen and Habr do not.** Every one of them deletes
`style`, `class`, fonts and colours on import. What survives is structure and
Unicode.

So the design layer here is:

- **structure** — section rhythm, a lede that works as a feed snippet, TL;DR,
  callouts, one bold anchor per section;
- **typography** — «ёлочки» or curly quotes, real dashes, ellipses, non-breaking
  spaces; these survive because they are characters, not styling;
- **honest degradation** — a table becomes a monospaced block on telegra.ph and a
  list on VK, and you are told so before you publish.

## What it looks like

Below is one article built for four platforms. Look past the styling and at the
differences: where a table stayed a table and where it collapsed into a list;
where code stayed code and where it became a quote.

### Telegram Instant View — a live page

The only genuine screenshot here: the skill published this page itself with
`telegraph_publish.py`, and telegra.ph pages get Instant View for free.

**[Open the demo →](https://telegra.ph/Kak-perestat-perepisyvat-statyu-chetyre-raza-07-30)**
(paste the link into any Telegram chat and the Instant View button appears)

![telegra.ph page: the TL;DR block as an aside, the table as a monospaced block](docs/screenshots/telegram-iv.png)

telegra.ph's limits are visible: headings are `h3`/`h4` only and there are no
tables at all, so the source table became an aligned monospaced block and
`:::tldr` became an `<aside>`.

### The channel announcement

![Telegram announcement: title, lede, three bullets, link, hashtags — 435 of 4096 characters](docs/screenshots/telegram-post.png)

A separate artifact: Telegram messages have no block tags whatsoever, so
structure rests on line breaks. The bullets come from `:::tldr`, the "read in
full" link from the published page, and the character count is enforced by the
validator.

### VK and Dzen — where it hurts most

<table>
<tr>
<td width="50%"><img src="docs/screenshots/vk.png" alt="VK article: the table flattened into a list"></td>
<td width="50%"><img src="docs/screenshots/dzen.png" alt="Dzen article: h2/h3 headings, formatting stripped inside list items"></td>
</tr>
<tr>
<td><b>VK.</b> The table collapsed into "first cell — column: value" lines.
There is no code element at all, so the fenced block became a quote with
non-breaking-space indentation. Images cannot be pasted: numbered placeholders
take their place and the report lists the upload order.</td>
<td><b>Dzen.</b> Headings are <code>h2</code>/<code>h3</code>, the table
collapses the same way. The platform's real trap is that formatting inside list
items is never rendered, so the builder strips it and reports that it did.</td>
</tr>
</table>

### Habr — the one platform that loses nothing

![Habr publication: a real table, h1–h3 headings](docs/screenshots/habr.png)

The same table is still a table, code is still code with its language, and the
spoiler is a real `<spoiler>`. If a piece has code, tables or formulas, Habr
should be the first target rather than the last.

### The degradation report

![Report: per platform, what changed and what to do by hand](docs/screenshots/report.png)

The insurance against "pasted it and never noticed". Per platform: which files
were built, what degraded, and what you have to do by hand — such as the order
in which to upload images to VK.

> **Honest note about these images.** Only one is a real screenshot — the
> telegra.ph page, because the skill publishes it itself. VK, Dzen and Habr
> cannot be reached without an account there, so what you see is a **render of
> the artifacts actually produced**, shown in a neutral reader: the content and
> the constraints are real, the platforms' own interfaces are not imitated.
> Regenerate everything with
> `node docs/make-screenshots.mjs out docs/screenshots`.

## What you get

| Target | File | How it gets published |
|---|---|---|
| Telegram Instant View | `{slug}.telegram-iv.html` | `telegraph_publish.py` → a link with native IV |
| Instant View (own site) | `{slug}.iv-page.html` | host it + the IV template in `assets/` |
| Telegram announcement | `{slug}.telegram-post.html` | `parse_mode=HTML`, ≤ 4096 chars |
| VK article | `{slug}.vk.html` | preview page → Copy → paste |
| Dzen | `{slug}.dzen.html`, `{slug}.dzen.rss.xml` | paste, or RSS ingestion |
| Habr | `{slug}.habr.md` | paste in Markdown mode |
| Degradation report | `{slug}.report.md` | what was lost, what to do by hand |

## Quick start

```bash
# 1. lint the source: structure, then typography
python3 scripts/source_lint.py     assets/sample-article.ru.md
python3 scripts/typography_lint.py assets/sample-article.ru.md --fix

# 2. build every target
python3 scripts/build_targets.py   assets/sample-article.ru.md -o out

# 3. check compliance — zero ERRORs is the definition of done
python3 scripts/validate_post.py --auto 'out/*'

# 4. publish the Instant View page, then relink the announcement
python3 scripts/telegraph_publish.py out/odin-istochnik.telegram-iv.html \
        --title "…" --author "…"
python3 scripts/build_targets.py assets/sample-article.ru.md -o out \
        -p telegram --iv-url https://telegra.ph/…

# 5. get a one-click copy page for VK / Dzen
python3 scripts/wrap_preview.py out/odin-istochnik.vk.html
```

Python 3 standard library only. No dependencies, no network except
`telegraph_publish.py`. (Playwright is needed only to regenerate this README's
images and plays no part in the skill itself.)

## The canonical source

```markdown
---
title: Как перестать переписывать статью четыре раза
lang: ru
lede: One sentence that must work as a feed snippet.
author: {{author}}
tags: [a, b]
canonical: https://…
---

:::tldr
- three actual conclusions
:::

opening paragraphs
<!--cut-->

## Section

> [!NOTE] An aside
> Moved out of the paragraph, rendered as <aside> on telegra.ph.

:::spoiler Long logs
Folded on Habr, visible everywhere else.
:::

| ≤ 3 columns | so it survives flattening |
| --- | --- |
```

Full element reference, with what each one becomes on each platform:
[references/common-components.md](references/common-components.md). A live
example using every element: [assets/sample-article.ru.md](assets/sample-article.ru.md).

## Layout

```
SKILL.md                        the workflow the agent follows
references/
  platform-index.md             single source of truth: what each platform accepts
  platform-telegram.md          telegra.ph nodes, IV templates, Bot API HTML
  platform-vk.md                paste-only editor, upload flow
  platform-dzen.md              content:encoded whitelist, RSS requirements
  platform-habr.md              Habr Flavored Markdown, spoilers, anchors, formulas
  typography-ru.md              «ёлочки», тире, неразрывные пробелы
  typography-en.md              curly quotes, em/en dash, ellipsis
  structure-recipes.md          article type → skeleton; five voice profiles
  common-components.md          canonical syntax → per-platform rendering
  format-normalize.md           docx / pdf / plain text / rich text → Markdown
  eval-cases.md                 regression cases
scripts/
  build_targets.py              parser + five renderers + degradation report
  source_lint.py                design gate before the build
  typography_lint.py            EN/RU micro-typography, with --fix
  validate_post.py              per-platform markup compliance
  telegraph_publish.py          publish to telegra.ph (native Instant View)
  wrap_preview.py               copy-to-clipboard preview page
  extract_docx.py               .docx → Markdown, no dependencies
assets/
  sample-article.ru.md          Russian sample exercising every element
  sample-article.en.md          English sample
  preview-template.html         the preview shell
  instant-view-template.txt     starter IV rules for a self-hosted page
docs/
  make-screenshots.mjs          regenerate the README images
  render-md.py                  render .md to HTML with the same parser
```

## Installing as a skill

The repository is both a plugin and its own marketplace, so two commands do it:

```
/plugin marketplace add Shadowru/crosspost-design-skill
/plugin install crosspost-design@crosspost-design
```

Then `/reload-plugins`. Updates arrive via `/plugin marketplace update
crosspost-design`.

Copying works too: put or symlink the directory at
`~/.claude/skills/crosspost-design/` (global) or `.claude/skills/crosspost-design/`
(per project) — `.claude-plugin/plugin.json` makes it auto-load next session. The
agent reads `SKILL.md` and pulls in `references/` on demand.

To check that everything still works after installing:

```bash
scripts/selftest.sh     # 24 checks: both samples built, every gate fires
```

Then just ask, in either language:

> «Сверстай эту статью под Дзен, ВК и Хабр»
> "Make an Instant View version and a channel post out of this"

## Verified platform facts

Whitelists in `references/` were checked against telegra.ph/api,
instantview.telegram.org/docs, core.telegram.org/bots/api,
habr.com/ru/docs/help/markdown/, habr.com/ru/docs/help/wysiwyg/ and
dzen.ru/help/ru/website/rss-modify.html. Platforms change; re-verify before
trusting a whitelist after an update, and fix the reference file first — the
scripts read their rules from the same facts.

## Licence

AGPL-3.0, inherited from the upstream project. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
