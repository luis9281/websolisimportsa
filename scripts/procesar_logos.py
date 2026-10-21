#!/usr/bin/env python3
"""
Prepara los logos oficiales de las marcas para la web.

Qué hace
  Toma cada archivo de imagenes-originales/logos/<marca>.(svg|png|jpg|webp) y genera
  assets/img/logos/<marca>.svg o assets/img/logos/<marca>.png, listo para mostrarse
  sobre fondo blanco:
    - SVG: se copia tal cual (o con los colores reemplazados, ver RECOLOR_SVG).
    - PNG/JPG/WebP: se recortan los márgenes vacíos, se quita el fondo blanco de los JPG
      y se reduce a 600 px de ancho como máximo.
  Algunas marcas solo publican su logo en blanco (para fondos oscuros). Para esas, los
  píxeles blancos se pintan con el color indicado en RECOLOR y el resto se respeta.

Requisitos
     python -m pip install pillow

Uso (desde la carpeta del proyecto)
     python scripts/procesar_logos.py
"""
import os
import re
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Falta Pillow. Instálalo con:  python -m pip install pillow")

ROOT = Path(os.environ["SOLIS_ROOT"]).resolve() if os.environ.get("SOLIS_ROOT") else Path(__file__).resolve().parent.parent
SRC = ROOT / "imagenes-originales" / "logos"
OUT = ROOT / "assets" / "img" / "logos"
MAX_W = 600

# Logos publicados solo en blanco → (color con que se pinta la parte blanca,
# desde qué fracción del ancho se aplica; sirve para no tocar el ícono de la izquierda)
RECOLOR = {
    "atramat": ((31, 59, 100), 0),
    "ritter": ((29, 43, 79), 0),
    "lasotronix": ((31, 42, 55), 0),
    "digitsole": ((11, 42, 107), 0.2),
}
# SVG publicados en blanco: (regla CSS original, regla nueva)
RECOLOR_SVG = {
    "ferno": [(".cls-2, .cls-3 {\n        fill: #fff;\n      }",
               ".cls-2 { fill: #fff; }\n      .cls-3 { fill: #1a1a1a; }")],
    "trulife": [("fill: #fff;", "fill: #55606e;")],
}


def recolor_white(im, rgb, x_from=0):
    px = im.load()
    for y in range(im.height):
        for x in range(int(im.width * x_from), im.width):
            r, g, b, a = px[x, y]
            if a and min(r, g, b) > 185:
                px[x, y] = (*rgb, a)
    return im


def white_to_alpha(im):
    """Fondo blanco (JPG) → transparente, con borde suave."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            m = min(r, g, b)
            if m > 235:
                px[x, y] = (r, g, b, 0)
            elif m > 200:
                px[x, y] = (r, g, b, int(a * (235 - m) / 35))
    return im


def trim(im):
    box = im.getchannel("A").getbbox()
    return im.crop(box) if box else im


def main():
    if not SRC.is_dir():
        sys.exit(f"No existe {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    done = []
    for f in sorted(SRC.iterdir()):
        slug, ext = f.stem, f.suffix.lower()
        if ext == ".svg":
            dst = OUT / f"{slug}.svg"
            text = f.read_text(encoding="utf-8")
            if re.search(r"<script|on\w+\s*=", text, re.I):
                print(f"  ! {f.name}: contiene scripts, se omite")
                continue
            for old, new in RECOLOR_SVG.get(slug, []):
                text = text.replace(old, new)
            dst.write_text(text, encoding="utf-8")
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            im = Image.open(f).convert("RGBA")
            if ext in (".jpg", ".jpeg"):
                im = white_to_alpha(im)
            if slug in RECOLOR:
                im = recolor_white(im, *RECOLOR[slug])
            im = trim(im)
            if im.width > MAX_W:
                im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
            dst = OUT / f"{slug}.png"
            im.save(dst, optimize=True)
        else:
            continue
        # borra otra versión anterior con distinta extensión
        for old in OUT.glob(slug + ".*"):
            if old != dst:
                old.unlink()
        done.append(dst.name)
        print(f"  ✓ {dst.relative_to(ROOT)}")
    print(f"{len(done)} logos listos en {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
