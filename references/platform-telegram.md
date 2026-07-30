# Telegram — Instant View page + channel post

Telegram is two artifacts, not one. **Instant View is a property of a web page,
not of a message.** A post carries the link; the IV page carries the article.
Building only one of them is the most common mistake.

Verified against `telegra.ph/api` (Node whitelist), `instantview.telegram.org/docs`
(templates) and the Bot API "formatting options" section.

---

## 1. The Instant View page

Two ways to get one:

**A. telegra.ph — no template needed.** Any telegra.ph page has Instant View
automatically. This is the default for authors without a website. Publish with:

```bash
scripts/telegraph_publish.py out/{slug}.telegram-iv.html --title "…" --author "…"
```

**B. Your own page + an IV template.** Host `{slug}.iv-page.html` (or any
semantic article page), then write rules in the IV Editor at
`instantview.telegram.org`. Rules are XPath-1.0 over the page DOM, so a clean
`<article> / <h1> / <p> / <figure>` structure is what makes the template short.
A starter template for the page this skill emits is in
[../assets/instant-view-template.txt](../assets/instant-view-template.txt).

### telegra.ph node whitelist

```
a  aside  b  blockquote  br  code  em  figcaption  figure  h3  h4  hr
i  iframe  img  li  ol  p  pre  s  strong  u  ul  video
```

Attributes: **`href` and `src` only.** Anything else — `alt`, `class`, `style`,
`id` — is dropped, and a tag outside the list is unwrapped into its children.

### Consequences you must design around

| Wanted | Reality | What the builder does |
|---|---|---|
| `h1`/`h2` in the body | not in the whitelist; the title is a separate field | `##` → `h3`, `###` → `h4`, `####` → bold paragraph |
| table | no table node at all | monospaced `<pre>` block, aligned by column |
| callout / admonition | no such node | `<aside>` with a bold label — the closest native thing |
| spoiler / details | not available | quote-like `<aside>` with its title shown |
| image `alt` | attribute dropped | caption goes in `<figcaption>`; alt is not emitted |
| external image | often fails to load | verify every image on the published page |
| code with a language | `<pre>` has no language slot | language line kept in the source, not in the output |

`<iframe>` and `<video>` do work — embeds survive as `<figure><iframe src>`.

---

## 2. The channel post

The announcement uses the Bot API **HTML style**:

```
b  strong  i  em  u  ins  s  strike  del  a  code  pre  blockquote
span class="tg-spoiler"  tg-spoiler  tg-emoji
```

Everything else is a parse error, not a silent drop — Telegram rejects the
message. There are **no block tags**: no `<p>`, no `<ul>`, no headings. Structure
comes from newlines and `•` characters.

Limits: **4096 characters** for a message, **1024** for a media caption.
`blockquote expandable` gives a collapsible quote in recent clients.

### Anatomy of the generated post

```
<b>Title</b>

Lede, or everything above <!--cut--> (max two paragraphs)

• TL;DR bullet one
• TL;DR bullet two
• TL;DR bullet three

<a href="…">Read in full →</a>

#tag #tag
```

The builder drops middle blocks if the post exceeds 4096 and says so in the
report. If it truncated, shorten the lede rather than accepting the cut.

---

## Element map

| Canonical | telegra.ph page | Channel post |
|---|---|---|
| `## Section` | `<h3>` | omitted (post is not an outline) |
| `### Sub` | `<h4>` | omitted |
| paragraph | `<p>` | blank-line-separated text |
| `**bold**` | `<strong>` | `<b>` |
| `*italic*` | `<em>` | `<i>` |
| `==highlight==` | `<strong>` | `<b>` |
| `` `code` `` | `<code>` | `<code>` |
| fenced code | `<pre>` | `<pre>` |
| `> quote` | `<blockquote>` | `<blockquote>` |
| `> [!NOTE]` | `<aside>` + bold label | not carried |
| `:::tldr` | `<aside>` + list | the `•` bullets |
| `:::spoiler` | `<aside>`, content visible | `<tg-spoiler>` if hand-written |
| table | `<pre>` ASCII block | not carried |
| `![](…)` | `<figure><img><figcaption>` | photo attachment |
| `@[youtube](url)` | `<figure><iframe>` | link preview |
| `[^1]` | `[1]` + a `Notes` list at the end | dropped |
| `<!--cut-->` | ignored | teaser boundary |
| `---` | `<hr>` | blank line |

## Editorial conventions

- Telegram readers scan the post and decide in two seconds — the lede must state
  the payoff, not the topic.
- Three bullets is the right number. Five is a wall.
- Hashtags at the end, three at most, in the article's language.
- The IV page can be long; the post cannot. Do not mirror the article in the
  post "just in case".
- Emoji are culturally normal in Telegram posts — one, as a marker, not a row.

## Checks

```bash
scripts/validate_post.py --platform telegraph out/{slug}.telegram-iv.html
scripts/validate_post.py --platform tg-post   out/{slug}.telegram-post.html
scripts/validate_post.py --platform tg-post   out/{slug}.telegram-post.html --limit 1024  # as a caption
```
