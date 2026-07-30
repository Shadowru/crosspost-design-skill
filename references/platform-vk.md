# VK — articles (`vk.com/@…`)

VK has no import API for articles. The only route is **paste into the editor**,
which means the artifact must be *rich text on the clipboard*, not an HTML file.
Open `{slug}.vk.html` through `scripts/wrap_preview.py`, press Copy, paste.

The editor's sanitiser keeps a small set of semantics and silently drops the
rest. Verified against the VK article editor's own toolbar (bold, italic,
strikethrough, link, two heading levels, two quote styles, lists, images,
media, divider) and paste behaviour.

## What survives a paste

```
p  h3  h4  b  strong  i  em  s  del  a  ul  ol  li  blockquote  br
```

Two heading levels only — the toolbar calls them **Заголовок** and
**Подзаголовок**. The builder emits `h3` and `h4`, which the editor maps onto
them; deeper headings become bold paragraphs.

## What does not

| Element | What happens | Substitute the builder uses |
|---|---|---|
| `<img>` | dropped — VK only accepts uploads | numbered placeholder `[Изображение N] caption` + an upload list in the report |
| `<iframe>`, embeds | dropped | link paragraph; add the block via the editor's **+** menu |
| `<pre>`, `<code>` | no code element exists | quote block, indentation rebuilt with non-breaking spaces |
| `<table>` | dropped whole | list of `first cell — column: value; …` lines |
| `<hr>` | the divider is an editor block | a `* * *` paragraph |
| `<u>` | no underline in the toolbar | plain text |
| `style`, `class` | stripped | — |
| footnotes | no anchor support | `[1]` markers plus a **Примечания** list at the end |

**Anything longer than a two-line command does not belong in a VK article as
code.** Screenshot it or link to a gist, and say so in the delivery note.

## Manual steps after pasting

1. Paste the copied rich text into a fresh article.
2. Walk the `[Изображение N]` placeholders top to bottom, upload each image from
   the report's ordered list, delete the placeholder line.
3. Re-add embeds through **+** → the relevant block.
4. Set the cover image and the article title (the title is a separate field).
5. Check the two quote styles: VK offers a left-rule quote and an italic one —
   pick one and keep it consistent through the piece.

## Editorial conventions

- VK readers arrive from a wall post, not from search. The first screen has to
  earn the scroll: lede, then a concrete claim, then the first heading.
- Lists work well here; long unbroken paragraphs do not.
- Keep sections short — 2–4 paragraphs — and give each one a heading.
- The wall post that links the article is a separate piece of writing; reuse the
  Telegram announcement's text as a starting point, minus the hashtags.
- No code, no tables, no formulas: if the piece needs them, VK is the wrong
  platform for that piece and it is worth saying so.

## Checks

```bash
scripts/validate_post.py --platform vk out/{slug}.vk.html
```

Warnings you should expect and act on: `<hr>` present, formatted image
placeholders left in, code degraded to a quote.
