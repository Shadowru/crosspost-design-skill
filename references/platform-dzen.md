# Dzen (Дзен)

Dzen accepts content two ways: **paste into the editor**, or **RSS ingestion**
with the article body inside `<content:encoded>`. The build produces both —
`{slug}.dzen.html` for pasting and `{slug}.dzen.rss.xml` as a ready feed item.

Verified against Dzen's publisher documentation for RSS markup
(`dzen.ru/help/ru/website/rss-modify.html`).

## Allowed inside `content:encoded`

```
p  h1  h2  h3  h4  b  i  u  s  a  ul  ol  li  blockquote
figure  figcaption  img  video  source  iframe  br
```

- `h1`–`h2` are the primary level, `h3`–`h4` the secondary. Headings may carry
  `id` for in-article navigation.
- `<figure>` + `<figcaption>` is the correct image form.
- `<video>` needs `<source>` and MP4; minimum 800 × 400.
- `<iframe>` works for YouTube, VK Video and similar.
- **"Parameters intended for additional styling and complex layouts are not
  processed"** — every attribute outside the functional set is dropped.

## Hard constraints that shape the writing

| Constraint | Consequence |
|---|---|
| **No formatting inside list items** | bold/italic inside `<li>` is not rendered — put the emphasis in the sentence introducing the list; the builder strips it and warns |
| No `<pre>`/`<code>` | code becomes a quote with non-breaking-space indentation; long code belongs in a screenshot |
| No `<table>` | tables flatten into a list of `first cell — column: value` lines; keep tables to 3 columns in the source or restructure |
| Images ≥ 700 px wide | narrower images are downranked or dropped |
| Items shorter than 300 characters are ignored | very short pieces should go to Telegram instead |
| No `h5`/`h6` | `####` and deeper become bold paragraphs |

## RSS item requirements

The generated `{slug}.dzen.rss.xml` is RSS 2.0 with the
`content` and `dc` namespaces and a single `<item>`. Before Dzen will connect a
feed it wants a real feed: **at least 10 items**, with at least 3 published in
the last month. So the generated file is a template for your feed builder, not
something to submit alone.

Fill in before use: `<channel><title>`, `<link>`, the item `<link>`/`<guid>`
(use `canonical:` in the front matter) and `<pubDate>` in RFC-822 form.

## Element map

| Canonical | Dzen |
|---|---|
| `## Section` | `<h2>` |
| `### Sub` | `<h3>` |
| `#### Sub-sub` | `<p><b>…</b></p>` |
| `**bold**` / `==highlight==` | `<b>` |
| `*italic*` | `<i>` |
| `~~strike~~` | `<s>` |
| `` `code` `` | plain text |
| fenced code | `<blockquote>` with nbsp indentation |
| `> quote` | `<blockquote>` |
| `> [!NOTE]` | `<blockquote>` with a bold label (bold lead-in + blocks if it holds a list) |
| `:::tldr` | bold lead-in + list |
| `:::spoiler` | title shown, content inline |
| list | `<ul>`/`<ol>`, inline formatting stripped |
| table | `<ul>` of flattened rows |
| `![](…)` | `<figure><img alt><figcaption>` |
| `@[youtube](url)` | `<figure><iframe>` |
| `[^1]` | `[1]` + a **Примечания** list |
| `---` | `<p>* * *</p>` |

## Editorial conventions

- Dzen is a recommendation feed: the title and the first sentence decide
  everything. Write the `lede:` as if it were the only thing shown, because in
  the feed card it is.
- Sections every 2–4 paragraphs; the reader is on a phone in a feed.
- The platform rewards completeness and time-on-page, not brevity — a 1000-word
  piece with structure outperforms a 400-word one.
- No hashtags in the body; Dzen uses the `<category>` tags from the feed or the
  editor's own tag field.

## Checks

```bash
scripts/validate_post.py --platform dzen out/{slug}.dzen.html
scripts/validate_post.py --platform dzen out/{slug}.dzen.rss.xml   # checks the CDATA payload
```
