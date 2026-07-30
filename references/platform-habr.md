# Habr (Хабр)

Habr is the one target here that is genuinely rich: real code blocks with
syntax highlighting, tables, spoilers, anchors, abbreviations and TeX formulas.
Paste `{slug}.habr.md` into the editor with **Markdown mode** enabled
(Settings → Markdown, before you start typing).

Verified against Habr's own docs: "Habr Flavored Markdown"
(`habr.com/ru/docs/help/markdown/`) and the WYSIWYG editor description
(`habr.com/ru/docs/help/wysiwyg/`).

## Habr Flavored Markdown

| Element | Syntax | Notes |
|---|---|---|
| Headings | `#`, `##`, `###` | **three levels only** |
| Bold / italic | `**b**`, `*i*` | |
| Underline / strike | `<u>…</u>`, `~~…~~` | |
| Super / subscript | `<sup>`, `<sub>` | |
| Inline code | `` `code` `` | |
| Code block | ```` ```python ```` | 20+ highlighted languages — always name one |
| Quote | `> …` | **no nesting** |
| Lists | `-` / `1.` | nesting supported |
| Table | pipe syntax | native, keep it |
| Image | `![alt](url "title")` | |
| Link | `[text](url)` | |
| Mention | `@username` | |
| Abbreviation | `<abbr title="…">ABBR</abbr>` | |
| Anchor | `<anchor>name</anchor>` | link to it with `#name` |
| Spoiler | `<spoiler title="Header">…</spoiler>` | blank lines around it |
| Media embed | `<oembed>url</oembed>` | YouTube, tweets, CodePen |
| Persona | `<persona>` | publications only |
| Divider | `***` or `---` | |
| Formula (inline) | `$inline$e=mc^2$inline$` | |
| Formula (block) | `$$display$$e=mc^2$$display$$` | |

Headings, tables and personas are **publication-only** — they do not work in
comments.

## What Habr does not have

| Wanted | Substitute |
|---|---|
| `====highlight====` | bold |
| admonition / callout box | `> **Note.** …` quote with a bold label |
| `[^1]` footnotes | numbered list at the end plus `<anchor>note-N</anchor>` |
| heading level 4+ | bold paragraph |
| any CSS | — |

## The cut

The current editor **does not use `<cut/>`**: the preview text is written on the
second screen of the publication flow, separately from the article. So:

- `<!--cut-->` in the source produces nothing by default.
- Set `habr_cut: true` in the front matter only if you are targeting the legacy
  markup.
- Use the `lede:` value as the preview text on that second screen — it was
  written for exactly this job.

## Element map

| Source | Habr |
|---|---|
| `## Section` | `##` |
| `### Sub` | `###` |
| `#### Sub-sub` | `**bold paragraph**` |
| `**bold**` / `==highlight==` | `**bold**` |
| `` `code` `` | `` `code` `` |
| fenced code | fenced code, language preserved |
| `> quote` | `> quote` |
| `> [!NOTE] Title` | `> **Title.** …` (bold lead-in + blocks if it holds a list) |
| `:::tldr` | `**Коротко**` + list |
| `:::spoiler Title` | `<spoiler title="Title">` |
| table | pipe table, alignment preserved |
| `![alt](url "cap")` | `![alt](url "cap")` |
| `@[youtube](url)` | `<oembed>url</oembed>` |
| `[^1]` | `<sup>[1](#note-1)</sup>` + a **Примечания / Notes** section |
| `---` | `---` |

## Editorial conventions

- The audience reads code. Do not paraphrase a command — show it, with a
  language tag.
- A table beats three paragraphs of comparison. This is the only target where
  you can rely on that.
- Hide long logs, configs and derivations in `<spoiler>` — burying them inline
  costs you readers.
- Put the article's claim in the first two paragraphs. Habr's comment section
  finds the gap between the title and the content very quickly.
- Tags and hubs are chosen in the editor, not in the text.

## Checks

```bash
scripts/validate_post.py --platform habr out/{slug}.habr.md
```

It checks heading depth, fence balance, `<spoiler>` balance and titles, tags
outside Habr's sanitiser and stray `style`/`class` attributes.
