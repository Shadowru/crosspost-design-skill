# English micro-typography

Every one of these platforms strips CSS and keeps Unicode. Typography is
therefore the only layer of visual craft that survives publication intact.
Write it correctly the first time; `typography_lint.py --fix` is a safety net.

## Non-negotiable

| Rule | Wrong | Right |
|---|---|---|
| Curly double quotes | `"text"` | `“text”` |
| Curly single quotes / apostrophe | `'text'`, `don't` | `‘text’`, `don’t` |
| Em dash for a break in thought | `word - word` | `word—word` |
| En dash for ranges | `5-7 days` | `5–7 days` |
| Hyphen only inside compounds | `well - known` | `well-known` |
| One ellipsis character | `...` | `…` |
| No space before punctuation | `word , word` | `word, word` |
| Space after punctuation | `word,word` | `word, word` |
| Single space between words | `word␣␣word` | `word word` |

## Dash style

Two defensible conventions; pick one per publication and stay with it.

| Style | Looks like | Flag |
|---|---|---|
| US (default) | `The point—and this matters—is simple.` | `--dash em` |
| UK | `The point – and this matters – is simple.` | `--dash en` |

The linter converts ` - ` to whichever you chose, including after a closing
quote or bracket.

## Non-breaking spaces (`--nbsp`)

- After short function words so they do not end a line: `in␣the`, `of␣a`.
- Between a number and its unit: `10␣kg`, `5␣%`, `Fig.␣3`.
- Inside names and references that must not split: `Windows␣11`, `§␣4`.

Off by default — in short posts the binding can be more noise than help.

## Things the linter will not decide for you

- **Title case vs sentence case.** Sentence case reads better on all four
  platforms and in feed cards. Choose once, apply everywhere.
- **Serial comma.** Pick a side; inconsistency is the only real error.
- **Abbreviations.** Spell out on first use, abbreviate after — Telegram and
  Dzen readers arrive without context.
- **ALL CAPS.** Not emphasis. Use bold, and use it once per section.
- **Exclamation marks.** One per article is already generous; `!!` never.
- **Numerals.** Spell out one to nine in prose; use figures in lists, tables and
  wherever the number is the point.

## Protected regions

Inline code, fenced blocks, URLs, Markdown link targets, HTML tags and
`{{placeholders}}` are masked before any rule runs, so quotes and dashes inside
code stay exactly as written.

## Checking

```bash
scripts/typography_lint.py article.md
scripts/typography_lint.py article.md --fix
scripts/typography_lint.py article.md --fix --dash en --nbsp
```
