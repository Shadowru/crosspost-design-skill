# crosspost-design · Telegram IV · VK · Dzen · Habr

**One canonical Markdown source → four published articles, in English or Russian.**

An agent skill (Claude Code / Codex / Cursor …) that formats an article for
Telegram Instant View, VK, Dzen and Habr — platforms that all strip CSS and
each accept a different, short whitelist of markup. It builds every target
deterministically, applies the typography of the language, and reports exactly
what each platform degraded.

English · [Русский](README.ru.md)

Adapted from [gzh-design-skill](https://github.com/isjiamu/gzh-design-skill)
(WeChat / 公众号, Chinese). AGPL-3.0 — see [NOTICE](NOTICE) for what was kept,
adapted and replaced.

---

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
`telegraph_publish.py`.

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
[references/common-components.md](references/common-components.md).

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
```

## Installing as a skill

Copy or symlink the directory into your agent's skills folder — for Claude Code,
`~/.claude/skills/crosspost-design/` (global) or `.claude/skills/crosspost-design/`
(per project). The agent reads `SKILL.md` and pulls in `references/` on demand.

Then just ask, in either language:

> «Разложи эту статью по Дзену, ВК и Хабру»
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
