/**
 * Regenerate docs/screenshots/*.png for the README.
 *
 * The images are renders of the artifacts this skill actually produces — not
 * captures of the VK / Dzen / Habr interfaces, which cannot be reached without
 * an account there. The only live capture is the telegra.ph page, which the
 * skill publishes itself.
 *
 * Usage:
 *   npm i playwright && npx playwright install chromium
 *   python3 scripts/build_targets.py assets/sample-article.ru.md -o out \
 *           --iv-url <published telegra.ph url>
 *   node docs/make-screenshots.mjs out docs/screenshots
 */

import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';

const OUT_DIR = resolve(process.argv[2] || 'out');
const SHOT_DIR = resolve(process.argv[3] || 'docs/screenshots');
const SLUG = process.argv[4] || 'odin-istochnik';
const IV_URL = process.env.IV_URL
  || 'https://telegra.ph/Kak-perestat-perepisyvat-statyu-chetyre-raza-07-30';

const W = 760, H = 1000;
const read = (f) => readFileSync(join(OUT_DIR, f), 'utf8');

const BASE = `
  *{box-sizing:border-box}
  body{margin:0;background:#eceef1;font:16px/1.6 -apple-system,'Segoe UI',Roboto,
       'Helvetica Neue',Arial,sans-serif;color:#16191d;-webkit-font-smoothing:antialiased}
  .chrome{display:flex;align-items:center;gap:10px;padding:12px 20px;background:#fff;
          border-bottom:1px solid #e3e6ea}
  .dot{width:10px;height:10px;border-radius:50%}
  .who{font-size:14px;font-weight:700;letter-spacing:.01em}
  .file{font-size:12.5px;color:#7b8390;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .tagline{margin-left:auto;font-size:11.5px;color:#9aa1ac;text-transform:uppercase;
           letter-spacing:.07em}
  .sheet{background:#fff;min-height:${H}px;padding:26px 30px 60px}
  .sheet h1{font-size:29px;line-height:1.25;margin:.2em 0 .5em}
  .sheet h2{font-size:23px;line-height:1.3;margin:1.4em 0 .5em}
  .sheet h3{font-size:19px;line-height:1.35;margin:1.3em 0 .45em}
  .sheet h4{font-size:16.5px;margin:1.2em 0 .4em}
  .sheet p,.sheet li{font-size:17px;line-height:1.65}
  .sheet a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(0,0,0,.15)}
  .sheet blockquote{margin:1.1em 0;padding:.15em 0 .15em 16px;
                    border-left:3px solid var(--accent);color:#3b4249}
  .sheet aside{margin:1.1em 0;padding:14px 18px;background:#f4f6f8;border-radius:10px;
               font-size:16px;color:#2c3238}
  .sheet pre{background:#f4f6f8;padding:14px 16px;border-radius:10px;overflow-x:auto;
             font:13.5px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}
  .sheet figure{margin:1.3em 0}
  .sheet img{max-width:100%;height:auto;display:block;margin:0 auto;
             background:#eef1f4;border-radius:8px;min-height:120px}
  .sheet figcaption{font-size:14px;color:#7b8390;text-align:center;margin-top:.5em}
  .sheet table{border-collapse:collapse;width:100%;font-size:15px;margin:1.2em 0}
  .sheet th,.sheet td{border:1px solid #e3e6ea;padding:7px 10px;text-align:left}
  .sheet th{background:#f7f9fb}
  .sheet hr{border:0;border-top:1px solid #e3e6ea;margin:1.6em 0}
  .fade{position:fixed;left:0;right:0;bottom:0;height:110px;pointer-events:none;
        background:linear-gradient(to bottom,rgba(255,255,255,0),#fff 78%)}
`;

function shell({ who, file, accent, tagline, body, fade = true }) {
  return `<!doctype html><html lang="ru"><head><meta charset="utf-8">
  <style>:root{--accent:${accent}}${BASE}</style></head><body>
  <div class="chrome">
    <span class="dot" style="background:${accent}"></span>
    <span class="who">${who}</span><span class="file">${file}</span>
    <span class="tagline">${tagline}</span>
  </div>
  <div class="sheet">${body}</div>
  ${fade ? '<div class="fade"></div>' : ''}
  </body></html>`;
}

const TERM = `
  body{margin:0;background:#0f1418;font:13.5px/1.75 ui-monospace,SFMono-Regular,Menlo,
       'DejaVu Sans Mono',monospace;color:#c9d3de}
  .bar{display:flex;gap:7px;align-items:center;padding:11px 16px;background:#161c22}
  .b{width:11px;height:11px;border-radius:50%}
  .t{margin-left:10px;font-size:12px;color:#66727f}
  .body{padding:16px 20px 22px;white-space:pre-wrap}
  .cmd{color:#8fd3ff} .ok{color:#6ddf8f} .warn{color:#f2c661} .err{color:#ff7b72}
  .dim{color:#7b8794}
`;

function terminal(text) {
  const html = text.split('\n').map((raw) => {
    const line = raw.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    if (line.startsWith('$')) return `<span class="cmd">${line}</span>`;
    if (line.includes('✓')) return `<span class="ok">${line}</span>`;
    if (line.includes('!') && line.includes('WARN')) return `<span class="warn">${line}</span>`;
    if (line.includes('✗') || line.includes('ERROR')) return `<span class="err">${line}</span>`;
    if (line.startsWith('•') || line.startsWith('   ~')) return `<span class="dim">${line}</span>`;
    return line;
  }).join('\n');
  return `<!doctype html><html><head><meta charset="utf-8"><style>${TERM}</style></head>
  <body><div class="bar"><span class="b" style="background:#ff5f56"></span>
  <span class="b" style="background:#ffbd2e"></span><span class="b" style="background:#27c93f"></span>
  <span class="t">crosspost-design · один прогон</span></div>
  <div class="body">${html}</div></body></html>`;
}

const browser = await chromium.launch();
mkdirSync(SHOT_DIR, { recursive: true });

async function shoot(name, html, { height = H, full = false } = {}) {
  const page = await browser.newPage({
    viewport: { width: W, height }, deviceScaleFactor: 2,
  });
  await page.setContent(html, { waitUntil: 'load' });
  await page.screenshot({ path: join(SHOT_DIR, name), fullPage: full });
  await page.close();
  console.log('✓', name);
}

// 1. The pipeline, verbatim console output.
const log = ['$ python3 scripts/source_lint.py     article.md',
  '$ python3 scripts/typography_lint.py article.md',
  '$ python3 scripts/build_targets.py   article.md -o out',
  "$ python3 scripts/validate_post.py --auto 'out/*'",
  '', read('pipeline.log')].join('\n');
await shoot('pipeline.png', terminal(log), { full: true });

// 2. The live telegra.ph page this skill published.
{
  const page = await browser.newPage({
    viewport: { width: W, height: H }, deviceScaleFactor: 2,
  });
  await page.goto(IV_URL, { waitUntil: 'networkidle' });
  await page.screenshot({ path: join(SHOT_DIR, 'telegram-iv.png') });
  await page.close();
  console.log('✓ telegram-iv.png (live page)');
}

// 3. The channel announcement.
const post = read(`${SLUG}.telegram-post.html`).trim();
await shoot('telegram-post.png', `<!doctype html><html lang="ru"><head><meta charset="utf-8">
  <style>${BASE}
   body{background:#0e1621}
   .chrome{background:#17212b;border-bottom-color:#0b1218}
   .who{color:#e7edf3}.file{color:#6b7b8a}.tagline{color:#5b6b7a}
   .msg{margin:26px 20px;padding:16px 18px;background:#182533;border-radius:14px;
        color:#e7edf3;font-size:16px;line-height:1.55;white-space:pre-wrap;max-width:560px}
   .msg a{color:#62b0e8;text-decoration:none}
   .meta{margin:0 20px 24px;font-size:12px;color:#5b6b7a}
  </style></head><body>
  <div class="chrome"><span class="dot" style="background:#2AABEE"></span>
  <span class="who">Telegram · пост в канал</span>
  <span class="file">${SLUG}.telegram-post.html</span>
  <span class="tagline">parse_mode=HTML</span></div>
  <div class="msg">${post}</div>
  <div class="meta">${post.replace(/<[^>]+>/g, '').length} символов из 4096</div>
  </body></html>`, { height: 120, full: true });

// 4-6. Paste-and-feed artifacts, rendered as the platform's whitelist allows.
await shoot('vk.png', shell({
  who: 'ВКонтакте · статья', file: `${SLUG}.vk.html`, accent: '#2787F5',
  tagline: 'рендер артефакта', body: read(`${SLUG}.vk.html`),
}));

await shoot('dzen.png', shell({
  who: 'Дзен · статья', file: `${SLUG}.dzen.html`, accent: '#FF7A00',
  tagline: 'рендер артефакта', body: read(`${SLUG}.dzen.html`),
}));

await shoot('habr.png', shell({
  who: 'Хабр · публикация', file: `${SLUG}.habr.md`, accent: '#629FCB',
  tagline: 'рендер артефакта', body: read('_habr.rendered.html'),
}));

// 7. The degradation report — the part that keeps the pipeline honest.
await shoot('report.png', shell({
  who: 'Отчёт о деградации', file: `${SLUG}.report.md`, accent: '#6b7280',
  tagline: 'что потеряла каждая площадка', body: read('_report.rendered.html'),
}));

await browser.close();
