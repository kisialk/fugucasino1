#!/usr/bin/env python3
"""Generate favicons and full-rebuild SEO HTML for Fugu Casino."""
from __future__ import annotations

import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://fugu-casino.vercel.app"
AFF = "https://lkhq.cc/8f315e"
OG_IMG = f"{BASE}/banner.png"
DATE = "2026-05-17"

NAV = [
    ("official-site", "Официальный сайт"),
    ("casino", "Казино"),
    ("bets", "Ставки"),
    ("bonus", "Бонусы"),
    ("registration", "Регистрация"),
    ("zerkalo", "Зеркало"),
    ("download", "Скачать"),
    ("login", "Вход"),
]

RELATED = [
    ("official-site", "Официальный сайт"),
    ("login", "Вход"),
    ("registration", "Регистрация"),
    ("zerkalo", "Зеркало"),
    ("bonus", "Бонусы"),
    ("casino", "Казино"),
    ("download", "Скачать"),
    ("bets", "Ставки"),
]

PAGES: dict = {}


def P(slug: str, **kw) -> None:
    PAGES[slug] = kw


def slug_id(text: str) -> str:
    s = text.lower().replace("ё", "е")
    s = re.sub(r"[^a-z0-9а-я]+", "-", s, flags=re.I)
    return s.strip("-")[:48]


def png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path: Path, size: int, draw) -> None:
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            raw.extend(draw(x, y, size))
    comp = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", comp) + png_chunk(b"IEND", b"")
    path.write_bytes(png)


def icon_rgba(x: int, y: int, size: int) -> bytes:
    cx, cy = size / 2, size / 2
    r = size * 0.42
    dx, dy = x - cx + 0.5, y - cy + 0.5
    bg = (31, 41, 55, 255)
    if dx * dx + dy * dy > r * r:
        return bytes(bg)
    t = size / 16
    if dy < -t and dx < t * 2:
        return bytes((83, 255, 0, 255))
    if abs(dx + t) < t * 1.4 and dy < t * 3:
        return bytes((78, 163, 255, 255))
    if abs(dy - t * 2) < t and dx < t * 3:
        return bytes((106, 99, 255, 255))
    if dx * dx + dy * dy < (r * 0.55) ** 2:
        return bytes((217, 228, 255, 255))
    return bytes(bg)


def write_ico(path: Path, sizes=(16, 32, 48)) -> None:
    images = []
    for s in sizes:
        raw = bytearray()
        for y in range(s):
            raw.append(0)
            for x in range(s):
                r, g, b, a = icon_rgba(x, y, s)
                raw.extend((b, g, r, a))
        images.append((s, zlib.compress(bytes(raw), 9)))
    offset = 6 + 16 * len(images)
    parts = [struct.pack("<HHH", 0, 1, len(images))]
    blobs = []
    for i, (s, data) in enumerate(images):
        parts.append(struct.pack("<BBBBHHII", s, s, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
        blobs.append(data)
    path.write_bytes(b"".join(parts) + b"".join(blobs))


def generate_favicons() -> None:
    icons = ROOT / "assets" / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    for name, size in [
        ("favicon-16x16.png", 16),
        ("favicon-32x32.png", 32),
        ("apple-touch-icon.png", 180),
        ("android-chrome-192x192.png", 192),
        ("android-chrome-512x512.png", 512),
    ]:
        write_png(ROOT / name, size, icon_rgba)
    write_png(icons / "favicon-source.png", 512, icon_rgba)
    write_ico(ROOT / "favicon.ico")


def head_block(title: str, desc: str, path: str) -> str:
    url = f"{BASE}{path}"
    return f"""    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="index, follow, max-image-preview:large">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="{OG_IMG}">
    <meta property="og:locale" content="ru_RU">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{OG_IMG}">
    <meta name="theme-color" content="#1f2937">
    <link rel="icon" href="/favicon.ico?v=3" sizes="any">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png?v=3">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png?v=3">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png?v=3">
    <link rel="manifest" href="/site.webmanifest">
    <link rel="stylesheet" href="/style.css">"""


def schema_block(
    path: str,
    title: str,
    desc: str,
    breadcrumb: str,
    faq: list[tuple[str, str]] | None,
    article: bool,
    h1: str,
    home: bool,
) -> str:
    url = f"{BASE}{path}"
    items = (
        [{"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{BASE}/"}]
        if home
        else [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": breadcrumb, "item": url},
        ]
    )
    graph: list[dict] = [
        {"@type": "WebSite", "@id": f"{BASE}/#website", "url": f"{BASE}/", "name": "Fugu Casino", "inLanguage": "ru-RU"},
        {"@type": "Organization", "@id": f"{BASE}/#organization", "name": "Fugu Casino", "url": f"{BASE}/", "logo": f"{BASE}/logo.svg"},
        {"@type": "WebPage", "@id": f"{url}#webpage", "url": url, "name": title, "description": desc, "isPartOf": {"@id": f"{BASE}/#website"}, "inLanguage": "ru-RU"},
        {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": items},
    ]
    if article:
        graph.append(
            {
                "@type": "Article",
                "@id": f"{url}#article",
                "headline": h1,
                "description": desc,
                "author": {"@id": f"{BASE}/#organization"},
                "publisher": {"@id": f"{BASE}/#organization"},
                "datePublished": DATE,
                "dateModified": DATE,
                "inLanguage": "ru-RU",
                "mainEntityOfPage": {"@id": f"{url}#webpage"},
            }
        )
    if faq:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{url}#faq",
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq],
            }
        )
    return f'    <script type="application/ld+json">\n{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)}\n    </script>'


def header_html(active: str | None = None) -> str:
    def nav_link(slug: str, label: str) -> str:
        cur = ' aria-current="page"' if slug == active else ""
        return f'              <a href="/{slug}/"{cur}>{label}</a>'

    links = "\n".join(nav_link(s, l) for s, l in NAV)
    mob = "\n".join(f'            <a href="/{s}/">{l}</a>' for s, l in NAV)
    return f"""    <header class="site-header">
      <div class="container header-inner">
        <div class="header-row">
          <a class="logo-link" href="/">
            <img src="/logo.svg" alt="Fugu Casino — логотип фугу казино" width="180" height="48" />
          </a>
          <a class="btn-bonus-header" href="{AFF}" rel="nofollow sponsored noopener" target="_blank">Бонус</a>
          <div class="header-end">
            <nav class="nav-desktop" aria-label="Основное меню">
{links}
            </nav>
            <button type="button" class="nav-toggle" aria-controls="nav-mobile" aria-expanded="false" aria-label="Меню">
              <span class="sr-only">Открыть меню</span>
              <span></span><span></span><span></span>
            </button>
          </div>
        </div>
        <div class="header-mobile-panel" id="nav-mobile">
          <nav class="nav-mobile-inner" aria-label="Мобильное меню">
{mob}
          </nav>
        </div>
      </div>
      <div class="header-glow" aria-hidden="true"></div>
    </header>"""


def footer_html() -> str:
    nav = "\n".join(f'          <a href="/{s}/">{l}</a>' for s, l in NAV)
    return f"""    <footer class="site-footer">
      <div class="container footer-inner">
        <a class="footer-logo" href="/">
          <img src="/logo.svg" alt="Fugu Casino" width="140" height="40" loading="lazy" decoding="async" />
        </a>
        <nav class="footer-nav" aria-label="Нижнее меню">
          <a href="/">Главная</a>
{nav}
        </nav>
        <nav class="footer-trust" aria-label="Правовая информация">
          <span class="footer-badge">18+</span>
          <a href="/responsible-gaming/">Ответственная игра</a>
          <a href="/privacy-policy/">Политика конфиденциальности</a>
          <a href="/terms/">Условия использования</a>
          <a href="/contacts/">Контакты</a>
        </nav>
        <p class="footer-copy">© Fugu Casino / Фугу казино. Информационный гид. Updated: May 2026</p>
      </div>
    </footer>"""


def breadcrumbs_html(home: bool, crumb: str, path: str) -> str:
    if home:
        return '          <nav class="breadcrumbs" aria-label="Хлебные крошки"><span>Главная</span></nav>'
    return f'          <nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="/">Главная</a><span aria-hidden="true">/</span><span>{crumb}</span></nav>'


def hero_trust_row() -> str:
    return """                <ul class="hero-trust-row" aria-label="Надёжность">
                  <li><span class="trust-pill">Updated: May 2026</span></li>
                  <li><span class="trust-pill">18+</span></li>
                  <li><a class="trust-pill trust-pill--link" href="/responsible-gaming/">Ответственная игра</a></li>
                  <li><a class="trust-pill trust-pill--link" href="/contacts/">Контакты</a></li>
                </ul>"""


def toc_html(sections: list[tuple[str, str, list[str]]], practical_h2: str, faq_h2: str) -> str:
    items = [f'              <li><a href="#{sid}">{h2}</a></li>' for h2, sid, _ in sections]
    items.append(f'              <li><a href="#practical">{practical_h2}</a></li>')
    items.append(f'              <li><a href="#faq">{slug_id(faq_h2)}">{faq_h2}</a></li>')
    return f"""      <section class="toc-section">
        <div class="container">
          <nav class="page-toc" aria-label="Содержание страницы">
            <p class="toc-label">Содержание</p>
            <ol>
{chr(10).join(items)}
            </ol>
          </nav>
        </div>
      </section>"""


def sections_html(sections: list[tuple[str, str, list[str]]]) -> str:
    blocks = []
    for h2, sid, paras in sections:
        ps = "\n".join(f"              <p>{p}</p>" for p in paras)
        blocks.append(f'              <h2 id="{sid}">{h2}</h2>\n{ps}')
    return "\n\n".join(blocks)


def practical_html(h2: str, intro: str, tips: list[str], sid: str = "practical") -> str:
    lis = "\n".join(f"                <li>{t}</li>" for t in tips)
    return f"""      <section class="content-section practical-section">
        <div class="container">
          <div class="text-wrap">
            <div class="prose practical-box">
              <h2 id="{sid}">{h2}</h2>
              <p>{intro}</p>
              <ul class="practical-list">
{lis}
              </ul>
            </div>
          </div>
        </div>
      </section>"""


def faq_html(items: list[tuple[str, str]], h2: str) -> str:
    fid = slug_id(h2) or "faq"
    blocks = "\n".join(
        f"""            <details>
              <summary>{q}</summary>
              <p>{a}</p>
            </details>"""
        for q, a in items
    )
    return f"""      <section class="faq-section" id="{fid}">
        <div class="container">
          <div class="text-wrap">
            <h2 id="faq">{h2}</h2>
            <div class="faq">
{blocks}
            </div>
          </div>
        </div>
      </section>"""


def related_block(current: str) -> str:
    links = [f'            <li><a href="/{s}/">{l}</a></li>' for s, l in RELATED if s != current][:6]
    return f"""      <section class="content-section related-section">
        <div class="container">
          <div class="text-wrap">
            <h2>Полезные разделы фугу казино</h2>
            <ul class="related-links">
{chr(10).join(links)}
            </ul>
          </div>
        </div>
      </section>"""


def cta_bottom(title: str, text: str, btn: str, href: str = AFF) -> str:
    rel = ' rel="nofollow sponsored noopener" target="_blank"' if href == AFF else ""
    return f"""      <section class="cta-bottom-section">
        <div class="container">
          <div class="cta-bottom-card">
            <h2>{title}</h2>
            <p>{text}</p>
            <a class="btn-cta btn-cta--lg" href="{href}"{rel}>{btn}</a>
          </div>
        </div>
      </section>"""


def page(slug: str, cfg: dict) -> str:
    path = cfg["path"]
    title = cfg["title"]
    desc = cfg["desc"]
    h1 = cfg["h1"]
    leads = cfg["leads"]
    sections = cfg["sections"]
    practical = cfg["practical"]
    faq = cfg["faq"]
    faq_h2 = cfg["faq_h2"]
    breadcrumb = cfg["breadcrumb"]
    cta = cfg.get("cta", "Перейти")
    cta2 = cfg.get("cta2")
    cta2_label = cfg.get("cta2_label", "Регистрация")
    alt = cfg["alt"]
    home = cfg.get("home", False)
    article = cfg.get("article", True)
    href = cfg.get("cta_href", AFF)
    bhref = cfg.get("banner_href", AFF)
    cta_rel = ' rel="nofollow sponsored noopener" target="_blank"' if href == AFF else ""
    ban_rel = ' rel="nofollow sponsored noopener" target="_blank"' if bhref == AFF else ""
    cta2_html = ""
    if cta2:
        cta2_html = f'\n                  <a class="btn-cta btn-cta--outline" href="{cta2}" rel="nofollow sponsored noopener" target="_blank">{cta2_label}</a>'

    leads_html = "\n".join(f'                <p class="lead">{p}</p>' for p in leads)
    faq_schema = [(q, re.sub(r"<[^>]+>", "", a)) for q, a in faq]

    return f"""<!DOCTYPE html>
<html lang="ru">
  <head>
{head_block(title, desc, path)}
{schema_block(path, title, desc, breadcrumb, faq_schema, article, h1, home)}
  </head>
  <body>
{header_html(None if slug == "index" else slug)}
    <main class="site-main">
      <section class="hero-section">
        <div class="container">
          <div class="hero-grid">
            <div class="hero-col hero-col--text">
              <div class="text-wrap">
{breadcrumbs_html(home, breadcrumb, path)}
                <h1>{h1}</h1>
{leads_html}
{hero_trust_row()}
                <div class="hero-cta-row">
                  <a class="btn-cta" href="{href}"{cta_rel}>{cta}</a>{cta2_html}
                </div>
              </div>
            </div>
            <div class="hero-col hero-col--media">
              <a class="hero-banner-link" href="{bhref}"{ban_rel}>
                <img src="/banner.png" alt="{alt}" width="640" height="360" loading="eager" fetchpriority="high" decoding="async" />
              </a>
            </div>
          </div>
        </div>
      </section>

{toc_html(sections, practical["h2"], faq_h2)}

      <section class="content-section">
        <div class="container">
          <div class="text-wrap">
            <div class="prose">
{sections_html(sections)}
            </div>
          </div>
        </div>
      </section>

{practical_html(practical["h2"], practical["intro"], practical["tips"])}
{faq_html(faq, faq_h2)}
{related_block(slug)}
{cta_bottom(cfg.get("cta_bottom_title", "Готовы начать?"), cfg.get("cta_bottom_text", "Перейдите на Fugu Casino и выберите подходящий раздел."), cta, href)}
    </main>
{footer_html()}
    <script src="/script.js" defer></script>
  </body>
</html>
"""


def word_count_main(html: str) -> int:
    m = re.search(r"<main.*?</main>", html, re.S)
    if not m:
        return 0
    text = re.sub(r"<[^>]+>", " ", m.group())
    return len(re.findall(r"[\wа-яА-ЯёЁ]+", text, re.U))


exec(open(ROOT / "build_content_ru.py", encoding="utf-8").read())


def _plain(p: str) -> str:
    return re.sub(r"<[^>]+>", "", p).strip()


_BOILERPLATE = (
    "Перед переходом на площадку закройте лишние вкладки",
    "Раздел «",
    "гида дополняет главную страницу",
    "Соседние материалы гида дополняют этот",
    "Тема «",
    "важна для тех, кто ищет конкретный ответ",
)


def final_clean_all() -> None:
    for slug in list(PAGES.keys()):
        cfg = PAGES[slug]
        new_secs = []
        for h2, sid, paras in cfg["sections"]:
            seen: set[str] = set()
            kept = []
            for p in paras:
                t = _plain(p)
                if not t or t in seen:
                    continue
                if any(m in t for m in _BOILERPLATE):
                    continue
                seen.add(t)
                kept.append(p)
            new_secs.append((h2, sid, kept))
        cfg["sections"] = new_secs


def main() -> None:
    generate_favicons()
    final_clean_all()
    for _slug in list(PAGES.keys()):
        apply_wording(_slug)
    for slug, cfg in PAGES.items():
        fname = "index.html" if slug == "index" else f"{slug}.html"
        html = page(slug, cfg)
        wc = word_count_main(html)
        (ROOT / fname).write_text(html, encoding="utf-8")
        print(f"wrote {fname} ({wc} words in main)")


if __name__ == "__main__":
    main()
