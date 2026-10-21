# Solis Import S.A. — Guía de productos y plan de contenido

Documento de trabajo para ampliar el catálogo del sitio: agregar productos nuevos y completar la información de cada uno.
(El `.htaccess` bloquea los archivos `.md`, así que este archivo no se publica aunque se suba al hosting).

---

## 1. Cómo está armado el sitio

Sitio estático en HTML puro, sin frameworks. Hosting Apache (cPanel). Las páginas de marcas, el catálogo y el inicio **se generan** con `scripts/build.py` a partir de `data/brands.json`.

| Ruta | Qué es | ¿Se genera? |
|---|---|---|
| `index.html` | Inicio: muro de logos en la portada, tarjetas y franja de marcas | Sí |
| `productos/index.html` | Catálogo: filtro por marca + buscador (busca también por nombre de producto) | Sí |
| `project/<slug>/index.html` | Una página por marca o línea de producto | Sí |
| `project/tur-gmbh/`, `project/tur-therapy/` | Redirigen a `project/tur/` (y 301 en `.htaccess`) | Sí |
| `sitemap.xml` | Solo páginas con contenido | Sí |
| `quienes-somos/`, `contactenos/`, `404.html` | Páginas fijas | No, se editan a mano |
| `assets/css/style.css` | Estilos de todo el sitio | — |
| `assets/js/main.js` | Menú, diapositivas, filtro del catálogo, formulario | — |
| `assets/img/logos/` | **Logos oficiales** de las 19 marcas, listos para la web | Con `procesar_logos.py` |
| `imagenes-originales/logos/` | Logos tal como se descargaron de cada fabricante (bloqueada al público) | — |
| `assets/img/brands/` | Fotos de portada de marca (`<slug>.webp`, 4:5) | Con `descargar_imagenes.py` |
| `data/brands.json` | **Fuente de datos** de marcas, líneas y productos (bloqueada al público) | — |

### Scripts

| Script | Para qué |
|---|---|
| `python scripts/build.py` | Regenera el sitio desde el JSON. **Correr después de cada cambio en el JSON.** |
| `python scripts/build.py --serve` | Regenera y levanta un servidor de prueba en http://localhost:8000 |
| `python scripts/procesar_logos.py` | Convierte los logos de `imagenes-originales/logos/` en `assets/img/logos/` (recorta, quita fondo blanco, oscurece los logos que solo existen en blanco) |
| `python scripts/descargar_imagenes.py` | Descarga y optimiza fotos de portada a WebP |

Requisito: `python -m pip install pillow` (solo para los scripts de imágenes; `build.py` no necesita nada extra).

---

## 2. Modelo de datos (`data/brands.json`)

```jsonc
{
  "site":      { ...datos de contacto, "lastmod": "2026-10-21" },
  "brands":    [ ...marca ],
  "lines":     [ ...línea (sub-página de una marca, ej. suturas de Atramat) ],
  "redirects": { "project/tur-gmbh/": "project/tur/" }
}
```

### Marca
```jsonc
{
  "slug": "ferno",                       // carpeta: project/ferno/
  "name": "Ferno",
  "area": "Atención de emergencias",     // etiqueta en tarjetas y filtro
  "tagline": "Equipo para atención de emergencias y trauma",
  "meta": "Texto para Google (≈150 caracteres)",
  "has_content": true,                   // false = página "Información próximamente" + noindex
  "cover": "ferno",                      // opcional: assets/img/brands/ferno.webp. Sin foto se muestra el logo
  "logo": "ferno.svg",                   // assets/img/logos/ferno.svg
  "logo_wall": false,                    // opcional: no mostrarla en el muro de logos de la portada
  "website": "https://www.ferno.com/",   // enlace "Sitio oficial" en la página de la marca
  "description": ["Párrafo 1", "Párrafo 2"],
  "highlights": [ { "value": "700 lb", "label": "capacidad de la camilla..." } ],
  "products": [ ...producto ],
  "lines": ["slug-de-linea", ...]        // opcional, solo Atramat
}
```

### Producto
```jsonc
{
  "name": "kimatur · Ondas de choque",   // obligatorio
  "desc": "Descripción corta, 1–3 frases", // obligatorio
  "models": ["kimatur PRIME", "kimatur GO"], // opcional: se muestran como etiquetas
  "datasheet": true,                      // opcional: el botón dice "Pedir ficha técnica"
  "link": "pga-rapid"                     // opcional: enlaza a otra página de project/
}
```

Cada producto se muestra como una fila con título, descripción, modelos y botón **Cotizar** (WhatsApp con el nombre del producto y la marca ya escritos).

---

## 3. Estado actual del catálogo (21-10-2026)

Las **19 marcas tienen página con contenido** y logo oficial.

| Marca | Área | Productos | Foto de portada |
|---|---|---|---|
| Atramat | Suturas quirúrgicas | 7 líneas, 26 productos | Sí |
| Ferno | Atención de emergencias | 4 | Sí |
| Ritter | Odontología | 1 | Sí |
| Pega Medical | Ortopedia pediátrica | 5 | Sí |
| MyRay | Radiología dental | 5 | Sí |
| Fanem | Neonatología y hospitalario | 4 | Sí |
| Novaerus | Desinfección de aire | 3 | Sí |
| SurgiSeal | Cierre de heridas | 4 (características) | Sí |
| Brix 3000 | Odontología | 3 (características) | Sí |
| Sunset Healthcare | Insumos respiratorios y heridas | 6 | No (logo) |
| Digitsole | Análisis de la marcha | 4 | No (logo) |
| Lasotronix | Láseres dentales y médicos | 5 | No (logo) |
| H.B. Fuller | Adhesivos médicos | 4 | No (logo) |
| TUR | Rehabilitación y fisioterapia | 6 | No (logo) |
| Vcomin | Doppler fetal y oximetría | 5 | No (logo) |
| Trulife | Ortesis, prótesis y cuidado de presión | 6 | No (logo) |
| MIR | Espirometría y oximetría | 7 | No (logo) |
| GV Health | Control de infecciones e higiene | 6 | No (logo) |
| Carestream Dental | Imagen dental digital | 7 | No (logo) |

El contenido de las 10 marcas nuevas se redactó a partir de los sitios oficiales de cada fabricante (octubre 2026). **Conviene que Solis confirme qué productos de cada marca vende realmente en Panamá** y quite los que no maneje.

### Origen de los logos

Todos se descargaron de los sitios oficiales. Casos especiales:

| Marca | Nota |
|---|---|
| Atramat, Ritter, Lasotronix, Digitsole, Ferno, Trulife | El fabricante solo publica el logo en blanco; `procesar_logos.py` pinta la parte blanca de un color oscuro |
| Pega Medical | Su sitio ahora usa la marca **OrthoPediatrics Canada** (Pega fue adquirida); se usó ese logo |
| SurgiSeal | No hay logo propio publicado; se usó el de **H.B. Fuller Medical Adhesive Technologies** (su fabricante). Si Solis tiene el logo de SurgiSeal, reemplazar `imagenes-originales/logos/surgiseal.png` |
| Vcomin | Solo existe en JPG con fondo blanco; el script quita el fondo |

### Fotos de uso libre

| Archivo | Uso | Fuente | Licencia |
|---|---|---|---|
| `assets/img/content/hero-equipos.webp` | Fondo de la primera diapositiva del inicio (con atenuación clara) | Quirófano, foto de Arseny Togulev en Unsplash — https://unsplash.com/photos/DE6rYp1nAho (original en `imagenes-originales/fotos/`) | Licencia Unsplash: uso comercial gratuito, sin atribución obligatoria |

### Líneas de suturas Atramat (plantilla "suturas")

Las 7 líneas de `lines` con `"template": "suturas"` se muestran con un diseño propio inspirado en atramat.com (fondo blanco, azul `#1f2a5a`, turquesa `#00a3c4` y un color por sutura, igual al de su caja). El orden del submenú **Suturas** sale de `"menu_suturas"`.

```jsonc
{
  "slug": "suturas-quirurgicas-absorbibles", "nav": "Suturas absorbibles",   // texto en el submenú
  "template": "suturas", "parent": "atramat", "cover": "absorbibles",
  "callout": { "title": "...", "text": ["..."], "list": ["..."] },          // opcional (bloque destacado)
  "products": [{
    "id": "pga-rapid",                      // ancla: project/<línea>/#pga-rapid
    "name": "PGA Rapid", "subtitle": "Ácido poliglicólico de absorción rápida",
    "color": "#e73745",                     // color de la ficha
    "indication": "...",
    "stats": [{ "label": "Absorción total", "value": "45–60 días" }],
    "tech": [["Composición", "..."], ["Absorción", "Hidrólisis"]],
    "features": ["..."], "models": ["..."], "image": "assets/img/content/..."
  }]
}
```

Fuente del contenido: fichas oficiales de atramat.com (octubre 2026), traducidas. Las fotos de portada de Mínima invasión, Propymesh, Agujas y Bonewax son del sitio de Atramat (originales en `imagenes-originales/atramat/`); algunas tienen texto en inglés.

---

## 4. Información a recopilar por producto

Plantilla para llenar antes de cargar cada producto. Lo marcado con * es lo mínimo.

```
Marca*:
Nombre comercial / modelo*:
Categoría / uso*:            (ej. "Ventilador de transporte")
Descripción corta*:          (1–3 frases, en lenguaje claro)
Modelos / referencias:       (van en "models")
Características clave:       (3–6 viñetas)
Especificaciones técnicas:   (dimensiones, peso, capacidad, potencia, materiales…)
Aplicaciones / especialidad: (UCI, quirófano, consultorio dental…)
Registro sanitario MINSA:    (n.º, si aplica)
Certificaciones:             (FDA, CE, ISO 13485…)
Garantía:
Ficha técnica (PDF / URL):
Foto(s):                     (fondo limpio, mínimo 1200 px)
Video (YouTube):
```

Si un producto acumula mucha información, conviene darle su **propia página** como línea (en `lines`, con `parent`), como ya se hizo con PGA Rapid, y enlazarla con `"link"`.

---

## 5. Pasos para agregar un producto

1. Llenar la plantilla de la sección 4.
2. Agregar el producto al arreglo `products` de su marca en `data/brands.json`.
3. Marca nueva: agregarla a `brands` con todos sus campos, poner su logo en `imagenes-originales/logos/<slug>.png|svg` y correr `python scripts/procesar_logos.py`.
4. Foto de portada (opcional): `imagenes-originales/<slug>-portada.jpg` y `python scripts/descargar_imagenes.py --offline`; luego `"cover": "<slug>"` en el JSON.
5. `python scripts/build.py --serve` y revisar en http://localhost:8000 (textos, botón Cotizar, filtro y búsqueda, vista móvil).
6. Subir al hosting los archivos que cambiaron (HTML generados, `sitemap.xml`, imágenes nuevas).

> El formulario de contacto necesita PHP, así que en el servidor de prueba no envía mensajes; en el hosting sí.

---

## 6. Pendientes / prioridades

- [x] Recrear `build.py` (generador del sitio).
- [x] Logos oficiales de las 19 marcas en `assets/img/logos/`.
- [x] Páginas con contenido para las 10 marcas que no tenían.
- [x] Resolver `tur-gmbh` / `tur-therapy` (redirigen a `project/tur/`).
- [ ] Confirmar con Solis los productos que realmente se venden de cada marca nueva.
- [ ] Fotos de portada para las 10 marcas nuevas (hoy muestran el logo).
- [ ] Logo propio de SurgiSeal.
- [ ] SurgiSeal y Brix 3000: convertir "características" en productos reales (presentaciones).
- [ ] Ampliar marcas con pocos productos (Ritter: 1).
- [ ] Fotos por producto (hoy solo hay portadas de marca).

---

## 7. Registro de cambios

| Fecha | Cambio |
|---|---|
| 2026-10-21 | Creación de este documento |
| 2026-10-21 | `scripts/build.py` y `scripts/procesar_logos.py`; logos oficiales de las 20 marcas; contenido para Sunset, Digitsole, Lasotronix, H.B. Fuller, TUR, Vcomin, Trulife, MIR, GV Health y Carestream Dental; muro de logos en la portada; redirecciones de TUR |
| 2026-10-21 | Se eliminó Magnamed (ya no se distribuye): datos, página, imágenes, logo, formulario de contacto y script de imágenes; `/project/magnamed/` redirige al catálogo |
| 2026-10-21 | Foto de fondo (Unsplash) con atenuación en la primera diapositiva del inicio |
| 2026-10-21 | Submenú Suturas con 7 líneas Atramat (absorbibles, no absorbibles, Plus, mínima invasión, Propymesh, agujas, bonewax) con fichas técnicas; PGA Rapid se integró a absorbibles (redirección 301) |
