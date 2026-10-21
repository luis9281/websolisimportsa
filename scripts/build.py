#!/usr/bin/env python3
"""
Generador del sitio de Solis Import S.A.

Función principal
  Lee data/brands.json (la única fuente de datos de marcas, líneas y productos) y escribe
  el HTML estático del sitio. Así, agregar o corregir un producto es editar el JSON y
  correr este script: todas las páginas que lo muestran se actualizan juntas.

Qué genera
  suturas/index.html             Sección Suturas del menú (líneas de suturas; contenido propio pendiente)
  index.html                     Inicio: muro de logos en la portada, tarjetas y franja de marcas
  productos/index.html           Catálogo con filtro por marca y buscador
  project/<slug>/index.html      Una página por marca y por línea (ej. suturas Atramat)
  project/<viejo>/index.html     Páginas de redirección (clave "redirects" del JSON)
  sitemap.xml                    Solo las páginas con contenido

No toca quienes-somos/, contactenos/ ni 404.html (se editan a mano).

Imágenes que usa
  assets/img/logos/<logo>        Logo oficial de cada marca (ver scripts/procesar_logos.py)
  assets/img/brands/<cover>.webp Foto de portada (opcional; sin portada se muestra el logo)
  assets/img/lines/<cover>.webp  Foto de portada de las líneas

Uso (desde la carpeta del proyecto)
     python scripts/build.py              # genera el sitio
     python scripts/build.py --serve      # genera y abre un servidor de prueba en http://localhost:8000
     python scripts/build.py --serve 8080 # otro puerto
"""
import html
import json
import os
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(os.environ["SOLIS_ROOT"]).resolve() if os.environ.get("SOLIS_ROOT") else Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "brands.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
BRANDS = DATA["brands"]
LINES = DATA.get("lines", [])
BY_SLUG = {b["slug"]: b for b in BRANDS}
LINE_BY_SLUG = {l["slug"]: l for l in LINES}
BASE = SITE["url"].rstrip("/") + "/"
WA = SITE["whatsapp"]
YEAR = SITE["lastmod"][:4]

esc = html.escape


def q(text):
    return urllib.parse.quote(text, safe="")


def wa(text):
    return f"https://wa.me/{WA}?text={q(text)}"


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def mono(name):
    return f'<span class="mono" aria-hidden="true">{esc(name[0].upper())}</span>'


def has_file(rel):
    return (ROOT / rel).is_file()


def cover_path(item):
    """Ruta (desde la raíz) de la foto de portada, o None si no existe."""
    c = item.get("cover")
    if not c:
        return None
    for folder in ("brands", "lines"):
        rel = f"assets/img/{folder}/{c}.webp"
        if has_file(rel):
            return rel
    return None


def logo_path(brand):
    lg = brand.get("logo")
    rel = f"assets/img/logos/{lg}" if lg else None
    return rel if rel and has_file(rel) else None


def brand_of(item):
    return BY_SLUG.get(item.get("parent")) or item


# --------------------------------------------------------------------------- piezas comunes

ICONS = {
    "wa": '<path d="M12 2a10 10 0 0 0-8.6 15L2 22l5.1-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.2 15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 0 1 12 3.8zM8.6 7.4c-.2 0-.5 0-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 2.2.9 2.6.7 3.1.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.2-.2-.5-.3l-1.6-.8c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1-.3-.1-1.1-.4-2.1-1.3-.8-.7-1.3-1.5-1.4-1.8-.2-.3 0-.4.1-.6l.4-.5c.1-.1.2-.3.2-.5.1-.2 0-.3 0-.5l-.7-1.7c-.2-.4-.4-.4-.6-.4z"/>',
    "ig": '<path d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7zm5 3.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 0 1 12 7.5zm0 2A2.5 2.5 0 1 0 14.5 12 2.5 2.5 0 0 0 12 9.5zM17.5 6a1 1 0 1 1-1 1 1 1 0 0 1 1-1z"/>',
    "yt": '<path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3z"/>',
    "in": '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.5h4V21H3zM9.5 9.5h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5c0-1.2 0-2.8-1.7-2.8s-2 1.3-2 2.7V21h-4z"/>',
}


def svg(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" class="">{ICONS[name]}</svg>'


SHIELD = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5L15.5 10"/></svg>'


def nav_block(r, current=""):
    """Menú principal (también se copia a quienes-somos/, contactenos/ y 404.html).
    "Suturas" despliega las líneas de DATA["menu_suturas"]."""
    nav = [("", "Inicio", "inicio"), ("quienes-somos/", "Sobre nosotros", "nosotros"),
           ("productos/", "Productos", "productos"), ("suturas/", "Suturas", "suturas"),
           ("contactenos/", "Contáctenos", "contacto")]
    cur = ' aria-current="page"'
    items = []
    for href, label, key in nav:
        a = f'<a href="{r}{href}"{cur if key == current else ""}>{label}</a>'
        if key == "suturas":
            sub = "".join(
                f'<li><a href="{r}project/{s}/">{esc(LINE_BY_SLUG[s].get("nav", LINE_BY_SLUG[s]["name"]))}</a></li>'
                for s in DATA.get("menu_suturas", []) if s in LINE_BY_SLUG)
            items.append(f'    <li class="has-sub">{a}<ul class="sub" aria-label="Suturas">{sub}</ul></li>')
        else:
            items.append(f"    <li>{a}</li>")
    return '<nav class="nav" aria-label="Principal"><ul>\n' + "\n".join(items) + "\n  </ul></nav>"


def page(r, *, title, desc, canonical, body, current="", robots="index", og_image=None, ld=(), preload=None):
    """Documento completo. r = prefijo relativo a la raíz ('', '../', '../../')."""
    og_image = og_image or BASE + "assets/img/og-default.jpg"
    home = r or "./"
    pre = f'\n<link rel="preload" as="image" href="{r}{preload}" type="image/webp">' if preload else ""
    lds = "".join("\n" + jsonld(x) for x in ld)
    return f"""<!doctype html>
<html lang="es-PA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots},follow, max-image-preview:large">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0a2540">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_PA">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Instrument+Sans:wght@400..700&display=swap">
<link rel="stylesheet" href="{r}assets/css/style.css">{pre}{lds}
</head>
<body>
<a class="skip" href="#main">Saltar al contenido</a>
<div class="topbar"><div class="wrap">
  <div class="contact">
    <a href="tel:+{WA}">{SITE['phone_main']}</a>
    <a class="hide-s" href="mailto:{SITE['email']}"><span class="hide-s">{SITE['email']}</span></a>
  </div>
  <div class="social">
    <a href="https://wa.me/{WA}" aria-label="WhatsApp" rel="noopener" target="_blank">{svg('wa')}</a>
    <a href="{SITE['instagram']}" aria-label="Instagram" rel="noopener" target="_blank">{svg('ig')}</a>
    <a href="{SITE['youtube']}" aria-label="YouTube" rel="noopener" target="_blank">{svg('yt')}</a>
    <a href="{SITE['linkedin']}" aria-label="LinkedIn" rel="noopener" target="_blank">{svg('in')}</a>
  </div>
</div></div>
<header class="site-header"><div class="wrap">
  <a class="logo" href="{home}" aria-label="Solis Import S.A. — Inicio">
    <picture><source srcset="{r}assets/img/logo.webp" type="image/webp">
    <img src="{r}assets/img/logo.png" alt="Solis Import S.A." width="190" height="52"></picture>
  </a>
  <button class="menu-btn" aria-label="Abrir menú" aria-expanded="false" type="button">
    <svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
  </button>
  {nav_block(r, current)}
</div></header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap foot-grid">
    <div>
      <a class="logo" href="{home}"><picture><source srcset="{r}assets/img/logo.webp" type="image/webp">
      <img src="{r}assets/img/logo.png" alt="Solis Import S.A." width="170" height="46" loading="lazy"></picture></a>
      <p>Somos una empresa orientada al sector salud desde nuestra fundación en 1996.</p>
      <ul>
        <li><a href="{r}quienes-somos/">Quiénes somos</a></li>
        <li><a href="{r}productos/">Productos</a></li>
        <li><a href="{r}suturas/">Suturas</a></li>
        <li><a href="{r}contactenos/">Contáctenos</a></li>
      </ul>
    </div>
    <div>
      <h2>Síguenos</h2>
      <ul>
        <li><a href="{SITE['instagram']}" rel="noopener" target="_blank">Instagram</a></li>
        <li><a href="{SITE['youtube']}" rel="noopener" target="_blank">YouTube</a></li>
        <li><a href="{SITE['linkedin']}" rel="noopener" target="_blank">LinkedIn</a></li>
        <li><a href="https://wa.me/{WA}" rel="noopener" target="_blank">WhatsApp</a></li>
      </ul>
    </div>
    <div>
      <h2>Panamá</h2>
      <p>{esc(SITE['address_panama'])}<br>{esc(SITE['postal'])}</p>
      <p>Tel. {esc(SITE['phones_office'])}<br>WhatsApp {SITE['phone_main']}<br>
      <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
    </div>
    <div>
      <h2>Provincia de Herrera</h2>
      <p>{esc(SITE['address_chitre'])}</p>
      <p>Tel. {esc(SITE['phone_chitre'])}</p>
    </div>
  </div>
  <div class="legal"><div class="wrap"><span>© {YEAR} Solis Import S.A. Todos los derechos reservados.</span>
  <span>Distribuidor autorizado de equipos e insumos médicos en Panamá.</span></div></div>
</footer>
<a class="wa-float" href="{wa('Hola, quisiera más información sobre sus productos.')}" target="_blank" rel="noopener" aria-label="Consultar por WhatsApp">{svg('wa')}<span>Consultar por WhatsApp</span></a>
<script src="{r}assets/js/main.js" defer></script>
</body>
</html>
"""


def logo_img(brand, r, cls="", w=200, h=80, lazy=True):
    lp = logo_path(brand)
    if not lp:
        return ""
    lz = ' loading="lazy"' if lazy else ""
    c = f' class="{cls}"' if cls else ""
    return f'<img{c} src="{r}{lp}" alt="{esc(brand["name"])}" width="{w}" height="{h}"{lz} decoding="async">'


def card(item, r):
    """Tarjeta de marca o de línea. Con foto: la foto (las portadas ya traen el logo). Sin foto: el logo al centro."""
    brand = brand_of(item)
    soon = not item.get("has_content", True)
    text = " ".join(x for x in (item["name"], item.get("area", ""), item.get("tagline", "")) if x)
    text += " " + " ".join(p["name"] for p in item.get("products", []))
    cp = cover_path(item)
    lg = logo_img(brand, r, "", 160, 60)
    if cp:
        media = f'{mono(item["name"])}<img src="{r}{cp}" alt="{esc(item["name"])} — Solis Import Panamá" width="400" height="500" loading="lazy" onerror="this.remove()">'
        ph = '<div class="ph">'
    else:
        media = mono(item["name"]) + (f'<span class="logo-box">{lg}</span>' if lg else "")
        ph = '<div class="ph is-logo">'
    tag = '<span class="tag">Próximamente</span>' if soon else ""
    more = "Consultar por esta marca" if soon else "Ver detalle"
    return f"""<article class="card" data-brand="{brand['slug']}" data-text="{esc(text.strip())}">
  {ph}{media}{tag}</div>
  <div class="body">
    <h3><a href="{r}project/{item['slug']}/">{esc(item['name'])}</a></h3>
    <p class="area">{esc(item.get('area', ''))}</p>
    <span class="more" aria-hidden="true">{more}</span>
  </div>
</article>"""


def thumb(brand, r, size):
    lp = logo_path(brand)
    img = f'<img src="{r}{lp}" alt="" width="{size}" height="{size}" loading="lazy" onerror="this.remove()">' if lp else ""
    return f'<span class="thumb{" is-logo" if lp else ""}">{mono(brand["name"])}{img}</span>'


# --------------------------------------------------------------------------- inicio

def build_home():
    r = ""
    featured = [b for b in BRANDS if b.get("has_content")]
    # "logo_wall": false en el JSON saca una marca del muro (p. ej. logos muy alargados)
    wall = [b for b in featured if b.get("logo_wall", True) and logo_path(b)][:11]
    wall_html = "".join(
        f'<li><a href="project/{b["slug"]}/" aria-label="{esc(b["name"])}">{logo_img(b, r, "", 180, 70, lazy=False) or esc(b["name"])}</a></li>'
        for b in wall)
    wall_html += f'<li class="more"><a href="productos/"><strong>{len(BRANDS)}</strong> marcas<span>Ver catálogo</span></a></li>'
    cards = "".join(card(b, r) for b in featured[:10])
    strip = "".join(
        f'<li><a href="project/{b["slug"]}/" title="{esc(b["name"])} · {esc(b.get("area", ""))}">'
        f'{logo_img(b, r, "", 160, 64) or esc(b["name"])}<span class="vh">{esc(b["name"])}</span></a></li>'
        for b in BRANDS)
    names = ", ".join(b["name"] for b in featured[:7])
    desc = f"Distribuidor autorizado en Panamá de suturas {names} y más. Insumos médico quirúrgicos, equipos médicos y dentales desde 1996."
    body = f"""
<section class="hero" aria-label="Destacados">
  <div class="slides">
    <div class="slide is-active has-bg">
      <div class="slide-bg" aria-hidden="true"><img src="assets/img/content/hero-equipos.webp" alt="" width="1920" height="1080" fetchpriority="high"></div>
      <div class="wrap">
      <div>
        <h1>Tu salud es parte de nuestro éxito</h1>
        <p class="sub">Accesorios e insumos médico quirúrgicos, equipos médicos, medicamentos, suplementos nutricionales, antisépticos y desinfectantes.</p>
        <div class="actions"><a class="btn" href="productos/">Ver productos</a>
        <a class="btn ghost" href="quienes-somos/">Quiénes somos</a></div>
        <p class="hero-note">{SHIELD} Distribuidor autorizado de {len(BRANDS)} marcas internacionales</p>
      </div>
      <ul class="logo-wall" aria-label="Marcas que distribuimos">{wall_html}</ul>
    </div></div>
    <div class="slide"><div class="wrap">
      <div>
        <h2 class="hl">Confianza y seguridad</h2>
        <p class="sub">Las suturas quirúrgicas Atramat® ofrecen innovación, calidad y tecnología. Su gama Premium de materiales y agujas está hecha para las especialidades y los cirujanos más exigentes.</p>
        <div class="actions"><a class="btn" href="project/atramat/">Más información</a></div>
      </div>
      <div class="slide-photo"><img src="assets/img/content/suturas-seccion.webp" alt="Suturas quirúrgicas Atramat" width="720" height="576" loading="lazy"></div>
    </div></div>
    <div class="slide"><div class="wrap">
      <div>
        <h2 class="hl">Solis Import S.A.</h2>
        <p class="sub">Más de 30 años importando, distribuyendo y dando mantenimiento a equipos e insumos para hospitales y clínicas de Panamá.</p>
        <div class="actions"><a class="btn" href="contactenos/">Contáctenos</a></div>
      </div>
      <div class="brand-mark">
        <picture><source srcset="assets/img/logo-solis-hero.webp" type="image/webp">
        <img src="assets/img/logo-solis-hero.png" alt="Solis Import S.A. — Importadores de equipos, accesorios e insumos médicos" width="581" height="116" loading="lazy"></picture>
        <dl class="mark-facts">
          <div><dt>1996</dt><dd>año de fundación</dd></div>
          <div><dt>{len(BRANDS)}</dt><dd>marcas internacionales</dd></div>
          <div><dt>2</dt><dd>sedes: Panamá y Chitré</dd></div>
        </dl>
      </div>
    </div></div>
  </div>
  <div class="hero-ctrl"><div class="wrap">
    <button class="dot" type="button" aria-label="Diapositiva 1"></button>
    <button class="dot" type="button" aria-label="Diapositiva 2"></button>
    <button class="dot" type="button" aria-label="Diapositiva 3"></button>
    <div class="arrow"><button type="button" data-prev aria-label="Anterior">&#8592;</button><button type="button" data-next aria-label="Siguiente">&#8594;</button></div>
  </div></div>
</section>

<section class="section">
  <div class="wrap split">
    <div>
      <h2>Comprometidos con nuestra gente</h2>
      <h3>Políticas de calidad</h3>
      <p>Analizamos el entorno corporativo, económico y social para impulsar los cambios que favorecen el desarrollo integral de quienes forman parte de la organización y motivan su superación.</p>
      <a class="btn ghost" href="quienes-somos/">Conoce nuestra misión y valores</a>
    </div>
    <button class="video" type="button" data-yt="x77hOABzXUg" aria-label="Reproducir video institucional">
      <img src="assets/img/content/calidad-video.webp" alt="" width="800" height="450" loading="lazy">
      <span class="play"><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg></span></span>
    </button>
  </div>
</section>

<section class="section alt">
  <div class="wrap">
    <div class="section-head"><h2>Nuestra línea de productos</h2>
    <a class="btn ghost sm" href="productos/">Ver el catálogo completo</a></div>
    <div class="grid">
      {cards}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div>
      <h2>Calidad e innovación en suturas</h2>
      <p>Nuestra línea de suturas absorbibles y no absorbibles Atramat® está hecha para cirujanos que buscan la mejor calidad y valor en sus procedimientos.</p>
      <p>Las suturas Atramat® Plus están recubiertas con diacetato de clorhexidina, un agente antibacteriano de amplio espectro que inhibe el crecimiento de bacterias.</p>
      <div class="actions"><a class="btn" href="project/atramat/">Ver línea Atramat</a>
      <a class="btn ghost" href="project/suturas-quirurgicas-plus-antibacterianas/">Suturas PLUS</a></div>
    </div>
    <div class="slide-photo"><img src="assets/img/content/agujas-atramat.webp" alt="Agujas de sutura quirúrgica Atramat" width="720" height="576" loading="lazy"></div>
  </div>
</section>

<section class="section alt">
  <div class="wrap">
    <div class="section-head"><h2>Marcas que distribuimos</h2>
    <a class="btn ghost sm" href="productos/">Ver todas</a></div>
    <ul class="logos">
      {strip}
    </ul>
  </div>
</section>"""
    org = {"@context": "https://schema.org", "@type": ["Organization", "LocalBusiness"], "@id": BASE + "#organization",
           "name": SITE["name"], "url": BASE, "logo": BASE + "assets/img/logo.png", "image": BASE + "assets/img/og-default.jpg",
           "description": "Importación y distribución de insumos, equipos médicos y quirúrgicos en Panamá desde 1996.",
           "foundingDate": "1996", "email": SITE["email"], "telephone": "+507-6862-9425",
           "address": {"@type": "PostalAddress", "streetAddress": "Parque Lefevre, Panamá Viejo Business Center, local G-9",
                       "addressLocality": "Ciudad de Panamá", "addressCountry": "PA", "postOfficeBoxNumber": "0819-05563"},
           "areaServed": "PA", "sameAs": [SITE["instagram"], SITE["youtube"], SITE["linkedin"]]}
    web = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": BASE, "inLanguage": "es-PA"}
    return page(r, title="Solis Import S.A. | Insumos y equipos médicos en Panamá desde 1996", desc=desc,
                canonical=BASE, body=body, current="inicio", ld=(org, web),
                preload="assets/img/content/hero-equipos.webp")


# --------------------------------------------------------------------------- catálogo

def build_suturas():
    """Portada de la sección Suturas (menú principal): las líneas de DATA["menu_suturas"]."""
    r = "../"
    atramat = BY_SLUG.get("atramat", {})
    lg = logo_img(atramat, r, "", 220, 80, lazy=False) if atramat else ""
    body = f"""<div class="wrap crumbs"><nav aria-label="Ruta"><ol><li><a href="{r}">Inicio</a></li><li aria-current="page">Suturas</li></ol></nav></div>

<section class="brand-hero"><div class="wrap">
  <div>
    <span class="badge">{SHIELD} Distribuidor autorizado en Panamá</span>
    <h1>Suturas quirúrgicas</h1>
    <p class="tagline">Suturas absorbibles, no absorbibles y antibacterianas para cada especialidad.</p>
    <div class="actions">
      <a class="btn wa" href="{wa('Hola, quisiera cotizar suturas quirúrgicas.')}" target="_blank" rel="noopener">Cotizar suturas</a>
      <a class="btn ghost" href="{r}project/atramat/">Conocer Atramat</a>
    </div>
  </div>
  <div class="frame logo-frame"><div class="ph">{lg}</div></div>
</div></section>

<section class="section"><div class="wrap">
  {categories({"lines": DATA.get("menu_suturas", [])}, r, "Líneas de productos")}
</div></section>"""
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Suturas", "item": BASE + "suturas/"}]}
    return page(r, title="Suturas quirúrgicas en Panamá | Solis Import S.A.",
                desc="Suturas quirúrgicas absorbibles, no absorbibles y antibacterianas PLUS en Panamá. Distribuidor autorizado Atramat: Solis Import S.A.",
                canonical=BASE + "suturas/", body=body, current="suturas", ld=(crumbs,))


def build_catalog():
    r = "../"
    tiles = "".join(
        f'<li><button type="button" class="tile{"" if b.get("has_content") else " soon"}" data-brand="{b["slug"]}" aria-pressed="false">'
        f'{thumb(b, r, 44)}<span>{esc(b["name"])}<small>{esc(b.get("area", ""))}</small></span></button></li>'
        for b in BRANDS)
    items = BRANDS + LINES
    cards = "".join(card(i, r) for i in items)
    content = [b for b in BRANDS if b.get("has_content")]
    names = ", ".join(b["name"] for b in content[:10])
    body = f"""
<section class="section">
  <div class="wrap">
    <h1>Catálogo de productos</h1>
    <p class="lead">Elige una o varias marcas para ver sus líneas. Todas son representadas en Panamá por Solis Import S.A.</p>

    <div class="finder" id="finder">
      <div class="finder-bar">
        <label for="q" class="vh">Buscar</label>
        <div class="search">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
          <input id="q" type="search" placeholder="Buscar marca o producto" autocomplete="off">
        </div>
        <button class="linkbtn" type="button" data-clear hidden>Limpiar filtros</button>
        <span class="count" id="count" role="status" aria-live="polite"></span>
      </div>
      <ul class="tray" aria-label="Filtrar por marca">{tiles}</ul>
    </div>

    <div class="grid" id="catalog">
      {cards}
    </div>

    <div class="empty" id="empty" hidden>
      <h2>No encontramos coincidencias</h2>
      <p style="margin-inline:auto">Prueba con otra marca o escríbenos y te ayudamos a encontrar lo que necesitas.</p>
      <div class="actions" style="justify-content:center">
        <button class="btn ghost" type="button" data-clear>Limpiar filtros</button>
        <a class="btn wa" href="{wa('Hola, estoy buscando un producto y no lo encuentro en el catálogo.')}" target="_blank" rel="noopener">Escribir por WhatsApp</a>
      </div>
    </div>
  </div>
</section>"""
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Catálogo de productos",
            "url": BASE + "productos/", "isPartOf": {"@id": BASE + "#organization"},
            "mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": b["name"], "url": f"{BASE}project/{b['slug']}/"}
                for i, b in enumerate(content)]}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Productos", "item": BASE + "productos/"}]}
    return page(r, title="Catálogo de productos médicos y dentales en Panamá | Solis Import S.A.",
                desc=f"Filtra por marca: {names} y más. Distribuidor autorizado en Panamá.",
                canonical=BASE + "productos/", body=body, current="productos", ld=(coll, crumbs))


# --------------------------------------------------------------------------- marca / línea

def others_for(item):
    content = [b for b in BRANDS if b.get("has_content")]
    ref = brand_of(item)["slug"]
    idx = next((i for i, b in enumerate(content) if b["slug"] == ref), -1)
    if idx < 0:
        return content[:4]
    return [content[(idx + k) % len(content)] for k in range(1, 5)]


def spec(p, item, r):
    name = p["name"]
    owner = item["name"]
    models = p.get("models") or []
    chips = ('<div class="chips-row">' + "".join(f'<span class="chip">{esc(m)}</span>' for m in models) + "</div>") if models else ""
    link = p.get("link")
    if link:
        btn = f'<a class="btn ghost sm" href="{r}project/{link}/">Ver detalle</a>'
    elif p.get("datasheet"):
        btn = f'<a class="btn ghost sm" href="{wa(f"Hola, quisiera la ficha técnica de {name} ({owner}).")}" target="_blank" rel="noopener">Pedir ficha técnica</a>'
    else:
        btn = f'<a class="btn ghost sm" href="{wa(f"Hola, quisiera cotizar {name} ({owner}).")}" target="_blank" rel="noopener">Cotizar</a>'
    return f'<li class="spec"><div><h3>{esc(name)}</h3><p>{esc(p.get("desc", ""))}</p>{chips}</div>{btn}</li>'


def chip(p, line_slug, r):
    if p.get("id"):
        return f'<a class="chip" href="{r}project/{line_slug}/#{p["id"]}">{esc(p["name"])}</a>'
    if p.get("link"):
        return f'<a class="chip" href="{r}project/{p["link"]}/">{esc(p["name"])}</a>'
    return f'<span class="chip">{esc(p["name"])}</span>'


def categories(brand, r, title="Categorías de productos"):
    out = []
    for slug in brand.get("lines", []):
        l = LINE_BY_SLUG.get(slug)
        if not l:
            continue
        cp = cover_path(l)
        img = f'<img src="{r}{cp}" alt="{esc(l["name"])}" width="320" height="400" loading="lazy" onerror="this.remove()">' if cp else ""
        chips = ""
        if l.get("products"):
            chips = '<div class="chips-row" aria-label="Familias">' + "".join(chip(p, slug, r) for p in l["products"]) + "</div>"
        out.append(f'<article class="cat"><div class="cat-img">{mono(l["name"])}{img}</div><div class="cat-body">'
                   f'<h3><a href="{r}project/{slug}/">{esc(l["name"])}</a></h3><p>{esc(l["description"][0])}</p>{chips}'
                   f'<a class="btn ghost sm" href="{r}project/{slug}/">Ver categoría</a></div></article>')
    return f'<h2 id="categorias">{esc(title)}</h2><div class="cats">' + "".join(out) + "</div>" if out else ""


# --------------------------------------------------------------------------- líneas de suturas (estilo Atramat)

CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'


def sx_product(p, line, r):
    """Ficha técnica de un producto: barra de color, indicación, datos clave, tabla y características."""
    pid, name = p["id"], p["name"]
    stats = "".join(f'<div><span>{esc(s["label"])}</span><strong>{esc(s["value"])}</strong></div>' for s in p.get("stats", []))
    tech = "".join(f"<tr><th scope=\"row\">{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in p.get("tech", []))
    feats = "".join(f"<li>{CHECK}{esc(f)}</li>" for f in p.get("features", []))
    models = "".join(f'<span class="chip">{esc(m)}</span>' for m in p.get("models", []))
    img = (f'<figure class="sx-fig"><img src="{r}{p["image"]}" alt="{esc(name)}" loading="lazy"></figure>'
           if p.get("image") and has_file(p["image"]) else "")
    return f"""<article class="sx-prod" id="{pid}" style="--sw:{p.get('color', '#00a3c4')}">
  <header class="sx-prod-head">
    <span class="sx-dot" aria-hidden="true"></span>
    <div><h3>{esc(name)}</h3>{f'<p class="sx-sub">{esc(p["subtitle"])}</p>' if p.get("subtitle") else ""}</div>
    <a class="btn ghost sm" href="{wa(f"Hola, quisiera cotizar {name} (Atramat).")}" target="_blank" rel="noopener">Cotizar</a>
  </header>
  <div class="sx-prod-body">
    {f'<p class="sx-ind"><strong>Indicaciones.</strong> {esc(p["indication"])}</p>' if p.get("indication") else ""}
    {f'<div class="sx-stats">{stats}</div>' if stats else ""}
    {img}
    <div class="sx-cols">
      {f'<div><h4>Información técnica</h4><table class="sx-tech">{tech}</table></div>' if tech else ""}
      {f'<div><h4>Características</h4><ul class="sx-feat">{feats}</ul></div>' if feats else ""}
    </div>
    {f'<div class="chips-row">{models}</div>' if models else ""}
  </div>
</article>"""


def build_suture_line(item):
    r = "../../"
    slug, name = item["slug"], item["name"]
    brand = brand_of(item)
    url = f"{BASE}project/{slug}/"
    prods = item.get("products", [])
    menu = [s for s in DATA.get("menu_suturas", []) if s in LINE_BY_SLUG]
    cur = ' aria-current="page"'
    tabs = "".join(
        f'<li><a href="{r}project/{s}/"{cur if s == slug else ""}>{esc(LINE_BY_SLUG[s].get("nav", LINE_BY_SLUG[s]["name"]))}</a></li>'
        for s in menu)
    cp = cover_path(item)
    hero_img = f'<img src="{r}{cp}" alt="{esc(name)} Atramat" width="440" height="550">' if cp else logo_img(brand, r, "", 220, 80, lazy=False)
    index = "".join(
        f'<li><a href="#{p["id"]}" style="--sw:{p.get("color", "#00a3c4")}"><span class="sx-swatch" aria-hidden="true"></span>'
        f'<span class="sx-idx-name">{esc(p["name"])}</span><span class="sx-idx-sub">{esc(p.get("subtitle", ""))}</span>'
        f'<span class="sx-more">Ver ficha</span></a></li>' for p in prods)
    callout = ""
    if item.get("callout"):
        c = item["callout"]
        callout = (f'<section class="sx-callout"><div class="wrap"><h2>{esc(c["title"])}</h2>'
                   + "".join(f"<p>{esc(t)}</p>" for t in c.get("text", []))
                   + ('<ul class="sx-feat">' + "".join(f"<li>{CHECK}<em>{esc(x)}</em></li>" for x in c.get("list", [])) + "</ul>" if c.get("list") else "")
                   + "</div></section>")
    needles = ""
    if slug != "agujas" and "agujas" in LINE_BY_SLUG:
        ncp = cover_path(LINE_BY_SLUG["agujas"])
        needles = f"""<section class="sx-band"><div class="wrap sx-band-in">
  {f'<img src="{r}{ncp}" alt="Agujas quirúrgicas Atramat" width="400" height="500" loading="lazy">' if ncp else ""}
  <div><p class="sx-eyebrow">Agujas Atramat®</p><h2>La calidad y la tecnología de nuestras agujas son la punta de nuestro proceso de innovación.</h2>
  <a class="btn" href="{r}project/agujas/">Conocer las agujas</a></div>
</div></section>"""
    others = [LINE_BY_SLUG[s] for s in menu if s != slug][:1]
    nxt = others[0] if others else None
    body = f"""<div class="wrap crumbs"><nav aria-label="Ruta"><ol><li><a href="{r}">Inicio</a></li><li><a href="{r}suturas/">Suturas</a></li><li aria-current="page">{esc(item.get("nav", name))}</li></ol></nav></div>

<div class="wrap"><ul class="sx-tabs" aria-label="Líneas Atramat">{tabs}</ul></div>

<section class="sx-hero"><div class="wrap">
  <div>
    <p class="sx-eyebrow">{logo_img(brand, r, "sx-brand", 130, 50, lazy=False)}<span>Distribuidor autorizado en Panamá</span></p>
    <h1>{esc(name)}</h1>
    {"".join(f"<p>{esc(t)}</p>" for t in item.get("description", []))}
    <div class="actions">
      <a class="btn wa" href="{wa(f"Hola, quisiera cotizar {name} (Atramat).")}" target="_blank" rel="noopener">Solicitar cotización</a>
      {'<a class="btn ghost" href="#productos">Ver productos</a>' if len(prods) > 1 else ""}
    </div>
  </div>
  <div class="sx-hero-img">{hero_img}</div>
</div></section>

{f'<section class="section sx-index-sec" id="productos"><div class="wrap"><h2>Línea {esc(item.get("nav", name))}</h2><ul class="sx-index">{index}</ul></div></section>' if len(prods) > 1 else ""}

{callout}

<section class="section sx-list"><div class="wrap">
  {"".join(sx_product(p, item, r) for p in prods)}
  <p class="sx-note">* Para más información, consulta las instrucciones de uso del producto.</p>
</div></section>

{needles}

<section class="section"><div class="wrap">
  <div class="section-head"><h2>Siguientes pasos</h2></div>
  <div class="sx-next">
    <a href="{r}suturas/"><strong>Más líneas de productos</strong><span>Suturas, mínima invasión, malla, agujas y bonewax de Atramat.</span><em>Ver todas</em></a>
    {f'<a href="{r}project/{nxt["slug"]}/"><strong>{esc(nxt.get("nav", nxt["name"]))}</strong><span>{esc(nxt.get("tagline", ""))}</span><em>Explorar</em></a>' if nxt else ""}
    <a href="{r}contactenos/"><strong>Cotiza con Solis Import</strong><span>Indícanos producto, calibre, aguja y cantidad. Respondemos con precio y disponibilidad.</span><em>Contáctanos</em></a>
  </div>
</div></section>"""
    title = f"{name} Atramat en Panamá | Solis Import S.A."
    desc = item.get("meta") or f"{name} Atramat en Panamá. Solis Import S.A."
    og = BASE + cp if cp else None
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE},
              {"@type": "ListItem", "position": 2, "name": "Suturas", "item": BASE + "suturas/"},
              {"@type": "ListItem", "position": 3, "name": item.get("nav", name), "item": url}]},
          {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "item": {
                  "@type": "Product", "name": f"Atramat {p['name']}",
                  "description": p.get("indication") or p.get("subtitle", ""),
                  "brand": {"@type": "Brand", "name": "Atramat"}, **({"image": og} if og else {})}}
              for i, p in enumerate(prods)]}]
    return page(r, title=title, desc=desc, canonical=url, body=body, current="suturas", og_image=og, ld=ld)


def build_item(item):
    if item.get("template") == "suturas":
        return build_suture_line(item)
    r = "../../"
    slug, name = item["slug"], item["name"]
    brand = brand_of(item)
    is_line = item is not brand
    soon = not item.get("has_content", True)
    url = f"{BASE}project/{slug}/"
    tagline = item.get("tagline") or "Estamos preparando la información de esta marca."
    cp = cover_path(item)
    lg = logo_img(brand, r, "", 220, 80, lazy=False)
    quote = wa(f"Hola, quisiera cotizar productos {name}.")

    if cp:
        frame = f'<div class="frame"><div class="ph">{mono(name)}<img src="{r}{cp}" alt="{esc(name)} — distribuido por Solis Import en Panamá" width="440" height="550" onerror="this.remove()"></div></div>'
    else:
        frame = f'<div class="frame logo-frame"><div class="ph">{mono(name)}{lg}</div></div>'

    crumbs_html = f'<li><a href="{r}">Inicio</a></li><li><a href="{r}productos/">Productos</a></li>'
    crumbs_ld = [{"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE},
                 {"@type": "ListItem", "position": 2, "name": "Productos", "item": BASE + "productos/"}]
    if is_line:
        crumbs_html += f'<li><a href="{r}project/{brand["slug"]}/">{esc(brand["name"])}</a></li>'
        crumbs_ld.append({"@type": "ListItem", "position": 3, "name": brand["name"], "item": f"{BASE}project/{brand['slug']}/"})
    crumbs_html += f'<li aria-current="page">{esc(name)}</li>'
    crumbs_ld.append({"@type": "ListItem", "position": len(crumbs_ld) + 1, "name": name, "item": url})

    facts = ""
    if item.get("highlights"):
        facts = '<div class="wrap"><div class="facts">' + "".join(
            f'<div><strong>{esc(h["value"])}</strong><span>{esc(h["label"])}</span></div>' for h in item["highlights"]) + "</div></div>\n"

    web = brand.get("website")
    web_dd = f'\n      <dt>Fabricante</dt><dd><a href="{esc(web)}" target="_blank" rel="noopener">Sitio oficial de {esc(brand["name"])}</a></dd>' if web and not is_line else ""
    aside = f"""  <aside class="aside" aria-label="Cotizar">
    <h2>Cotiza con nosotros</h2>
    <p>Indícanos el producto, la cantidad y tus datos. Respondemos con precio y disponibilidad.</p>
    <a class="btn wa" href="{quote}" target="_blank" rel="noopener">Cotizar por WhatsApp</a>
    <a class="btn ghost" href="mailto:{SITE['email']}?subject={q('Cotización ' + name)}">Enviar un correo</a>
    <dl>
      <dt>Teléfono</dt><dd>{SITE['phone_main']}<br>{esc(SITE['phones_office'])}</dd>
      <dt>Correo</dt><dd><a href="mailto:{SITE['email']}">{SITE['email']}</a></dd>
      <dt>Ubicación</dt><dd>{esc(SITE['address_panama'])}</dd>{web_dd}
    </dl>
  </aside>"""

    if soon:
        main = f"""<section class="section"><div class="wrap soon-box">
  <h2>Información próximamente</h2>
  <p>Estamos preparando el contenido de {esc(name)}. Si necesitas precios, disponibilidad o fichas técnicas, escríbenos y te atendemos directamente.</p>
  <div class="actions">
    <a class="btn wa" href="{quote}" target="_blank" rel="noopener">Consultar por WhatsApp</a>
    <a class="btn ghost" href="mailto:{SITE['email']}?subject={q('Consulta sobre ' + name)}">Escribir por correo</a>
  </div>
</div></section>"""
    else:
        about = "".join(f"<p>{esc(p)}</p>" for p in item.get("description", []))
        prods = item.get("products", [])
        plist = ('<h2>Productos destacados</h2><ul class="specs">' + "".join(spec(p, item, r) for p in prods) + "</ul>") if prods and not item.get("lines") else ""
        main = f"""<section class="section"><div class="wrap detail">
  <div><h2>Sobre {esc(name)}</h2>{about}{categories(item, r)}{plist}</div>
{aside}
</div></section>"""

    others = "".join(card(b, r) for b in others_for(item))
    body = f"""<div class="wrap crumbs"><nav aria-label="Ruta"><ol>{crumbs_html}</ol></nav></div>

<section class="brand-hero"><div class="wrap">
  <div>
    <span class="badge">{SHIELD} Distribuidor autorizado en Panamá</span>
    <h1>{esc(name)}</h1>
    <p class="tagline">{esc(tagline)}</p>
    <div class="actions">
      <a class="btn wa" href="{quote}" target="_blank" rel="noopener">Solicitar cotización</a>
      <a class="btn ghost" href="{r}productos/">Volver al catálogo</a>
    </div>
  </div>
  {frame}
</div></section>
{facts}
{main}

<section class="section alt"><div class="wrap">
  <div class="section-head"><h2>Otras marcas que distribuimos</h2><a class="btn ghost sm" href="{r}productos/">Ver todas</a></div>
  <div class="grid">{others}</div>
</div></section>"""

    if item.get("tagline"):
        title = f"{name} en Panamá | {item['tagline']} – Solis Import S.A."
    else:
        title = f"{name} en Panamá | Solis Import S.A."
    desc = item.get("meta") or f"{name} en Panamá: distribuidor autorizado Solis Import S.A. Consulta precios y disponibilidad."
    img_rel = cp or logo_path(brand)
    og = BASE + img_rel if img_rel else None
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs_ld},
          {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url, "description": desc,
           "inLanguage": "es-PA", "isPartOf": {"@id": BASE + "#organization"}}]
    prods = item.get("products", []) if not soon else []
    if prods:
        ld.append({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {
                "@type": "Product", "name": p["name"], "description": p.get("desc", ""),
                "brand": {"@type": "Brand", "name": brand["name"]}, **({"image": og} if og else {})}}
            for i, p in enumerate(prods)]})
    return page(r, title=title, desc=desc, canonical=url, body=body, current="productos",
                robots="noindex" if soon else "index", og_image=og, ld=ld)


def build_redirect(target):
    url = BASE + target
    return f"""<!doctype html>
<html lang="es-PA">
<head>
<meta charset="utf-8">
<title>Redirigiendo…</title>
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url=../../{target}">
</head>
<body>
<p>Esta página se movió a <a href="../../{target}">{url}</a>.</p>
</body>
</html>
"""


def build_sitemap(items):
    lm = SITE["lastmod"]
    urls = ["", "quienes-somos/", "productos/", "suturas/", "contactenos/"] +[f"project/{i['slug']}/" for i in items if i.get("has_content", True)]
    rows = "\n".join(f"  <url><loc>{BASE}{u}</loc><lastmod>{lm}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


# --------------------------------------------------------------------------- principal

def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    return rel


def check():
    """Avisa de datos o imágenes que faltan, sin detener la generación."""
    warns = []
    for b in BRANDS:
        if not logo_path(b):
            warns.append(f"sin logo: {b['slug']} (esperado assets/img/logos/{b.get('logo', b['slug'] + '.png')})")
        if b.get("has_content") and not b.get("products") and not b.get("lines"):
            warns.append(f"sin productos: {b['slug']}")
    for l in LINES:
        if l.get("parent") not in BY_SLUG:
            warns.append(f"línea sin marca válida: {l['slug']}")
    return warns


# Páginas fijas (se editan a mano): build.py solo les actualiza el menú principal
STATIC_NAV = [("quienes-somos/index.html", "../", "nosotros"), ("contactenos/index.html", "../", "contacto"),
              ("404.html", "/", "")]


def sync_static_nav():
    import re
    done = []
    for rel, r, current in STATIC_NAV:
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        new, n = re.subn(r'<nav class="nav" aria-label="Principal">.*?</ul></nav>', lambda m: nav_block(r, current), text, count=1, flags=re.S)
        if n and new != text:
            p.write_text(new, encoding="utf-8", newline="\n")
            done.append(rel)
    return done


def main():
    out = [write("index.html", build_home()), write("productos/index.html", build_catalog()),
           write("suturas/index.html", build_suturas())]
    out += sync_static_nav()
    items = BRANDS + LINES
    for i in items:
        out.append(write(f"project/{i['slug']}/index.html", build_item(i)))
    for old, new in DATA.get("redirects", {}).items():
        out.append(write(old.rstrip("/") + "/index.html", build_redirect(new)))
    out.append(write("sitemap.xml", build_sitemap(items)))
    print(f"{len(out)} archivos generados ({len(BRANDS)} marcas, {len(LINES)} líneas).")
    for w in check():
        print("  aviso:", w)

    if "--serve" in sys.argv:
        import http.server
        import functools
        i = sys.argv.index("--serve")
        port = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 and sys.argv[i + 1].isdigit() else 8000
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        print(f"Servidor de prueba en http://localhost:{port}/  (Ctrl+C para detener)")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    main()
