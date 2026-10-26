#!/usr/bin/env python3
"""viotours.in static site builder.

    python3 build.py            # writes the site to ./dist
    python3 build.py --serve    # builds, then serves ./dist on http://localhost:8000

Stdlib only. Content lives in content/*.json; shared look in css/site.css; behaviour in js/.
Edit content, rebuild, rsync dist/ to the server.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE_URL = "https://www.viotours.in"
TODAY = dt.date.today()

# Shows a thin banner on every page while packages/prices are placeholders. Set False at launch.
SAMPLE_CONTENT = True

esc = html.escape


# ---------------------------------------------------------------- helpers
def load(name: str) -> dict:
    return json.loads((ROOT / "content" / name).read_text(encoding="utf-8"))


_icon_cache: dict[str, str] = {}


def icon(name: str, cls: str = "icon") -> str:
    """Inline one of the 23 design-system icons so it takes currentColor."""
    if name not in _icon_cache:
        svg = (ROOT / "assets" / "icons" / f"{name}.svg").read_text(encoding="utf-8")
        inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
        inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
        _icon_cache[name] = inner
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{_icon_cache[name]}</svg>'


def check_icon(cls: str = "icon icon--sm") -> str:
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'


def cross_icon(cls: str = "icon icon--sm") -> str:
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg>'


def inr(n: int) -> str:
    """Indian digit grouping: 248000 -> 2,48,000."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


_logo_n = 0


def logo_svg() -> str:
    """Inline the pin-and-orbit mark; gradient ids are made unique so header and footer copies don't clash."""
    global _logo_n
    _logo_n += 1
    svg = (ROOT / "assets" / "img" / "logo-mark.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<title>.*?</title>", "", svg, flags=re.S)
    svg = svg.replace('role="img" aria-label="viotours"', 'aria-hidden="true" focusable="false"')
    for gid in ("g", "p", "n", "front"):
        svg = svg.replace(f'id="{gid}"', f'id="{gid}{_logo_n}"').replace(f"url(#{gid})", f"url(#{gid}{_logo_n})")
    return svg


def kolam(x: int, y: int, cols: int = 5, rows: int = 4, pitch: int = 24) -> str:
    dots = "".join(
        f'<circle cx="{c * pitch + (r % 2) * pitch // 2}" cy="{r * pitch}" r="2.5"/>'
        for r in range(rows) for c in range(cols - (r % 2))
    )
    w, h = cols * pitch, rows * pitch
    return (f'<svg class="kolam" style="left:{x}px;top:{y}px" width="{w}" height="{h}" '
            f'viewBox="-4 -4 {w} {h}" fill="currentColor" aria-hidden="true">{dots}</svg>')


# ---------------------------------------------------------------- illustrated scenes
# Placeholders for photography, drawn in brand inks. Set "image" in packages.json to replace.
SCENES = {
    "alps": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="244" cy="54" r="22" fill="var(--accent)"/>
<path d="M0 200 L70 92 L112 140 L168 58 L236 150 L280 108 L320 150 L320 200Z" fill="var(--brand)"/>
<path d="M70 92 L86 116 L76 112 L64 120Z M168 58 L188 88 L176 82 L168 92 L158 80 L150 86Z M280 108 L292 124 L278 120 L270 124Z" fill="var(--surface-raised)"/>
<path d="M0 200 L60 160 L120 184 L200 150 L320 196 L320 200Z" fill="var(--brand-strong)"/>
<path d="M18 176 h80" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 6"/>""",
    "tropics": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="96" cy="70" r="26" fill="var(--accent)"/>
<path d="M0 140 Q160 120 320 140 L320 200 L0 200Z" fill="var(--brand)"/><path d="M0 164 Q160 150 320 166 L320 200 L0 200Z" fill="var(--brand-strong)"/>
<path d="M232 150 Q236 100 226 64" stroke="var(--ink)" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="M226 64 q-30 -6 -48 12 M226 64 q-14 -26 -38 -24 M226 64 q24 -22 46 -12 M226 64 q34 2 46 22 M226 64 q6 -28 -4 -40" stroke="var(--brand-strong)" stroke-width="6" fill="none" stroke-linecap="round"/>""",
    "balloons": """<rect width="320" height="200" fill="var(--surface-sunk)"/>
<path d="M0 200 L0 150 Q40 120 80 150 Q120 110 170 150 Q220 118 260 146 Q292 128 320 140 L320 200Z" fill="var(--brand)"/>
<path d="M0 200 L0 176 Q80 156 160 178 Q240 160 320 176 L320 200Z" fill="var(--brand-strong)"/>
<g><ellipse cx="96" cy="60" rx="24" ry="28" fill="var(--accent)"/><path d="M84 84 L90 98 h12 L108 84" stroke="var(--ink)" stroke-width="1.5" fill="none"/><rect x="89" y="98" width="14" height="9" rx="2" fill="var(--ink)"/></g>
<g><ellipse cx="214" cy="44" rx="16" ry="19" fill="var(--brand)"/><rect x="209" y="70" width="10" height="7" rx="2" fill="var(--ink)"/><path d="M206 60 L210 70 M222 60 L218 70" stroke="var(--ink)" stroke-width="1.2"/></g>
<g><ellipse cx="266" cy="92" rx="11" ry="13" fill="var(--accent)"/><rect x="263" y="109" width="7" height="5" rx="1.5" fill="var(--ink)"/></g>""",
    "ocean": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="232" cy="78" r="30" fill="var(--accent)"/>
<path d="M0 118 H320 V200 H0Z" fill="var(--brand)"/><path d="M0 150 Q80 140 160 152 T320 150 V200 H0Z" fill="var(--brand-strong)"/>
<g fill="var(--surface-raised)"><path d="M54 104 L84 86 L114 104Z"/><rect x="60" y="104" width="48" height="12"/></g>
<g stroke="var(--surface-raised)" stroke-width="2"><path d="M66 116 V134 M84 116 V136 M102 116 V134 M84 136 H200"/></g>
<g fill="var(--surface-raised)"><path d="M150 106 L172 92 L194 106Z"/><rect x="156" y="106" width="34" height="10"/></g>""",
    "temple": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="76" cy="58" r="22" fill="var(--accent)"/>
<path d="M0 200 L0 166 Q160 150 320 166 L320 200Z" fill="var(--brand-strong)"/>
<g fill="var(--brand)"><path d="M168 54 h64 l-12 -12 h-40z"/><rect x="186" y="54" width="28" height="18"/><path d="M160 86 h80 l-14 -14 h-52z"/><rect x="180" y="86" width="40" height="20"/><path d="M152 120 h96 l-16 -16 h-64z"/><rect x="174" y="120" width="52" height="40"/></g>
<g fill="var(--accent)" opacity=".9"><circle cx="40" cy="120" r="6"/><circle cx="52" cy="112" r="5"/><circle cx="58" cy="126" r="6"/><circle cx="272" cy="112" r="6"/><circle cx="284" cy="104" r="5"/><circle cx="290" cy="120" r="6"/></g>
<path d="M50 166 V126 M282 166 V118" stroke="var(--ink)" stroke-width="3"/>""",
    "desert": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="160" cy="84" r="34" fill="var(--accent)"/>
<path d="M0 200 L0 140 Q80 104 170 140 Q240 116 320 132 L320 200Z" fill="var(--brand)"/>
<path d="M0 200 L0 172 Q100 146 200 170 Q270 156 320 166 L320 200Z" fill="var(--brand-strong)"/>
<g fill="var(--ink)"><rect x="232" y="40" width="5" height="96"/><path d="M228 40 L234.5 12 L241 40Z"/></g>""",
    "himalaya": """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="66" cy="50" r="20" fill="var(--accent)"/>
<path d="M0 200 L40 120 L90 160 L150 64 L210 150 L260 96 L320 160 L320 200Z" fill="var(--brand)"/>
<path d="M150 64 L172 98 L160 92 L150 102 L140 90 L130 96Z M260 96 L276 120 L262 116 L250 120Z" fill="var(--surface-raised)"/>
<path d="M0 200 L0 180 Q160 160 320 184 L320 200Z" fill="var(--brand-strong)"/>
<path d="M20 70 Q90 96 170 40" stroke="var(--ink)" stroke-width="1" fill="none"/>
<g><rect x="40" y="74" width="8" height="10" fill="var(--accent)"/><rect x="66" y="80" width="8" height="10" fill="var(--brand)"/><rect x="92" y="80" width="8" height="10" fill="var(--surface-raised)"/><rect x="118" y="72" width="8" height="10" fill="var(--accent)"/><rect x="144" y="58" width="8" height="10" fill="var(--brand)"/></g>""",
}


def media(pkg: dict, alt: bool = False) -> str:
    if pkg.get("image"):
        alt = pkg["title"]
        src = ROOT / pkg["image"]
        if src.suffix == ".svg" and src.exists():  # illustrated scene: use its <title> as the description
            m = re.search(r"<title>(.*?)</title>", src.read_text(encoding="utf-8"), re.S)
            alt = "Illustration: " + m.group(1) if m else alt
        return f'<img src="/{esc(pkg["image"])}" alt="{esc(alt)}" width="800" height="500" loading="lazy">'
    body = SCENES.get(pkg.get("scene", ""), SCENES["alps"])
    return f'<svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">{body}</svg>'


SCENES["fjord"] = """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="252" cy="46" r="18" fill="var(--accent)"/>
<path d="M0 200 L0 60 L40 40 L78 120 L96 200Z" fill="var(--brand)"/><path d="M320 200 L320 50 L268 72 L236 128 L214 200Z" fill="var(--brand)"/>
<path d="M150 150 L176 70 L200 150Z" fill="var(--brand-strong)"/><path d="M176 70 L186 98 L176 92 L168 100Z" fill="var(--surface-raised)"/>
<path d="M60 160 Q160 150 260 160 L270 200 L50 200Z" fill="var(--brand-strong)"/>
<path d="M118 170 h44 l-6 7 h-34z" fill="var(--surface-raised)"/><path d="M130 170 v-8 h14 v8" fill="var(--surface-raised)"/>
<path d="M40 40 Q46 90 44 132" stroke="var(--surface-raised)" stroke-width="2" fill="none" opacity=".7"/>"""
SCENES["meghalaya"] = """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="70" cy="44" r="18" fill="var(--accent)"/>
<path d="M0 120 Q60 70 120 104 Q170 60 220 96 Q270 70 320 100 L320 200 L0 200Z" fill="var(--brand)"/>
<path d="M196 90 C200 120 198 140 204 160" stroke="var(--surface-raised)" stroke-width="6" fill="none" stroke-linecap="round" opacity=".9"/>
<path d="M0 150 Q160 138 320 152 L320 200 L0 200Z" fill="#7fb3ad"/><path d="M0 172 Q160 164 320 174 L320 200 L0 200Z" fill="#5f9690"/>
<g fill="var(--brand-strong)"><path d="M118 160 q22 6 44 0 l-4 5 h-36z"/><path d="M136 160 l4 -10 h6 l4 10z"/></g>
<path d="M120 170 q20 4 40 0" stroke="var(--brand-strong)" stroke-width="1" fill="none" opacity=".35"/>
<path d="M60 186 h6 M84 182 h4 M240 184 h8" stroke="var(--brand-strong)" stroke-width="1.5" opacity=".4"/>"""
SCENES["silkroad"] = """<rect width="320" height="200" fill="var(--surface-sunk)"/><circle cx="262" cy="44" r="20" fill="var(--accent)"/>
<rect x="0" y="172" width="320" height="28" fill="var(--brand-strong)"/>
<g fill="var(--brand)"><rect x="40" y="76" width="16" height="96"/><path d="M38 76 h20 l-3 -8 h-14z"/><rect x="264" y="76" width="16" height="96"/><path d="M262 76 h20 l-3 -8 h-14z"/>
<rect x="96" y="96" width="128" height="76"/><path d="M128 96 a32 32 0 0 1 64 0z"/></g>
<path d="M144 172 v-44 a16 16 0 0 1 32 0 v44z" fill="var(--accent)"/><path d="M152 172 v-36 a8 8 0 0 1 16 0 v36z" fill="var(--brand-strong)"/>
<g fill="var(--accent)"><rect x="96" y="108" width="128" height="4"/><rect x="40" y="96" width="16" height="3"/><rect x="264" y="96" width="16" height="3"/><rect x="40" y="120" width="16" height="3"/><rect x="264" y="120" width="16" height="3"/></g>
<path d="M160 64 a4 4 0 1 0 0.1 0" fill="var(--accent)"/>"""


HERO_ART = """<svg viewBox="0 0 500 540" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<rect width="500" height="540" fill="var(--surface-sunk)"/>
<circle cx="360" cy="120" r="56" fill="var(--accent)"/>
<path d="M0 540 L0 360 L110 220 L190 300 L290 170 L400 300 L460 250 L500 290 L500 540Z" fill="var(--brand)"/>
<path d="M110 220 L134 254 L120 248 L106 262 L94 246Z M290 170 L322 214 L304 206 L290 222 L276 204 L262 212Z" fill="var(--surface-raised)"/>
<path d="M0 540 L0 430 Q130 380 250 430 Q380 384 500 420 L500 540Z" fill="var(--brand-strong)"/>
<path d="M40 470 Q220 300 420 380" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-dasharray="4 8" stroke-linecap="round"/>
<g transform="translate(150 88)"><ellipse cx="0" cy="0" rx="34" ry="40" fill="var(--brand)"/><path d="M-12 -38 Q-4 0 -6 36 M12 -38 Q4 0 6 36" stroke="var(--accent)" stroke-width="3" fill="none"/><path d="M-18 34 L-8 54 M18 34 L8 54" stroke="var(--ink)" stroke-width="2"/><rect x="-10" y="54" width="20" height="14" rx="3" fill="var(--ink)"/></g>
<g fill="var(--accent)" opacity=".8"><circle cx="40" cy="40" r="3"/><circle cx="64" cy="40" r="3"/><circle cx="88" cy="40" r="3"/><circle cx="52" cy="64" r="3"/><circle cx="76" cy="64" r="3"/><circle cx="64" cy="88" r="3"/></g>
</svg>"""


# ---------------------------------------------------------------- layout
NAV = [("Home", "/"), ("Packages", "/packages.html"), ("Events", "/events.html"),
       ("Journal", "/blog.html"), ("About", "/about.html"), ("Contact", "/contact.html")]

STYLES = [
    ("luxury", "Luxury escapes", "hotel", "Hand-picked stays and private transfers, without the fuss."),
    ("adventure", "Adventure & thrill", "paragliding", "Balloons, high passes and wild water, with licensed operators only."),
    ("honeymoon", "Honeymoons", "partner", "Just the two of you. We handle every detail quietly."),
    ("family", "Family gatherings", "family", "Three generations, one pace. Reunions, weddings, milestones."),
    ("snow", "Snow mountains", "trail", "First snow or fiftieth: Alps, Himalaya and beyond."),
]
STYLE_NAMES = {k: n for k, n, _, _ in STYLES}

ACTIVITIES = [
    ("kayak", "Kayaking"), ("cruise", "Cruises"), ("trail", "Mountain trails"), ("cycling", "Cycling"),
    ("motorbike", "Bike tours"), ("paragliding", "Paragliding"), ("balloon", "Hot-air balloon"),
    ("bus", "Coach tours"), ("car", "Self-drive"),
]


def page(*, path: str, title: str, desc: str, body: str, nav: str = "", noindex: bool = False) -> None:
    full_title = "viotours — " + title if title else "viotours — private guided journeys for families and groups"
    nav_html = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if label == nav else ""}>{label}</a>' for label, href in NAV
    )
    banner = ('<div class="preview-bar">Preview site — packages, dates and prices shown are samples, '
              'not live offers.</div>') if SAMPLE_CONTENT else ""
    canonical = SITE_URL + ("/" if path == "index.html" else "/" + path)
    doc = f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:type" content="website">
<meta property="og:site_name" content="viotours">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/img/og-image.jpg">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#1c2a44">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/CormorantGaramond-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Jost-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{banner}
<header class="site-header">
  <div class="container site-header__inner">
    <a class="logo" href="/" aria-label="viotours home">{logo_svg()}<span class="logo__word">vio<b>tours</b></span></a>
    <nav class="nav" aria-label="Main">{nav_html}<a class="btn btn--primary nav__cta" href="/enquire.html">Plan my trip</a></nav>
    <a class="btn btn--primary header-cta" href="/enquire.html">Plan my trip</a>
    <button class="menu-btn" aria-expanded="false" aria-label="Menu"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a class="logo" href="/" aria-label="viotours home">{logo_svg()}<span class="logo__word">vio<b>tours</b></span></a>
        <p class="footer-about">Private, guided journeys for families and small groups of 6 to 15. Planned by a person, led by a vetted guide, priced fairly.</p>
      </div>
      <div><h4>Explore</h4><ul>
        <li><a href="/packages.html">All packages</a></li>
        <li><a href="/packages.html?style=honeymoon">Honeymoons</a></li>
        <li><a href="/packages.html?style=snow">Snow mountains</a></li>
        <li><a href="/packages.html?style=adventure">Adventure</a></li>
        <li><a href="/events.html">Events</a></li>
      </ul></div>
      <div><h4>viotours</h4><ul>
        <li><a href="/about.html">About and safety</a></li>
        <li><a href="/blog.html">Journal</a></li>
        <li><a href="/partners.html">Partner with us</a></li>
        <li><a href="/contact.html">Contact</a></li>
      </ul></div>
      <div><h4>Talk to a planner</h4><ul>
        <li><a data-wa="Hello viotours, I'd like help planning a trip." href="#" target="_blank" rel="noopener">WhatsApp</a></li>
        <li><a data-email href="#"></a></li>
        <li>Chennai · Ras Al Khaimah</li>
        <li>24×7 helpline while you travel</li>
      </ul></div>
    </div>
    <div class="footer-base"><span>© <span data-year>{TODAY.year}</span> viotours.in</span><span>Prices are per person and list what is included.</span></div>
  </div>
</footer>
<button class="music" type="button" aria-pressed="false" aria-label="Play theme music">{icon("music")}<span class="music__bars" aria-hidden="true"><i></i><i></i><i></i></span><span class="music__label">Play music</span></button>
<audio id="bgm" preload="auto"><source src="/assets/audio/povoma-oorgolam-bgm.webm" type="audio/webm"><source src="/assets/audio/povoma-oorgolam-bgm.mp3" type="audio/mpeg"></audio>
<a class="wa" data-wa="Hello viotours, I'd like help planning a trip." href="#" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">{icon("contact")}<span class="wa__label">WhatsApp us</span></a>
<script src="/js/config.js"></script>
<script src="/js/site.js" defer></script>
</body>
</html>
"""
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    PAGES.append((path, noindex))


PAGES: list[tuple[str, bool]] = []


# ---------------------------------------------------------------- components
def package_card(p: dict, heading: str = "h3") -> str:
    chips = (f'<span class="chip">{icon("events", "icon icon--sm")}{p["nights"]} nights</span>'
             f'<span class="chip">{icon("family", "icon icon--sm")}{esc(p["group"])}</span>'
             f'<span class="chip">{icon("guide", "icon icon--sm")}Guide included</span>' + level_chip(p))
    tags = p['styles'] + (['india'] if p.get('region') == 'India' else [])
    return f"""<article class="card" data-styles="{' '.join(tags)}" data-activities="{' '.join(p['activities'])}">
  <div class="card__media">{media(p)}<span class="card__flag badge badge--gold">{icon("family", "icon icon--sm")}{esc(p['flag'])}</span></div>
  <div class="card__body">
    <span class="eyebrow">{esc(p['departure'])}</span>
    <{heading} class="card__title"><a href="/packages/{p['slug']}.html">{esc(p['title'])}</a></{heading}>
    <p class="card__places">{esc(p['places'])}</p>
    <div class="card__meta">{chips}</div>
    <div class="card__foot">{price_html(p)}
    <a class="btn btn--accent btn--sm" href="/enquire.html?package={p['slug']}">Request trip</a></div>
  </div>
</article>"""


def level_chip(p: dict) -> str:
    if not p.get("level"):
        return ""
    return f'<span class="chip chip--level">{icon("trail", "icon icon--sm")}Adventure level: {esc(p["level"])}</span>'


def price_html(p: dict) -> str:
    if p.get("price_inr"):
        return f'<div class="price">₹&#8201;{inr(p["price_inr"])}<small>{esc(p["price_basis"])}</small></div>'
    return f'<div class="price price--ask">Price on request<small>{esc(p.get("price_basis") or "per person, quoted for your group")}</small></div>'


def newsletter_band() -> str:
    return f"""<section class="section section--sunk"><div class="container cta-band">
  <div><span class="eyebrow">Newsletter</span><h2 class="her-h2" style="margin-top:12px">New departures, once a month</h2>
  <p class="lead" style="margin:12px 0 0">Small-group dates, visa reminders and the occasional travel story. No daily emails.</p></div>
  <form class="form" data-form="newsletter" data-ok="You're on the list. Look out for our next note.">
    <label class="sr-only" for="nl-email">Email address</label>
    <div class="inline-form"><input id="nl-email" type="email" name="email" placeholder="you@example.com" required autocomplete="email">
    <button class="btn btn--primary" type="submit">Subscribe</button></div>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="sr-only" aria-hidden="true">
    <div class="form-status" aria-live="polite"></div>
  </form>
</div></section>"""


def fmt_date(d: str) -> dt.date:
    return dt.date.fromisoformat(d)


# ---------------------------------------------------------------- pages
def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for d in ("css", "js", "assets"):
        shutil.copytree(ROOT / d, DIST / d)
    PAGES.clear()

    pkgs = [p for p in load("packages.json")["packages"] if p.get("active")]
    featured = sorted([p for p in pkgs if p.get("featured")], key=lambda p: p.get("position", 99))[:3]
    events = sorted([e for e in load("events.json")["events"] if fmt_date(e["date"]) >= TODAY], key=lambda e: e["date"])
    posts = sorted(load("posts.json")["posts"], key=lambda p: p["date"], reverse=True)

    # ---------- home
    style_tiles = "".join(
        f'<a class="style-tile" href="/packages.html?style={k}">{icon(ic)}<h3>{n}</h3><p>{esc(t)}</p></a>'
        for k, n, ic, t in STYLES)
    activity_tiles = "".join(
        f'<a class="activity" href="/packages.html?activity={k}">{icon(k)}{n}</a>' for k, n in ACTIVITIES)
    event_rows = "".join(event_row(e) for e in events[:2]) or '<p class="muted">New events are announced here first.</p>'
    home = f"""
<section class="hero">
  {kolam(-20, 24, 6, 4)}
  <div class="container hero__grid">
    <div>
      <span class="eyebrow">Private, guided journeys · groups of 6 to 15</span>
      <h1 class="her-hero">Travel together, come home closer</h1>
      <p class="lead">Luxury escapes, honeymoons, family gatherings, snow mountains and a little adventure. Planned by a person, led by a vetted guide, at a price we can show is fair.</p>
      <div class="hero__actions"><a class="btn btn--primary btn--lg" href="/enquire.html">Plan my trip</a><a class="btn btn--secondary btn--lg" href="/packages.html">See packages</a></div>
      <div class="hero__trust">
        <span>{icon("safety", "icon icon--sm")}24×7 India + destination helpline</span>
        <span>{icon("safety", "icon icon--sm")}Insured</span>
        <span>{icon("safety", "icon icon--sm")}Guides background-checked</span>
      </div>
    </div>
    <div class="hero__art hero__art--brand"><img src="/assets/img/hero-brand.jpg" width="1024" height="1024" alt="The viotours pin with a compass star, ringed by an orbit, beside a vintage globe. Bringing travel to life." fetchpriority="high"></div>
  </div>
</section>

<section class="section section--sunk" aria-labelledby="featured-h">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Featured departures</span><h2 class="her-h2" id="featured-h">Three journeys we love right now</h2></div>
    <a class="btn btn--ghost" href="/packages.html">All packages →</a></div>
    <div class="grid-3">{''.join(package_card(p) for p in featured)}</div>
  </div>
</section>

<section class="section" aria-labelledby="styles-h">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Ways to travel</span><h2 class="her-h2" id="styles-h">What kind of trip is it?</h2>
    <p class="lead">Every itinerary is built around who is coming. Start with the feeling you want, and we'll shape the rest.</p></div></div>
    <div class="styles">{style_tiles}</div>
  </div>
</section>

<section class="section section--brand" aria-labelledby="promise-h">
  <div class="container promise">
    <div><span class="eyebrow">Our promise</span><h2 class="her-h2" id="promise-h" style="margin-top:12px">Looked after, from the first call to the flight home</h2>
    <p class="lead" style="margin-top:16px">We are a direct agency, not a booking website. One planner owns your trip, and one guide travels with your group.</p>
    <a class="btn btn--on-brand" href="/about.html">How we keep you safe</a></div>
    <div class="promise__list">
      <div class="promise__item">{icon("guide")}<div><h3>A guide with your group</h3><p>Background-checked, briefed on every traveller, with you on the ground.</p></div></div>
      <div class="promise__item">{icon("safety")}<div><h3>Insured and supported</h3><p>Travel insurance included. A 24×7 helpline in India and at your destination.</p></div></div>
      <div class="promise__item">{icon("family")}<div><h3>Small groups only</h3><p>6 to 15 travellers, or your own private family group.</p></div></div>
      <div class="promise__item">{icon("compare")}<div><h3>Prices you can check</h3><p>Per person, with what is included written out. No hidden extras.</p></div></div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="how-h">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">How it works</span><h2 class="her-h2" id="how-h">Four steps, one point of contact</h2></div></div>
    <div class="steps">
      <div class="step"><h3>Tell us who's coming</h3><p>Ages, interests, food, mobility, the dates that work. A five-minute form or a WhatsApp message.</p></div>
      <div class="step"><h3>Get a plan in 48 hours</h3><p>A planner sends a day-by-day itinerary and a per-person price with everything listed.</p></div>
      <div class="step"><h3>Shape it together</h3><p>Change the pace, swap a hotel, add a surprise. We handle visas and paperwork with you.</p></div>
      <div class="step"><h3>Travel looked-after</h3><p>Your guide meets you at arrivals. The helpline is open around the clock.</p></div>
    </div>
  </div>
</section>

<section class="section section--sunk" aria-labelledby="act-h">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Adventures</span><h2 class="her-h2" id="act-h">Something to talk about at home</h2>
    <p class="lead">Every activity runs with licensed operators, and we keep a spare day for the weather.</p></div></div>
    <div class="activities">{activity_tiles}</div>
  </div>
</section>

<section class="section" aria-labelledby="ev-h">
  <div class="container">
    <div class="section-head"><div><span class="eyebrow">Events</span><h2 class="her-h2" id="ev-h">Meet us before you travel</h2></div>
    <a class="btn btn--ghost" href="/events.html">All events →</a></div>
    {event_rows}
  </div>
</section>
{newsletter_band()}
"""
    page(path="index.html", title="", nav="Home", body=home,
         desc="viotours plans private, guided journeys for families and small groups of 6 to 15: luxury escapes, honeymoons, family gatherings, snow mountains and adventure.")

    # ---------- packages list
    style_filters = '<button class="filter" data-filter-style="all" aria-pressed="true">All trips</button>' + "".join(
        f'<button class="filter" data-filter-style="{k}" aria-pressed="false">{n}</button>' for k, n, _, _ in STYLES)
    style_filters += '<button class="filter" data-filter-style="india" aria-pressed="false">India</button>'
    act_filters = "".join(
        f'<button class="activity" data-filter-activity="{k}" aria-pressed="false">{icon(k)}{n}</button>' for k, n in ACTIVITIES)
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Packages</span><h1 class="her-hero">Active journeys</h1>
  <p class="lead">Every package can be run privately for your family or group. Prices are per person and list exactly what is included.</p>
</div></section>
<section class="section"><div class="container">
  <div class="filters" role="group" aria-label="Trip style">{style_filters}</div>
  <details class="mt-6" style="margin:0 0 32px"><summary class="label" style="cursor:pointer">Filter by activity</summary>
    <div class="activities" style="margin-top:16px" role="group" aria-label="Activity">{act_filters}</div></details>
  <div class="grid-3" data-filter-grid>{''.join(package_card(p, "h2") for p in pkgs)}</div>
  <div class="empty" data-empty hidden><p>No package matches both filters yet.</p><a class="btn btn--primary" href="/enquire.html">Ask us to plan one</a></div>
  <p class="note center mt-6">Don't see your destination? <a href="/enquire.html">Tell us where you'd like to go</a> and we'll plan it from scratch.</p>
</div></section>
{newsletter_band()}"""
    page(path="packages.html", title="Packages", nav="Packages", body=body,
         desc="Active viotours packages: snow mountains, honeymoons, family gatherings, luxury escapes and adventure, for private groups of 6 to 15.")

    # ---------- package detail
    for p in pkgs:
        days = "".join(f'<li><span class="day">{esc(d)}</span><div><h3>{esc(t)}</h3><p>{esc(x)}</p></div></li>'
                       for d, t, x in p["itinerary"])
        inc = "".join(f'<li>{check_icon()}<span>{esc(x)}</span></li>' for x in p["includes"])
        exc = "".join(f'<li>{cross_icon()}<span>{esc(x)}</span></li>' for x in p["excludes"])
        styles = " · ".join(STYLE_NAMES[s] for s in p["styles"])
        acts = "".join(f'<span class="chip">{icon(a, "icon icon--sm")}{dict(ACTIVITIES)[a]}</span>' for a in p["activities"])
        body = f"""
<section><div class="container" style="padding-top:32px">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/packages.html">Packages</a> / {esc(p['title'])}</nav>
  <span class="eyebrow">{esc(p['departure'])}</span>
  <h1 class="her-hero" style="margin-top:12px">{esc(p['title'])}</h1>
  <p class="lead" style="margin:12px 0 0">{esc(p['places'])}</p>
  <div class="pkg-hero">{media(p)}</div>
</div></section>
<section class="section"><div class="container pkg-layout">
  <div>
    <p class="lead" style="color:var(--ink)">{esc(p['summary'])}</p>
    <div class="pkg-facts">
      <span class="chip">{icon("events", "icon icon--sm")}{p['nights']} nights</span>
      <span class="chip">{icon("family", "icon icon--sm")}{esc(p['group'])}</span>
      <span class="chip">{icon("guide", "icon icon--sm")}Guide included</span>
      <span class="chip">{icon("safety", "icon icon--sm")}Insured</span>{level_chip(p)}{acts}
    </div>
    <div class="pkg-mobile-cta">{price_html(p)}
      <a class="btn btn--accent" href="/enquire.html?package={p['slug']}">Request this trip</a></div>
    <h2 class="her-h2" style="margin:24px 0 16px">Day by day</h2>
    <ol class="itinerary">{days}</ol>
    <h2 class="her-h2" style="margin:56px 0 24px">What's included</h2>
    <div class="incl"><div class="yes"><h3 class="label" style="margin-bottom:12px">Included</h3><ul>{inc}</ul></div>
    <div class="no"><h3 class="label" style="margin-bottom:12px">Not included</h3><ul>{exc}</ul></div></div>
    {f'<p class="note mt-6"><strong>Good to know:</strong> {esc(p["note"])}</p>' if p.get("note") else ""}
    <p class="note mt-6">Every itinerary can be adjusted for your group's pace, food and mobility. Activities run with licensed operators, weather permitting.</p>
  </div>
  <aside class="book-panel" aria-label="Request this trip">
    {('<span class="eyebrow">From</span>' + price_html(p) + f'<span class="fx" data-inr="{p["price_inr"]}"></span>') if p.get("price_inr") else price_html(p)}
    <dl>
      <div><dt>Duration</dt><dd>{p['nights']} nights</dd></div>
      <div><dt>Group</dt><dd>{esc(p['group'])}</dd></div>
      <div><dt>Style</dt><dd>{esc(styles)}</dd></div>
    </dl>
    <a class="btn btn--accent btn--lg" href="/enquire.html?package={p['slug']}">Request this trip</a>
    <a class="btn btn--secondary" data-wa="Hello viotours, I'm interested in {esc(p['title'])}." href="#" target="_blank" rel="noopener">{icon("contact")}Ask on WhatsApp</a>
    <p class="note" style="margin:0">No payment now. A planner confirms availability and the final price with you.</p>
  </aside>
</div></section>"""
        page(path=f"packages/{p['slug']}.html", title=p["title"], nav="Packages", body=body,
             desc=f"{p['title']}: {p['summary']}")

    # ---------- enquiry
    opts = '<option value="">Not sure yet — help me choose</option>' + "".join(
        f'<option value="{p["slug"]}">{esc(p["title"])}</option>' for p in pkgs)
    style_pills = "".join(
        f'<label class="pill"><input type="checkbox" name="trip_style" value="{n}"><span>{n}</span></label>'
        for _, n, _, _ in STYLES)
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Plan my trip</span><h1 class="her-hero">Tell us who's coming</h1>
  <p class="lead">A planner replies within one working day with questions or a first itinerary. There's no payment and no obligation.</p>
</div></section>
<section class="section"><div class="container" style="max-width:820px">
  <form class="form panel" data-form="trip-request" data-ok="Thank you. A viotours planner will reply within one working day, usually on WhatsApp.">
    <div class="field"><label for="enq-package">Package</label><select id="enq-package" name="package">{opts}</select></div>
    <fieldset class="field"><legend>What kind of trip?</legend><div class="pills">{style_pills}</div></fieldset>
    <div class="form-row">
      <div class="field"><label for="enq-dest">Where would you like to go?</label><input id="enq-dest" type="text" name="destination" placeholder="e.g. Switzerland, or 'somewhere with snow'"></div>
      <div class="field"><label for="enq-when">When?</label><input id="enq-when" type="text" name="dates" placeholder="e.g. late December, 8–10 nights"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="enq-adults">Adults</label><input id="enq-adults" type="number" name="adults" min="1" max="15" value="2" required></div>
      <div class="field"><label for="enq-kids">Children and their ages</label><input id="enq-kids" type="text" name="children" placeholder="e.g. 2 — ages 4 and 9"></div>
    </div>
    <div class="field"><label for="enq-notes">Anything we should plan around?</label><textarea id="enq-notes" name="notes" placeholder="Food (vegetarian, Jain), mobility, a birthday or anniversary, budget per person…"></textarea></div>
    <hr class="rule" style="margin:8px 0">
    <div class="form-row">
      <div class="field"><label for="enq-name">Your name</label><input id="enq-name" type="text" name="name" required autocomplete="name"></div>
      <div class="field"><label for="enq-phone">Phone or WhatsApp</label><input id="enq-phone" type="tel" name="phone" required autocomplete="tel" placeholder="+91 or +971"></div>
    </div>
    <div class="field"><label for="enq-email">Email</label><input id="enq-email" type="email" name="email" required autocomplete="email"></div>
    <label class="check"><input type="checkbox" name="consent" value="yes" required><span>You may contact me about this trip by phone, WhatsApp or email.</span></label>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="sr-only" aria-hidden="true">
    <div class="form-status" aria-live="polite"></div>
    <div><button class="btn btn--primary btn--lg" type="submit">Send my request</button></div>
  </form>
</div></section>"""
    page(path="enquire.html", title="Plan my trip", body=body,
         desc="Tell viotours who's travelling and what you'd like. A planner replies within one working day.")

    # ---------- events
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Events</span><h1 class="her-hero">Meet us before you travel</h1>
  <p class="lead">Small evenings and online sessions where you can meet the planners and guides, and ask anything.</p>
</div></section>
<section class="section"><div class="container">{''.join(event_row(e) for e in events) or '<div class="empty">No upcoming events right now. Subscribe below and we will tell you first.</div>'}</div></section>
{newsletter_band()}"""
    page(path="events.html", title="Events", nav="Events", body=body,
         desc="viotours events: trip briefings, honeymoon planning sessions and meet-ups in Chennai, online and the UAE.")

    # ---------- blog
    cards = "".join(
        f'<article class="post-card"><span class="eyebrow">{fmt_date(x["date"]).strftime("%-d %b %Y")}</span>'
        f'<h2 class="her-h3" style="font-size:22px;line-height:28px"><a href="/blog/{x["slug"]}.html" style="color:var(--ink);text-decoration:none">{esc(x["title"])}</a></h2>'
        f'<p>{esc(x["excerpt"])}</p><span class="label" style="color:var(--brand)">Read →</span></article>'
        for x in posts)
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Journal</span><h1 class="her-hero">Notes from the road</h1>
  <p class="lead">Practical advice from our planners and guides on travelling well together.</p>
</div></section>
<section class="section"><div class="container grid-3">{cards}</div></section>
{newsletter_band()}"""
    page(path="blog.html", title="Journal", nav="Journal", body=body,
         desc="The viotours journal: practical advice on family, honeymoon, snow and adventure travel.")
    for x in posts:
        body = f"""
<section class="page-head"><div class="container" style="max-width:820px">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/blog.html">Journal</a></nav>
  <span class="eyebrow">{fmt_date(x["date"]).strftime("%-d %B %Y")}</span><h1 class="her-hero" style="font-size:clamp(34px,5vw,52px);line-height:1.12">{esc(x['title'])}</h1>
  <p class="lead">{esc(x['excerpt'])}</p>
</div></section>
<section class="section"><div class="container" style="max-width:820px"><article class="prose">{x['body']}</article>
<hr class="rule"><a class="btn btn--primary" href="/enquire.html">Plan my trip</a> <a class="btn btn--ghost" href="/blog.html">More from the journal</a></div></section>"""
        page(path=f"blog/{x['slug']}.html", title=x["title"], nav="Journal", body=body, desc=x["excerpt"])

    # ---------- about
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">About viotours</span><h1 class="her-hero">A travel agency that travels with you</h1>
  <p class="lead">We plan private, guided journeys for families and small groups who travel abroad and expect to be looked after. We are a direct agency, not a booking website.</p>
</div></section>
<section class="section"><div class="container">
  <div class="stat-row">
    <div class="stat"><b>6–15</b><span>travellers per group, or your own private family</span></div>
    <div class="stat"><b>1</b><span>planner who owns your trip from first call to flight home</span></div>
    <div class="stat"><b>24×7</b><span>helpline in India and at your destination</span></div>
  </div>
</div></section>
<section class="section section--sunk"><div class="container grid-2" style="align-items:start">
  <div class="prose"><span class="eyebrow">Why we exist</span>
    <h2 style="margin-top:12px">Travel is better when someone has your back</h2>
    <p>Booking websites are good at selling rooms. They are not there when a flight is cancelled at midnight, when your father needs a wheelchair at a connecting airport, or when a child is unwell in a city where nobody speaks your language.</p>
    <p>viotours is built for those moments. Every trip is planned by a person who has travelled the route, and led by a guide who knows your group before you land.</p>
    <p>We work from Chennai and Ras Al Khaimah, serving families in India, the UAE and NRIs abroad.</p>
  </div>
  <div class="panel" id="safety"><span class="eyebrow">Safety, stated plainly</span>
    <h2 class="her-h3" style="margin:12px 0 16px">What we do on every trip</h2>
    <ul class="contact-list" style="margin:0">
      <li>{icon("guide")}<div><b>Background-checked guides</b><span class="muted">Briefed on every traveller's needs before arrival.</span></div></li>
      <li>{icon("safety")}<div><b>Travel insurance included</b><span class="muted">Explained to you, with help to claim if needed.</span></div></li>
      <li>{icon("contact")}<div><b>24×7 helpline</b><span class="muted">Answered in India and at your destination.</span></div></li>
      <li>{icon("paragliding")}<div><b>Licensed operators only</b><span class="muted">For balloons, paragliding, rafting and the like, with a weather day kept spare.</span></div></li>
      <li>{icon("passport")}<div><b>Visas and paperwork with you</b><span class="muted">We prepare the files and check them before submission.</span></div></li>
    </ul>
  </div>
</div></section>
<section class="section"><div class="container center">
  <h2 class="her-h2">Start with a conversation</h2>
  <p class="lead" style="margin:12px auto 24px;max-width:560px">Tell us who's travelling and what you hope to feel. We'll take it from there.</p>
  <a class="btn btn--primary btn--lg" href="/enquire.html">Plan my trip</a>
</div></section>"""
    page(path="about.html", title="About and safety", nav="About", body=body,
         desc="About viotours: a direct travel agency for families and small groups, with vetted guides, included insurance and a 24×7 helpline.")

    # ---------- contact
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Contact</span><h1 class="her-hero">Talk to a planner</h1>
  <p class="lead">WhatsApp is quickest. We reply within one working day, and around the clock once you are travelling.</p>
</div></section>
<section class="section"><div class="container contact-grid">
  <form class="form panel" data-form="contact">
    <div class="form-row">
      <div class="field"><label for="c-name">Name</label><input id="c-name" type="text" name="name" required autocomplete="name"></div>
      <div class="field"><label for="c-phone">Phone or WhatsApp</label><input id="c-phone" type="tel" name="phone" autocomplete="tel"></div>
    </div>
    <div class="field"><label for="c-email">Email</label><input id="c-email" type="email" name="email" required autocomplete="email"></div>
    <div class="field"><label for="c-msg">Message</label><textarea id="c-msg" name="message" required></textarea></div>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="sr-only" aria-hidden="true">
    <div class="form-status" aria-live="polite"></div>
    <div><button class="btn btn--primary" type="submit">Send message</button></div>
  </form>
  <div>
    <ul class="contact-list">
      <li>{icon("contact")}<div><b>WhatsApp</b><a data-wa="Hello viotours" href="#" target="_blank" rel="noopener">Start a chat</a></div></li>
      <li>{icon("contact")}<div><b>Email</b><a data-email href="#"></a></div></li>
      <li>{icon("location")}<div><b>Offices</b><span class="muted">Chennai, Tamil Nadu · Ras Al Khaimah, UAE</span></div></li>
      <li>{icon("safety")}<div><b>Travelling with us now?</b><span class="muted">Use the helpline number on your emergency card, any hour.</span></div></li>
    </ul>
    <iframe class="map" title="viotours office location on Google Maps" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      src="https://www.google.com/maps?q=Chennai%2C%20Tamil%20Nadu&amp;output=embed"></iframe>
  </div>
</div></section>"""
    page(path="contact.html", title="Contact", nav="Contact", body=body,
         desc="Contact viotours on WhatsApp, email or the form. Offices in Chennai and Ras Al Khaimah.")

    # ---------- partners
    body = f"""
<section class="page-head">{kolam(-10, 20, 6, 3)}<div class="container">
  <span class="eyebrow">Partners</span><h1 class="her-hero">Partner with viotours</h1>
  <p class="lead">We work with guides, hotels, transport and activity operators who share our standards. If that's you, we'd like to hear from you.</p>
</div></section>
<section class="section"><div class="container grid-2" style="align-items:start">
  <div class="prose">
    <h2 style="margin-top:0">Who we're looking for</h2>
    <ul>
      <li><strong>Guides</strong> who enjoy looking after families, and speak English, Tamil, Hindi or Arabic.</li>
      <li><strong>Hotels and villas</strong> suited to multi-generation groups.</li>
      <li><strong>Licensed activity operators</strong> for balloons, paragliding, diving and rafting.</li>
      <li><strong>Ground handlers and transport</strong> with well-kept vehicles and careful drivers.</li>
    </ul>
    <p>Every partner is checked before their first trip with us, and reviewed by our travellers after each one.</p>
  </div>
  <form class="form panel" data-form="partner" data-ok="Thank you. We'll be in touch within a week.">
    <div class="field"><label for="p-org">Organisation or your name</label><input id="p-org" type="text" name="organisation" required></div>
    <div class="field"><label for="p-type">Partner type</label><select id="p-type" name="partner_type" required>
      <option value="">Choose one</option><option>Guide</option><option>Hotel or villa</option><option>Activity operator</option><option>Transport or ground handler</option><option>Other</option></select></div>
    <div class="form-row">
      <div class="field"><label for="p-loc">Where you operate</label><input id="p-loc" type="text" name="location" required></div>
      <div class="field"><label for="p-web">Website or profile</label><input id="p-web" type="text" name="url"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="p-email">Email</label><input id="p-email" type="email" name="email" required></div>
      <div class="field"><label for="p-phone">Phone or WhatsApp</label><input id="p-phone" type="tel" name="phone"></div>
    </div>
    <div class="field"><label for="p-msg">Tell us about your work</label><textarea id="p-msg" name="message"></textarea></div>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="sr-only" aria-hidden="true">
    <div class="form-status" aria-live="polite"></div>
    <div><button class="btn btn--primary" type="submit">Send</button></div>
  </form>
</div></section>"""
    page(path="partners.html", title="Partner with us", body=body,
         desc="Guides, hotels and licensed operators: partner with viotours to host families and small groups.")

    # ---------- sign in (UI only until the Supabase phase; not linked, not indexed)
    body = f"""
<section class="section"><div class="container" style="max-width:460px">
  <div class="panel stack-4">
    <span class="eyebrow">Traveller, guide and admin</span>
    <h1 class="her-h2">Sign in</h1>
    <p class="note">Accounts open with the next release. Until then, your planner shares your itinerary on WhatsApp and email.</p>
    <button class="btn btn--secondary" type="button" disabled style="width:100%">Continue with Google</button>
    <div class="field"><label for="s-email">Email</label><input id="s-email" type="email" disabled></div>
    <div class="field"><label for="s-pass">Password</label><input id="s-pass" type="password" disabled></div>
    <button class="btn btn--primary" type="button" disabled style="width:100%">Sign in</button>
  </div>
</div></section>"""
    page(path="signin.html", title="Sign in", body=body, noindex=True, desc="Sign in to viotours.")

    # ---------- 404
    body = """
<section class="section"><div class="container center" style="max-width:640px">
  <span class="eyebrow">Page not found</span><h1 class="her-hero" style="margin:12px 0">This path leads nowhere</h1>
  <p class="lead">The page may have moved, or the package may have finished its season.</p>
  <div class="hero__actions" style="justify-content:center;margin-top:24px"><a class="btn btn--primary" href="/packages.html">See packages</a><a class="btn btn--secondary" href="/">Home</a></div>
</div></section>"""
    page(path="404.html", title="Page not found", body=body, noindex=True, desc="Page not found.")

    # ---------- sitemap + robots
    urls = "".join(
        f"<url><loc>{SITE_URL}{'/' if p == 'index.html' else '/' + p}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>"
        for p, noidx in PAGES if not noidx)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(PAGES)} pages into {DIST}")


def event_row(e: dict) -> str:
    d = fmt_date(e["date"])
    return f"""<article class="event">
  <div class="event__date"><b>{d.day}</b><span>{d.strftime('%b %Y')}</span></div>
  <div><h3>{esc(e['title'])}</h3><p>{esc(e['where'])} — {esc(e['text'])}</p></div>
  <a class="btn btn--secondary btn--sm" data-wa="Hello viotours, I'd like to RSVP for: {esc(e['title'])} ({d.isoformat()})" href="#" target="_blank" rel="noopener">RSVP</a>
</article>"""


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("Serving on http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()
