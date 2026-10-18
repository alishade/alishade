"""Tarjeta estilo neofetch: rol, stack e hitos, línea a línea.

Uso: python scripts/make_info_card.py   ->  info-card.svg
     STATIC=1 python scripts/make_info_card.py   (fotograma final, sin animación)
"""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

BG, BAR, FG, DIM, RULE = "#100E24", "#1B1838", "#F5F3FF", "#A7A1CC", "#352F63"
ACCENTS = ["#A07CFF", "#FFC83D", "#5C8DFF", "#3FD68F", "#FF7A59", "#FF6FB5"]

USER, HOST = "alisha", "github"

# (clave, valor, color de la clave). Clave vacía = continuación de la línea anterior.
ROWS = [
    ("Rol", "Docente de robótica + desarrolladora de apps", "#A07CFF"),
    ("Base", "Madrid, España", "#A07CFF"),
    ("Ahora", "Robótica educativa con LEGO WeDo en Primaria", "#FFC83D"),
    ("", "Formo a docentes en programación y robótica", "#FFC83D"),
    ("Estudio", "TS en Educación Infantil · EPSUM (en curso)", "#FFC83D"),
    ("Antes", "DAM · Upgrade Hub (2023 – 2025)", "#5C8DFF"),
    ("Stack", "Swift · SwiftUI · TypeScript · Scrum", "#3FD68F"),
    ("Aula", "Scratch · MakeCode Arcade · LEGO WeDo", "#3FD68F"),
    ("Hitos", "1 app de salud creada, lanzada y vendida", "#FF7A59"),
    ("", "6 centros educativos · 2 cursos escolares", "#FF7A59"),
    ("Idiomas", "ES nativo · EN / CA intermedio", "#FF6FB5"),
    ("", "FR · DE · EU · FI · JA básico", "#FF6FB5"),
    ("Contacto", "linkedin.com/in/alishaibell", "#A07CFF"),
    ("", "alishaeditora@icloud.com", "#A07CFF"),
]

W = 490
FS, LH = 12.5, 21
PAD_X, TOP = 20, 50
KEY_W = 82
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
START, STAGGER = 0.5, 0.11
MIN_H = 417  # alto del retrato a 370 px, para que las dos columnas igualen


def build() -> str:
    lines: list[str] = []  # fragmentos <g> por línea, en orden de aparición
    y = TOP

    title = (
        f'<text x="{PAD_X}" y="{y}"><tspan fill="#A07CFF" font-weight="700">{USER}</tspan>'
        f'<tspan fill="{DIM}">@</tspan><tspan fill="#FFC83D" font-weight="700">{HOST}</tspan></text>'
    )
    lines.append(title)
    y += 12
    lines.append(f'<rect x="{PAD_X}" y="{y - 4}" width="{W - PAD_X * 2}" height="1" fill="{RULE}"/>')
    y += LH - 2

    for key, value, color in ROWS:
        k = f'<tspan fill="{color}" font-weight="700">{escape(key)}</tspan>' if key else ""
        lines.append(
            f'<text x="{PAD_X}" y="{y}">{k}</text>'
            f'<text x="{PAD_X + KEY_W}" y="{y}" fill="{FG}">{escape(value)}</text>'
        )
        y += LH

    y += 4
    blocks = "".join(
        f'<rect x="{PAD_X + i * 30}" y="{y - 12}" width="26" height="14" rx="3" fill="{c}"/>'
        for i, c in enumerate(ACCENTS)
    )
    lines.append(blocks)
    height = max(y + 22, MIN_H)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="Ficha de Alisha: rol, stack e hitos">',
    ]
    if not STATIC:
        out.append(
            "<style>.l{opacity:0;animation:in .45s ease-out forwards}"
            "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
            "</style>"
        )
    out += [
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v16H0z" fill="{BAR}"/>',
        '<circle cx="18" cy="13" r="5" fill="#ff5f56"/><circle cx="34" cy="13" r="5" fill="#ffbd2e"/>'
        '<circle cx="50" cy="13" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2:.0f}" y="17" text-anchor="middle" fill="{DIM}" font-family="{MONO}" '
        f'font-size="11">{USER}@{HOST}: ~ $ neofetch</text>',
        f'<g font-family="{MONO}" font-size="{FS}" fill="{FG}">',
    ]
    for i, frag in enumerate(lines):
        if STATIC:
            out.append(f"<g>{frag}</g>")
        else:
            out.append(f'<g class="l" style="animation-delay:{START + i * STAGGER:.2f}s">{frag}</g>')
    out += ["</g>", "</svg>"]
    return "\n".join(out)


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
