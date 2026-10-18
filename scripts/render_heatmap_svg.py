"""Dibuja data/contributions.json como el calendario de 53 semanas × 7 días.

Las casillas aparecen una vez en diagonal (semana + día) y se quedan fijas.

Uso: python scripts/render_heatmap_svg.py   ->  contrib-heatmap.svg
     STATIC=1 python scripts/render_heatmap_svg.py   (fotograma final, sin animación)
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

# nada -> lo más brillante (el nivel 5 es un extremo neón para los días récord)
PALETTE = ["#25214A", "#3B2F7A", "#5B45B0", "#7E5FE6", "#A07CFF", "#D9C8FF"]
BG, BAR, FG, DIM = "#100E24", "#1B1838", "#F5F3FF", "#A7A1CC"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W = 860
CELL, GAP = 12, 3
PITCH = CELL + GAP
LEFT, TOP = 50, 64
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DAY_LABELS = {1: "lun", 3: "mié", 5: "vie"}
START, STEP = 0.4, 0.028


def level(count: int, top: int, gh_level: int) -> int:
    if not count:
        return 0
    if count >= top and top > 0:
        return 5
    return max(1, min(4, gh_level))


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_date(iso: str, year: bool = True) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


def build(data: dict) -> str:
    days = data["days"]
    s = data["stats"]
    first = date.fromisoformat(days[0]["date"])
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    top = max(d["count"] for d in days)

    cells, month_labels = [], []
    last_month = None
    for d in days:
        dt = date.fromisoformat(d["date"])
        week = (dt - sunday).days // 7
        dow = (dt.weekday() + 1) % 7  # domingo = 0, como en GitHub
        x, y = LEFT + week * PITCH, TOP + dow * PITCH
        lv = level(d["count"], top, d["level"])
        anim = "" if STATIC else f' class="c" style="animation-delay:{START + (week + dow) * STEP:.2f}s"'
        title = f"{d['count']} contribuciones el {fmt_date(d['date'])}"
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[lv]}"{anim}>'
            f"<title>{title}</title></rect>"
        )
        if dt.day <= 7 and dow == 0 and dt.month != last_month:
            last_month = dt.month
            if week < 52:
                month_labels.append((x, MONTHS[dt.month - 1]))

    grid_bottom = TOP + 7 * PITCH - GAP
    height = grid_bottom + 58

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
        f'role="img" aria-label="{fmt(s["total"])} contribuciones en el último año">',
    ]
    if not STATIC:
        reveal_end = START + (52 + 6) * STEP + 0.4
        out.append(
            "<style>"
            ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
            "animation:drop .35s cubic-bezier(.2,.8,.2,1) forwards}"
            "@keyframes drop{from{opacity:0;transform:translateY(-7px) scale(.6)}"
            "to{opacity:1;transform:none}}"
            f".f{{opacity:0;animation:fade .5s ease-out {reveal_end:.2f}s forwards}}"
            "@keyframes fade{to{opacity:1}}"
            "</style>"
        )
    out += [
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v16H0z" fill="{BAR}"/>',
        '<circle cx="18" cy="13" r="5" fill="#ff5f56"/><circle cx="34" cy="13" r="5" fill="#ffbd2e"/>'
        '<circle cx="50" cy="13" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2:.0f}" y="17" text-anchor="middle" fill="{DIM}" font-family="{MONO}" '
        f'font-size="11">alisha@github: ~ $ ./contribuciones.sh</text>',
        f'<g font-family="{MONO}" font-size="10" fill="{DIM}">',
    ]
    for x, name in month_labels:
        out.append(f'<text x="{x}" y="{TOP - 8}">{name}</text>')
    for dow, name in DAY_LABELS.items():
        out.append(f'<text x="{LEFT - 8}" y="{TOP + dow * PITCH + 9.5}" text-anchor="end">{name}</text>')
    out.append("</g>")
    out += cells

    # Pie: total + rachas a la izquierda, leyenda Menos → Más a la derecha.
    fy = grid_bottom + 30
    best = s["best_day"]
    summary = (
        f'<tspan fill="{FG}" font-weight="700">{fmt(s["total"])}</tspan> contribuciones en el último año'
        f'  ·  racha <tspan fill="{FG}">{s["current_streak"]}</tspan>'
        f'  ·  máx. <tspan fill="{FG}">{s["longest_streak"]}</tspan>'
    )
    if best["count"]:
        summary += f'  ·  mejor día <tspan fill="{FG}">{best["count"]}</tspan> ({fmt_date(best["date"], year=False)})'
    out.append(
        f'<g class="f" font-family="{MONO}" font-size="11" fill="{DIM}">'
        f'<text x="{LEFT}" y="{fy}">{summary}</text>'
    )
    lx = W - 24 - len(PALETTE) * PITCH - 36
    out.append(f'<text x="{lx - 8}" y="{fy}" text-anchor="end">Menos</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + i * PITCH}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * PITCH + 5}" y="{fy}">Más</text>')
    out += ["</g>", "</svg>"]
    return "\n".join(out)


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
