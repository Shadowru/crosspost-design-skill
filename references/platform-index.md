# Platform index — the single source of truth

Step 1 of the workflow reads this table to recommend targets; step 5 reads the
per-platform file for the element map. If a fact here and a fact in a platform
file disagree, **the platform file wins** — it carries the verification source.

## Registered platforms

| Platform | How content gets in | Headings | Code | Tables | Images | Best fit |
|---|---|---|---|---|---|---|
| Telegram Instant View | telegra.ph API, or your own page + an IV template | `h3`, `h4` | `<pre>` | ✗ → `<pre>` | `<figure>`, Telegram-hosted only | channel-first publishing, English or Russian, any length |
| Telegram post | Bot API / paste, `parse_mode=HTML` | ✗ (bold line) | `<pre>`, `<code>` | ✗ | attachment | the announcement that carries the IV link |
| VK article | paste into the `vk.com/@…` editor | 2 levels | ✗ → quote | ✗ → list | upload in the editor | mass Russian audience, narrative and lists |
| Dzen | paste into the editor, or RSS `content:encoded` | `h1`–`h4` | ✗ → quote | ✗ → list | `<figure>`, ≥ 700 px wide | mass Russian audience, SEO and feed reach |
| Habr | paste in Markdown mode (HFM) | `#`–`###` | fenced, highlighted | ✓ native | Markdown image | technical long-form, code, tables, formulas |

## Files

| Platform | Reference | Build profile | Validator key |
|---|---|---|---|
| Telegram IV | [platform-telegram.md](platform-telegram.md) | `TELEGRAPH`, `IVPAGE` | `telegraph`, `iv-page` |
| Telegram post | [platform-telegram.md](platform-telegram.md) | `build_tg_post` | `tg-post` |
| VK | [platform-vk.md](platform-vk.md) | `VK` | `vk` |
| Dzen | [platform-dzen.md](platform-dzen.md) | `DZEN` | `dzen` |
| Habr | [platform-habr.md](platform-habr.md) | `HabrRenderer` | `habr` |

## Choosing targets

- **User named platforms** → use exactly those.
- **Technical piece with code, tables or formulas** → Habr first; Telegram IV
  second (code survives as `<pre>`). VK and Dzen will hurt — warn the user that
  code becomes a quote.
- **Narrative, opinion, lifestyle, Russian audience** → Dzen + VK, Telegram IV
  as the archive link.
- **English audience** → Telegram IV + Habr (Habr has an English section); VK and
  Dzen are Russian-language networks and are usually the wrong spend.
- **Short piece (< 300 words)** → Telegram post only. Dzen deprioritises short
  items and VK articles look empty.
- **No signal** → build all four and let the report show the trade-offs.

One source, many targets: never maintain per-platform copies of the text.

## Language pairing

| `lang:` | Typography reference | Notes |
|---|---|---|
| `ru` | [typography-ru.md](typography-ru.md) | «ёлочки», `—` with a non-breaking space, `–` in ranges |
| `en` | [typography-en.md](typography-en.md) | curly quotes, unspaced em dash by default |

UI strings the builder inserts (`Примечания` / `Notes`, `Коротко` / `TL;DR`,
`Читать целиком` / `Read in full`) come from the `L10N` table in
`scripts/build_targets.py` and follow `lang:`.

## Registering a new platform

1. Write `references/platform-{name}.md` with a verified tag whitelist.
2. Add a row to both tables above.
3. Add a profile dict to `scripts/build_targets.py` and a rule set to
   `scripts/validate_post.py`.
4. Rebuild `assets/sample-article.ru.md` and `assets/sample-article.en.md`, read
   the report, and confirm `validate_post.py --auto` is clean.
