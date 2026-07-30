# crosspost-design · Telegram IV · ВКонтакте · Дзен · Хабр

**Один канонический Markdown → четыре опубликованные статьи, на русском или английском.**

Скилл для агента (Claude Code / Codex / Cursor …), который верстает статью под
Telegram Instant View, ВК, Дзен и Хабр — площадки, каждая из которых вырезает
CSS и принимает свой короткий белый список разметки. Скилл детерминированно
собирает все цели, применяет типографику нужного языка и показывает, что именно
каждая площадка потеряла.

[English](README.md) · Русский

Адаптация [gzh-design-skill](https://github.com/isjiamu/gzh-design-skill)
(WeChat / 公众号, китайский). AGPL-3.0 — что сохранено, переработано и заменено,
описано в [NOTICE](NOTICE).

---

## Исходная посылка

WeChat разрешает произвольный инлайновый CSS — поэтому там имеет смысл возить с
собой цветовые темы. **Telegram, ВК, Дзен и Хабр — нет.** Каждая площадка
удаляет `style`, `class`, шрифты и цвета при импорте. Остаются структура и
Unicode.

Поэтому «оформление» здесь — это:

- **структура**: ритм разделов, лид, который работает как сниппет в ленте,
  блок «Коротко», врезки, один жирный акцент на раздел;
- **типографика**: «ёлочки», настоящие тире, многоточие, неразрывные пробелы —
  они выживают, потому что это символы, а не стили;
- **честная деградация**: таблица становится моноширинным блоком в telegra.ph и
  списком во ВК, и вы узнаёте об этом до публикации, а не после.

## Что получается на выходе

| Цель | Файл | Как публиковать |
|---|---|---|
| Telegram Instant View | `{slug}.telegram-iv.html` | `telegraph_publish.py` → ссылка с готовым IV |
| Instant View на своём сайте | `{slug}.iv-page.html` | хостите страницу + шаблон правил из `assets/` |
| Анонс в канал | `{slug}.telegram-post.html` | `parse_mode=HTML`, до 4096 символов |
| Статья ВК | `{slug}.vk.html` | страница предпросмотра → «Копировать» → вставка |
| Дзен | `{slug}.dzen.html`, `{slug}.dzen.rss.xml` | вставка в редактор или RSS |
| Хабр | `{slug}.habr.md` | вставка в режиме Markdown |
| Отчёт о деградации | `{slug}.report.md` | что потерялось и что делать руками |

## Быстрый старт

```bash
# 1. проверить исходник: структура, потом типографика
python3 scripts/source_lint.py     assets/sample-article.ru.md
python3 scripts/typography_lint.py assets/sample-article.ru.md --fix

# 2. собрать все цели
python3 scripts/build_targets.py   assets/sample-article.ru.md -o out

# 3. проверить соответствие — ноль ERROR означает «готово»
python3 scripts/validate_post.py --auto 'out/*'

# 4. опубликовать страницу IV и пересобрать анонс со ссылкой
python3 scripts/telegraph_publish.py out/odin-istochnik.telegram-iv.html \
        --title "…" --author "…"
python3 scripts/build_targets.py assets/sample-article.ru.md -o out \
        -p telegram --iv-url https://telegra.ph/…

# 5. получить страницу с кнопкой «Копировать» для ВК / Дзена
python3 scripts/wrap_preview.py out/odin-istochnik.vk.html
```

Только стандартная библиотека Python 3. Никаких зависимостей и сети, кроме
`telegraph_publish.py`.

## Канонический исходник

```markdown
---
title: Как перестать переписывать статью четыре раза
lang: ru
lede: Одно предложение, которое должно работать как сниппет в ленте.
author: {{автор}}
tags: [а, б]
canonical: https://…
---

:::tldr
- три настоящих вывода
:::

вступительные абзацы
<!--cut-->

## Раздел

> [!NOTE] Врезка
> Вынесена из абзаца, в telegra.ph рендерится как <aside>.

:::spoiler Длинные логи
Сворачивается на Хабре, на остальных площадках видна целиком.
:::

| не больше 3 колонок | чтобы пережить схлопывание |
| --- | --- |
```

Полный справочник элементов и того, во что каждый превращается на каждой
площадке: [references/common-components.md](references/common-components.md).

## Состав

```
SKILL.md                        рабочий процесс, по которому идёт агент
references/
  platform-index.md             единый источник правды: что принимает каждая площадка
  platform-telegram.md          узлы telegra.ph, шаблоны IV, HTML Bot API
  platform-vk.md                редактор только для вставки, порядок загрузки картинок
  platform-dzen.md              белый список content:encoded, требования к RSS
  platform-habr.md              Habr Flavored Markdown, спойлеры, якоря, формулы
  typography-ru.md              «ёлочки», тире, неразрывные пробелы
  typography-en.md              curly quotes, em/en dash, ellipsis
  structure-recipes.md          тип статьи → скелет; пять профилей голоса
  common-components.md          каноническая разметка → рендеринг по площадкам
  format-normalize.md           docx / pdf / текст / rich text → Markdown
  eval-cases.md                 регрессионные кейсы
scripts/
  build_targets.py              парсер + пять рендереров + отчёт о деградации
  source_lint.py                проверка исходника до сборки
  typography_lint.py            типографика RU/EN, с --fix
  validate_post.py              соответствие разметки каждой площадке
  telegraph_publish.py          публикация в telegra.ph (IV из коробки)
  wrap_preview.py               страница с кнопкой «Копировать»
  extract_docx.py               .docx → Markdown, без зависимостей
assets/
  sample-article.ru.md          русский пример со всеми элементами
  sample-article.en.md          английский пример
  preview-template.html         оболочка предпросмотра
  instant-view-template.txt     стартовые правила IV для своей страницы
```

## Установка

Скопируйте или слинкуйте каталог в папку скиллов агента — для Claude Code это
`~/.claude/skills/crosspost-design/` (глобально) или `.claude/skills/crosspost-design/`
(в проекте). Агент читает `SKILL.md` и подтягивает `references/` по мере
надобности.

Дальше достаточно попросить:

> «Разложи эту статью по Дзену, ВК и Хабру»
> «Сделай Instant View и анонс в канал»

## Откуда взяты факты о площадках

Белые списки в `references/` сверены с telegra.ph/api,
instantview.telegram.org/docs, core.telegram.org/bots/api,
habr.com/ru/docs/help/markdown/, habr.com/ru/docs/help/wysiwyg/ и
dzen.ru/help/ru/website/rss-modify.html. Площадки меняются: после обновлений
перепроверяйте и правьте сначала файл в `references/` — скрипты опираются на те
же факты.

## Лицензия

AGPL-3.0, унаследована от исходного проекта. См. [LICENSE](LICENSE) и
[NOTICE](NOTICE).
