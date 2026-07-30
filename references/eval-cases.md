# Evaluation cases

Regression checks for triggering, platform choice and degradation handling. Run
them when changing SKILL.md, the platform index or a build profile. They do not
affect a single generation.

## A. Should trigger

| # | User says | Expected |
|---|---|---|
| A1 | «Оформи эту статью для Дзена и ВК» | trigger; platforms = dzen, vk; no platform question |
| A2 | "Make an Instant View version of this post" | trigger; telegram; asks about telegra.ph vs own domain |
| A3 | «Сверстай текст под телегу и Хабр» | trigger; telegram + habr |
| A4 | "I want this published on Habr and as a Telegram post" | trigger; habr + telegram |
| A5 | «Вот docx, сверстай для всех каналов, не спрашивай» | trigger; auto mode; docx normalised first; all four |
| A6 | "Cross-post this article" (no platforms named) | trigger; recommends from platform-index, builds all four |
| A7 | «Почини типографику в статье» | trigger; typography_lint only, no build |

## B. Should not trigger

| # | User says | Expected |
|---|---|---|
| B1 | "Build me a landing page for this product" | no — frontend skill |
| B2 | «Сделай презентацию по этому тексту» | no — slides skill |
| B3 | "Write me an article about X" | no — this skill formats, it does not source-write; offer to format after |
| B4 | "Convert this Markdown to PDF" | no |

## C. Platform choice

| # | Input | Expected recommendation |
|---|---|---|
| C1 | 3000-word engineering write-up with code and a 5-column table | Habr first; warn that VK/Dzen lose the code and flatten the table |
| C2 | 700-word personal essay, Russian | Dzen + VK; Telegram IV as the archive link |
| C3 | 200-word note | Telegram post only; explain the Dzen 300-character floor |
| C4 | English-language technical post | Telegram IV + Habr; state that VK/Dzen are Russian-language networks |
| C5 | Tool roundup, 8 items | all four; table capped at 3 columns in the source |

## D. Degradation handling

| # | Source contains | Expected behaviour |
|---|---|---|
| D1 | 6-column table | source_lint warns; propose splitting *in the source*, not patching output |
| D2 | 40-line code block, targets include VK | report says code became a quote; delivery says the VK version should link out or use a screenshot |
| D3 | Bold inside list items, target Dzen | build strips it, report says so; suggest moving the emphasis into the lead-in sentence |
| D4 | 3 images, target VK | 3 numbered placeholders + an ordered upload list in the report |
| D5 | `####` heading | source_lint warns; it renders as a bold paragraph everywhere |
| D6 | Announcement over 4096 characters | builder drops middle blocks and reports it; delivery asks for a shorter lede |
| D7 | `:::spoiler` with essential content | reviewer note: only Habr folds it — never hide anything required |

## E. Typography

| # | Input | Expected after `--fix` |
|---|---|---|
| E1 | `"текст"` with `lang: ru` | `«текст»` |
| E2 | `«внутри "вложенная" цитата»` | `«внутри „вложенная“ цитата»` |
| E3 | `"it's a 'small' win" - and` with `lang: en` | `“it’s a ‘small’ win”—and` |
| E4 | `5-7 дней`, `...`, `слово - слово` | `5–7 дней`, `…`, `слово — слово` |
| E5 | quotes and dashes inside a fenced block | untouched |
| E6 | `:::tldr` line | untouched (not read as a missing space after a colon) |

## F. Pipeline invariants

| # | Check |
|---|---|
| F1 | `validate_post.py --auto out/*` is clean for the shipped samples |
| F2 | Every source paragraph, image and list item appears in every target |
| F3 | Exactly one sign-off block, at the end |
| F4 | `{{placeholders}}` reach the delivery message as an explicit "replace these" note |
| F5 | Outputs are never hand-edited — a change means editing the source and rebuilding |
