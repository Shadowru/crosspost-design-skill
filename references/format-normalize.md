# Format normalisation — everything becomes canonical Markdown first

The build pipeline only understands the canonical Markdown described in
[common-components.md](common-components.md). Anything else gets converted here
first, then confirmed with the user, then built. Conversion **restructures, it
never rewrites** — no added, cut or reworded content.

## Deciding what you have

| Input | Signal | Handling |
|---|---|---|
| Markdown | `.md`, or text containing `#`, `##`, `![]()` | straight into the pipeline |
| Word | `.docx` | `scripts/extract_docx.py` |
| PDF | `.pdf` | read page by page with the Read tool, then de-noise |
| Plain text | `.txt`, or a pasted wall of text | infer structure (below) |
| Web / rich text | HTML tags or clipboard style debris | strip styling, map semantics |
| Legacy Word | `.doc` | cannot be parsed — ask for a `.docx` re-save |
| Google Docs | a link | ask for an exported `.docx` or Markdown |

## Word (.docx)

```bash
<SKILL_ROOT>/scripts/extract_docx.py article.docx -o article.md
```

Zero dependencies. Heading styles (`Heading 1–6`, `Заголовок 1–6`, `Title`,
`Название`) become `#`–`######`; bold → `**`, italic → `*`, underline → `<u>`;
numbered and bulleted paragraphs → `- `; tables → Markdown tables; embedded
images are unpacked into `images/` next to the output and referenced relatively.

After conversion: add front matter by hand (`title`, `lang`, `lede`), then run
`source_lint.py`.

## PDF

Read the file page by page with the Read tool, then clean:

1. **Drop running heads and folios** — a line repeating on every page, bare page
   numbers (`12`, `— 12 —`, `Page 12`, `Стр. 12`).
2. **Rejoin hard-wrapped lines** — if a line ends without terminal punctuation
   and the next starts lowercase, they are one paragraph.
3. **Infer headings** with the plain-text heuristics below; font sizes are not
   available.
4. **Images cannot be extracted** — leave a callout placeholder at the position
   and tell the user which page it came from.
5. **Two-column PDFs interleave badly.** If sentences do not connect, say so and
   ask whether the source can be supplied another way.

## Plain text — inferring structure

A line is probably a heading when several of these hold:

- shorter than ~60 characters and does not end in `.`, `!`, `?`;
- surrounded by blank lines, or starts a block;
- carries an ordinal prefix: `1.`, `01`, `I.`, `Часть N`, `Глава N`, `Part N`,
  `Chapter N`, `Раздел N`;
- is followed by several long paragraphs (short line + long block rhythm).

**Levelling:** the most frequent heading pattern becomes `##`; the next level
down, if any, becomes `###`; a lone short line at the very top becomes the
`title`.

**If no headings can be found at all:** split the text into 3–6 topical blocks,
write a heading for each (real headings — `Почему это ломается`, never
`Часть первая`), and state plainly at the confirmation step which headings you
wrote yourself.

Other mappings: blank line → paragraph break; `«цитата»` or a quoted line with a
dash attribution → `lede` candidate or a `>` quote; lines starting with `·`, `-`
or `1.` → list items.

## Web / rich text

`<h1>`–`<h6>` → `#` levels; `<strong>`/`<b>` → `**`; `<em>`/`<i>` → `*`;
`<blockquote>` → `>`; `<li>` → `- `; `<img src>` → `![](src)` with the URL
preserved; `<pre>`/`<code>` → fenced blocks. Strip every style attribute, nested
`<span>`, `&nbsp;` debris and clipper metadata (source link, capture time, tool
byline) — that is not article content.

## Structure confirmation (required, except in auto mode)

Before choosing platforms, show the user what you inferred:

> Found 5 sections: 01 … / 02 … / 03 … (headings 3 and 5 are mine). 2 images,
> 1 table (4 columns — it will flatten into a list on VK and Dzen). Is the
> structure right?

Ten seconds here prevents rebuilding the whole piece. Mention anything that will
degrade badly, because the fix belongs in the source.

## Auto mode

When the user says "just build it", "no questions", "one shot":

1. Skip both the confirmation and the platform question — infer structure, pick
   platforms from [platform-index.md](platform-index.md), build, validate.
2. Deliver with a **decision note**, not a request for approval: sections found,
   headings you invented, platforms chosen and why, and the degradation summary
   from the build report.
3. If the user dislikes a decision, change that one thing and rebuild — the
   canonical source makes this cheap.

Default when the genre gives no signal: build all four targets.
