"""Convierte source-prepped.png en un retrato ASCII monocromo que se "teclea" solo.

Cada fila se revela con un clip que barre de izquierda a derecha (con un cursor de
bloque en el borde), escalonadas de arriba abajo. Se imprime una vez y se congela.

Uso: python scripts/make_ascii_svg.py   ->  alisha-ascii.svg
     STATIC=1 python scripts/make_ascii_svg.py   (fotograma final, sin animación)
"""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "alisha-ascii.svg"
STATIC = os.environ.get("STATIC") == "1"
INVERT = os.environ.get("INVERT", "1") == "1"
GAMMA = float(os.environ.get("GAMMA", "1.0"))
LOCAL = float(os.environ.get("LOCAL", "3.0"))

RAMP = " .`:-=+*cs#%@"  # claro (disperso) -> oscuro (denso); el espacio limpia el fondo
COLS = 100
CROP = (0.08, 0.04, 0.92, 0.74)  # izq, arriba, der, abajo (fracciones): cabeza y hombros

# Se diseña al tamaño en que se muestra (370 px en el README) para que la barra de
# título mida lo mismo que en la tarjeta de info.
WIDTH = 370
PAD_X, PAD_TOP, PAD_BOTTOM = 14, 38, 14
CW = (WIDTH - PAD_X * 2) / COLS  # ancho de carácter
LH = CW * 1.75  # alto de línea
FS = CW * 1.68  # tamaño de fuente
BG, BAR, FG, DIM, CURSOR = "#100E24", "#1B1838", "#E4E0FF", "#A7A1CC", "#A07CFF"

START, ROW_DUR, STAGGER = 0.4, 0.22, 0.055


def to_rows() -> list[str]:
    img = Image.open(SRC).convert("L")
    w, h = img.size
    l, t, r, b = CROP
    img = img.crop((int(w * l), int(h * t), int(w * r), int(h * b)))
    rows = round(COLS * img.height / img.width * CW / LH)
    small = img.resize((COLS, rows), Image.LANCZOS)
    # El fondo es blanco puro tras prep_photo: lo marcamos antes de tocar el contraste.
    bg = np.asarray(img.resize((COLS, rows), Image.BOX), dtype=np.float32) >= 246
    small = small.filter(ImageFilter.UnsharpMask(radius=1.2, percent=160, threshold=2))
    a = np.asarray(small, dtype=np.uint8)
    if LOCAL:
        # Ecualización local a resolución de rejilla: los rizos oscuros ganan textura.
        a = cv2.createCLAHE(clipLimit=LOCAL, tileGridSize=(6, 6)).apply(a)
    a = a.astype(np.float32)
    lo, hi = np.percentile(a[~bg], [2, 98])
    a = ((a - lo) / max(hi - lo, 1)).clip(0, 1)
    if INVERT:
        a = 1.0 - a  # texto claro sobre fondo oscuro: lo claro de la foto, denso
    a = a ** GAMMA
    idx = ((1.0 - a) * (len(RAMP) - 1) + 0.5).astype(int).clip(0, len(RAMP) - 1)
    idx[bg] = 0
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build(lines: list[str]) -> str:
    width = PAD_X * 2 + COLS * CW
    height = PAD_TOP + len(lines) * LH + PAD_BOTTOM
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="Retrato ASCII de Alisha">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{width - 20:.0f}a10 10 0 0 1 10 10v16H0z" fill="{BAR}"/>',
        '<circle cx="18" cy="13" r="5" fill="#ff5f56"/><circle cx="34" cy="13" r="5" fill="#ffbd2e"/>'
        '<circle cx="50" cy="13" r="5" fill="#27c93f"/>',
        f'<text x="{width / 2:.0f}" y="17" text-anchor="middle" fill="{DIM}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="11">'
        "alisha@github: ~/retrato</text>",
    ]
    if not STATIC:
        out.append("<defs>")
        for i, line in enumerate(lines):
            y = PAD_TOP + i * LH
            w = len(line) * CW
            begin = START + i * STAGGER
            out.append(
                f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{y:.2f}" width="0" height="{LH:.2f}">'
                f'<animate attributeName="width" from="0" to="{w + 2:.1f}" begin="{begin:.2f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
        out.append("</defs>")

    out.append(
        f'<g fill="{FG}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="{FS:.2f}" xml:space="preserve" style="white-space:pre">'
    )
    for i, line in enumerate(lines):
        if not line:
            continue
        # Los espacios iniciales se colapsan al renderizar: desplaza x y usa NBSP dentro.
        lead = len(line) - len(line.lstrip(" "))
        body = line[lead:].replace(" ", "\u00a0")
        y = PAD_TOP + i * LH + LH * 0.8
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        out.append(
            f'<text x="{PAD_X + lead * CW:.2f}" y="{y:.1f}" textLength="{len(body) * CW:.2f}" '
            f'lengthAdjust="spacingAndGlyphs"{clip}>{escape(body)}</text>'
        )
    out.append("</g>")

    if not STATIC:
        # Cursor de bloque: salta de fila en fila siguiendo el borde del barrido.
        for i, line in enumerate(lines):
            if not line:
                continue
            y = PAD_TOP + i * LH + 0.5
            begin = START + i * STAGGER
            w = len(line) * CW
            out.append(
                f'<rect x="{PAD_X}" y="{y:.1f}" width="{CW:.2f}" height="{LH - 1:.2f}" fill="{CURSOR}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" dur="{ROW_DUR}s"/>'
                f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + w:.1f}" begin="{begin:.2f}s" '
                f'dur="{ROW_DUR}s"/></rect>'
            )
        # Cursor final parpadeando unas veces y luego fijo.
        y = PAD_TOP + len(lines) * LH - LH + 0.5
        last_begin = START + len(lines) * STAGGER + ROW_DUR
        out.append(
            f'<rect x="{PAD_X}" y="{y:.1f}" width="{CW:.2f}" height="{LH - 1:.2f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="opacity" values="1;0;1;0;1" begin="{last_begin:.2f}s" '
            f'dur="2.4s" fill="freeze"/></rect>'
        )
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    lines = to_rows()
    OUT.write_text(build(lines), encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)} ({COLS}x{len(lines)})")


if __name__ == "__main__":
    main()
