#!/usr/bin/env python3
"""
Descarga y optimiza para web todas las imágenes del sitio de Solis Import S.A.

Qué hace
  1. Descarga las imágenes originales de www.solisimportsa.com a la carpeta _descargas/
     (si ya existen no las vuelve a bajar).
  2. Las recorta a la proporción que usa el diseño, las reduce de tamaño y las guarda
     en WebP (pesan 60-80 % menos que el JPG original) dentro de assets/img/.
  3. Genera miniaturas cuadradas de cada marca para el filtro del catálogo.
  4. Crea favicon.png, apple-touch-icon.png y assets/img/og-default.jpg (vista previa al compartir).
  5. Si colocas logos o fotos propias en imagenes-originales/, también las optimiza:
         imagenes-originales/<marca>-logo.png      → logo de la marca (se usa en la miniatura del filtro)
         imagenes-originales/<marca>-portada.jpg   → foto de portada de la marca
     Ejemplos: trulife-logo.png, carestream-dental-logo.svg no (usa PNG/JPG/WebP), mir-portada.jpg

Requisitos
     python3 -m pip install pillow

Uso (desde la carpeta del proyecto)
     python3 scripts/descargar_imagenes.py            # descarga + optimiza
     python3 scripts/descargar_imagenes.py --force    # vuelve a procesar todo
     python3 scripts/descargar_imagenes.py --offline  # no descarga, solo procesa lo que ya hay
"""
import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Falta Pillow. Instálalo con:  python3 -m pip install pillow")

ROOT = Path(os.environ["SOLIS_ROOT"]).resolve() if os.environ.get("SOLIS_ROOT") else Path(__file__).resolve().parent.parent
RAW = ROOT / "_descargas"
MANUAL = ROOT / "imagenes-originales"
OUT = ROOT / "assets" / "img"
BASE = "https://www.solisimportsa.com/wp-content/uploads/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SolisSiteMigration/1.0)"}

BG = (237, 243, 247)  # --mist
WEBP_Q = 80

# (ruta en el sitio actual, tipo, nombre de salida sin extensión)
# tipos: portada (4:5, 800 px) · linea (4:5, 800 px) · foto (5:4, 1200 px) · video (16:9, 1280 px) · logo
MANIFEST = [
    ("2023/09/fonto-entrada-atramat.jpg", "portada", "atramat"),
    ("2023/10/fonto-entrada-ferno.jpg", "portada", "ferno"),
    ("2023/10/fonto-entrada-ritter.jpg", "portada", "ritter"),
    ("2023/08/fonto-entrada-productos.jpg", "portada", "pegamedical"),
    ("2022/09/portada-myray.jpg", "portada", "myray"),
    ("2022/09/portada-1.jpg", "portada", "fanem"),
    ("2020/07/portada-main.jpg", "portada", "novaerus"),
    ("2020/02/surgiseal-portada.jpg", "portada", "surgiseal"),
    ("2020/02/brix3000-portada.jpg", "portada", "brix3000"),
    # Líneas de producto Atramat
    ("2023/09/absorbibles.jpg", "linea", "absorbibles"),
    ("2023/10/fonto-entrada-quirurgica-no-absorbibles.jpg", "linea", "no-absorbibles"),
    ("2023/10/fonto-entrada-plus.jpg", "linea", "plus"),
    ("2023/10/fonto-entrada-PGA-Rapidjpg.jpg", "linea", "pga-rapid"),
    # Fotos de contenido
    ("2022/09/suturas-seccion.jpg", "foto", "suturas-seccion"),
    ("2022/09/agujas-atramat.jpg", "foto", "agujas-atramat"),
    ("2022/08/PHOTO-2021-05-26-10-18-31.jpg", "foto", "equipo"),
    ("2022/09/calidad-muestra-video-sin-icono.jpg", "video", "calidad-video"),
    # Logo
    ("2022/09/logo@2x-2.png", "logo", "logo"),
]

# Marcas del catálogo (para las miniaturas del filtro)
BRAND_SLUGS = [
    "atramat", "ferno", "ritter", "pegamedical", "myray", "fanem", "novaerus", "surgiseal", "brix3000",
    "sunset", "digitsole", "lasotronix", "hb-fuller", "tur", "vcomin", "trulife", "mir",
    "gv-health", "carestream-dental",
]
RATIOS = {"portada": (4, 5, 800), "linea": (4, 5, 800), "foto": (5, 4, 1200), "video": (16, 9, 1280)}


# ---------------------------------------------------------------- utilidades
def kb(path):
    return path.stat().st_size / 1024


def download(job, retries=3):
    """job = (n, total, url, dest). Descarga, comprueba que sea una imagen válida y reintenta."""
    n, total, url, dest = job
    err = "desconocido"
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            with Image.open(tmp) as im:   # si no es una imagen válida lanza error
                im.verify()
            tmp.replace(dest)
            print(f"  [{n}/{total}] ✓ {dest.name}")
            return None
        except Exception as e:  # noqa: BLE001 - queremos reintentar con cualquier fallo de red o formato
            err = str(e)
            time.sleep(1.5 * attempt)
    print(f"  [{n}/{total}] ✗ {dest.name}  ({err})")
    return url


def open_rgb(path, keep_alpha=False):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if keep_alpha and im.mode in ("RGBA", "LA", "P"):
        return im.convert("RGBA")
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def crop_ratio(im, rw, rh, max_w):
    """Recorta al centro a la proporción rw:rh y reduce a max_w (sin ampliar)."""
    w, h = im.size
    target = rw / rh
    if w / h > target:
        nw = int(h * target)
        box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
    else:
        nh = int(w / target)
        box = (0, (h - nh) // 2, w, (h - nh) // 2 + nh)
    im = im.crop(box)
    if im.width > max_w:
        im = im.resize((max_w, round(max_w * rh / rw)), Image.LANCZOS)
    return im


def contain_on(im, size, bg=(255, 255, 255), pad=0.12):
    """Coloca la imagen completa (sin recortar) centrada sobre un fondo."""
    canvas = Image.new("RGB", size, bg)
    inner = (int(size[0] * (1 - 2 * pad)), int(size[1] * (1 - 2 * pad)))
    im = im.copy()
    im.thumbnail(inner, Image.LANCZOS)
    x, y = (size[0] - im.width) // 2, (size[1] - im.height) // 2
    if im.mode == "RGBA":
        canvas.paste(im, (x, y), im)
    else:
        canvas.paste(im, (x, y))
    return canvas


def save_webp(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=WEBP_Q, method=6)


def find_manual(slug, suffix):
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = MANUAL / f"{slug}-{suffix}.{ext}"
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------- procesos
def process_manifest(force):
    before = after = 0
    for rel, kind, name in MANIFEST:
        raw = RAW / Path(rel).name
        if not raw.exists():
            print(f"  – falta {raw.name}, se omite")
            continue
        folder = {"portada": "brands", "linea": "lines", "foto": "content", "video": "content", "logo": ""}[kind]
        dest = OUT / folder / f"{name}.webp"
        before += kb(raw)
        if dest.exists() and not force:
            after += kb(dest)
            continue
        if kind == "logo":
            im = open_rgb(raw, keep_alpha=True)
            if im.width > 600:
                im = im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS)
            save_webp(im, OUT / "logo.webp")
            (OUT).mkdir(parents=True, exist_ok=True)
            im.save(OUT / "logo.png", optimize=True)
            after += kb(OUT / "logo.webp")
        else:
            rw, rh, mw = RATIOS[kind]
            im = crop_ratio(open_rgb(raw), rw, rh, mw)
            save_webp(im, dest)
            after += kb(dest)
        print(f"  ✓ {dest.relative_to(ROOT)}")
    return before, after


def process_manual(force):
    """Logos y portadas propias de las marcas nuevas (carpeta imagenes-originales/)."""
    if not MANUAL.exists():
        return
    for slug in BRAND_SLUGS:
        logo = find_manual(slug, "logo")
        cover = find_manual(slug, "portada")
        if cover:
            dest = OUT / "brands" / f"{slug}.webp"
            if force or not dest.exists():
                save_webp(crop_ratio(open_rgb(cover), 4, 5, 800), dest)
                print(f"  ✓ portada propia: {dest.relative_to(ROOT)}")
        if logo:
            im = open_rgb(logo, keep_alpha=True)
            save_webp(im if im.width <= 600 else im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS),
                      OUT / "brands" / f"{slug}-logo.webp")
            if not cover:  # sin portada: el logo centrado sobre fondo suave hace de portada
                save_webp(contain_on(im, (800, 1000), BG, 0.15), OUT / "brands" / f"{slug}.webp")
            print(f"  ✓ logo propio: {slug}")


def make_thumbs(force):
    """Miniaturas cuadradas 160x160 para el filtro de marcas."""
    for slug in BRAND_SLUGS:
        dest = OUT / "brands" / f"{slug}-thumb.webp"
        if dest.exists() and not force:
            continue
        logo = find_manual(slug, "logo")
        if logo:
            im = contain_on(open_rgb(logo, keep_alpha=True), (160, 160), (255, 255, 255), 0.12)
        else:
            cover = OUT / "brands" / f"{slug}.webp"
            if not cover.exists():
                continue
            im = crop_ratio(open_rgb(cover), 1, 1, 160)
        save_webp(im, dest)
        print(f"  ✓ miniatura: {dest.relative_to(ROOT)}")


def make_icons(force):
    logo = OUT / "logo.png"
    if not logo.exists():
        return
    im = open_rgb(logo, keep_alpha=True)
    if force or not (ROOT / "favicon.png").exists():
        contain_on(im, (64, 64), (255, 255, 255), 0.06).save(ROOT / "favicon.png", optimize=True)
        contain_on(im, (180, 180), (255, 255, 255), 0.1).save(ROOT / "apple-touch-icon.png", optimize=True)
        print("  ✓ favicon.png y apple-touch-icon.png")
    og = OUT / "og-default.jpg"
    if force or not og.exists():
        canvas = Image.new("RGB", (1200, 630), BG)
        l = im.copy()
        l.thumbnail((820, 300), Image.LANCZOS)
        canvas.paste(l, ((1200 - l.width) // 2, (630 - l.height) // 2), l if l.mode == "RGBA" else None)
        canvas.save(og, "JPEG", quality=85, optimize=True, progressive=True)
        print("  ✓ assets/img/og-default.jpg")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="volver a procesar aunque ya exista el resultado")
    ap.add_argument("--offline", action="store_true", help="no descargar; solo procesar lo que ya está en _descargas/")
    args = ap.parse_args()

    RAW.mkdir(exist_ok=True)
    MANUAL.mkdir(exist_ok=True)

    if not args.offline:
        print("1/4 Descargando imágenes originales…")
        pending = [(BASE + rel, RAW / Path(rel).name) for rel, _, _ in MANIFEST
                   if args.force or not (RAW / Path(rel).name).exists()]
        jobs = [(i + 1, len(pending), u, d) for i, (u, d) in enumerate(pending)]
        failed = []
        if jobs:
            with ThreadPoolExecutor(max_workers=6) as ex:
                failed = [f for f in ex.map(download, jobs) if f]
        print(f"    {len(jobs) - len(failed)} descargadas, {len(failed)} con error, "
              f"{len(MANIFEST) - len(jobs)} ya estaban.")
        if failed:
            print("\n  ⚠ Estas imágenes no se pudieron descargar. Ábrelas en el navegador, guárdalas en la carpeta")
            print("    _descargas con el mismo nombre de archivo y ejecuta de nuevo (usará las que ya tienes):")
            for u in failed:
                print("      " + u)
            print()
    else:
        print("1/4 Modo sin conexión: se usa lo que hay en _descargas/")

    print("2/4 Optimizando imágenes del sitio…")
    before, after = process_manifest(args.force)
    print("3/4 Procesando logos y portadas propias (imagenes-originales/)…")
    process_manual(args.force)
    print("4/4 Miniaturas, favicon e imagen para redes…")
    make_thumbs(args.force)
    make_icons(args.force)

    if before:
        print(f"\nListo. Originales: {before / 1024:.1f} MB → optimizadas: {after / 1024:.1f} MB "
              f"(ahorro del {100 - after / before * 100:.0f} %).")
    print("Revisa el sitio con:  python3 -m http.server 8000   y abre http://localhost:8000")


if __name__ == "__main__":
    main()
