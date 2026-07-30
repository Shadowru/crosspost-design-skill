# Structure recipes and voice profiles

In the original WeChat skill this file's role was played by colour themes. Here
there is no colour. What makes two articles of the same kind feel like they came
from the same desk is **the skeleton and the voice** — how the piece opens, how
often it breaks, where the asides go, how it ends.

Pick one recipe per article and follow it. Improvising the shape per piece is
how a channel ends up looking like four different authors.

---

## Voice profiles

Choose with `tone:` in the front matter. The profile does not change the markup;
it changes the writing decisions the recipes leave open.

| Profile | Reads like | Sentences | Emphasis | Callouts | Best for |
|---|---|---|---|---|---|
| `editorial` | a magazine feature | medium, varied | one anchor per section | sparing, for asides | analysis, opinion, industry pieces |
| `technical` | documentation with an argument | short, declarative | on identifiers and results | frequent, for caveats | tutorials, engineering write-ups |
| `digest` | a curated list with a point of view | short | one per item | rare | roundups, tool lists, link digests |
| `essay` | a person thinking out loud | long, rhythmic | almost none | none | reflection, personal experience |
| `field-notes` | a log written up afterwards | clipped | on outcomes | frequent, for what went wrong | case studies, post-mortems |

Cross-platform reality check: `essay` survives VK and Dzen best; `technical`
belongs on Habr and Telegram; `digest` works everywhere; `field-notes` needs
Habr if there is real code.

---

## Recipes by article type

Each recipe lists the skeleton in order. `##` = section heading.

### Tutorial / how-to — `technical`

```
lede: what you will be able to do, and in what time
:::tldr — the three steps, or the result
<!--cut-->
opening: the problem, in one paragraph
## Prerequisites          → callout [!NOTE] with versions and assumptions
## Step 1 …               → code block + one screenshot
## Step 2 …               → code block, callout [!WARNING] on the trap
## Step 3 …
## Checking it worked     → expected output, verbatim
## What to do when it breaks → :::spoiler with the long log
sign-off
```

Rules: every step is imperative and testable. Every command in a fenced block
with a language. One image per step at most. Never more than four paragraphs
without code, a list or a callout.

### Roundup / tool list — `digest`

```
lede: what the list is for and who it is not for
:::tldr — the top three, named
<!--cut-->
opening: the selection criteria, honestly stated
## 1. Name  → what it does · who it fits · the catch (bold anchor on the catch)
## 2. Name
…  (5–9 items, identical internal shape)
## How to choose  → a ≤3-column table, or a list if VK/Dzen matter
sign-off
```

Rules: identical internal structure for every item — that repetition *is* the
design. The "catch" line is what separates a roundup from an ad.

### Analysis / opinion — `editorial`

```
lede: the claim, not the topic
:::tldr — the argument in three steps
<!--cut-->
opening: the observation that started it
## What everyone assumes
## Why that breaks         → the evidence; one bold anchor
## What follows instead
## The objection worth taking seriously  → callout [!NOTE]
## What to do with this
sign-off
```

Rules: state the claim before the evidence. One counter-argument section,
genuinely argued, is what makes the piece credible.

### Interview / profile — `editorial`

```
lede: the one thing this person said that changes your mind
:::tldr — three takeaways in their voice
<!--cut-->
opening: who they are, in two sentences
## Question as a heading   → quote blocks for the answers
## Question as a heading
…
## What stayed with me     → your own read, clearly separated
sign-off
```

Rules: questions become headings — it is the only way an interview stays
scannable without CSS. Answers in `>` quotes so the two voices are visually
distinct on every platform.

### Data / report — `technical`

```
lede: the headline number and what it means
:::tldr — three findings
<!--cut-->
opening: what was measured and how
## Method              → callout [!NOTE] on limitations
## Finding 1           → table (≤3 columns) or chart image with a caption
## Finding 2
## Finding 3
## What we cannot conclude
sign-off
```

Rules: every number gets a unit and a source footnote. Charts as images with
captions — the caption must state the finding, because on VK the image is
uploaded separately and the caption is its label.

### Essay / personal — `essay`

```
lede: the sentence the whole piece is orbiting
<!--cut-->
opening: the scene
## three or four sections with headings that are phrases, not labels
sign-off (short, no CTA stack)
```

Rules: no TL;DR — it kills the form. Almost no bold. Longer paragraphs are
allowed here and only here, but still break every ~4.

### Case study / post-mortem — `field-notes`

```
lede: what broke and what it cost
:::tldr — cause, fix, prevention
<!--cut-->
## Context           → what the system was
## What happened     → timeline as an ordered list
## Why               → the actual cause; one bold anchor
## The fix           → code or config
## What changed since → callout [!IMPORTANT]
sign-off
```

Rules: timeline as an ordered list, times included. Blameless language. The
prevention section is the reason the piece exists — do not let it be one line.

---

## Section rhythm (all recipes)

| Element | Target |
|---|---|
| `##` sections | 3–7 |
| Paragraphs per section | 2–4 |
| Consecutive paragraphs without a break | ≤ 4 (linter warns at 5) |
| Paragraph length | ≤ 700 characters (linter warns) |
| Bold anchors | ≤ 5 per article, ≤ 1 per section |
| Images | 1 per 2–3 sections; every one captioned |
| Callouts | 1–3 per article, more for `technical` |

## Headings that work

- Say the content, not the slot: `Почему копипаст не работает`, not `Раздел 2`.
- 3–8 words. A heading that wraps to two lines on a phone has failed.
- Parallel grammar across sections — all nouns or all questions, not a mix.
- No numbering in the text; if the recipe is a list of items, number them (`## 1. Name`).

## Endings

Choose one, never stack them:

- **Recap** — one paragraph, no bullets, for `technical` and `field-notes`.
- **Turn** — a sentence that reframes the opening, for `essay` and `editorial`.
- **Invitation** — one concrete question to the reader, for `digest`.

Then the sign-off block, once, with `{{author}}` placeholders.
