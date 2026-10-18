"""Descarga el calendario público de contribuciones (sin token) y calcula estadísticas.

GitHub sirve el calendario como HTML en https://github.com/users/<usuario>/contributions,
el mismo fragmento que usa la página de perfil.

Uso: python scripts/fetch_contributions.py   ->  data/contributions.json
"""
from __future__ import annotations

import json
import os
import re
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USERNAME = os.environ.get("GH_USERNAME", "alishade")


def fetch_days() -> list[dict]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    resp = requests.get(url, headers={"User-Agent": f"{USERNAME}-profile-readme"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # El número exacto vive en el <tool-tip for="contribution-day-component-x-y">.
    counts: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        m = re.match(r"\s*(\d[\d,]*)\s+contributions?", tip.get_text())
        counts[target] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append(
            {
                "date": td["data-date"],
                "level": int(td.get("data-level", 0)),
                "count": counts.get(td.get("id"), 0),
            }
        )
    if not days:
        raise SystemExit("no se encontraron días en el calendario: ¿ha cambiado el HTML de GitHub?")
    days.sort(key=lambda d: d["date"])
    return days


def stats(days: list[dict]) -> dict:
    by_date = {d["date"]: d["count"] for d in days}
    total = sum(by_date.values())

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # Racha actual: si hoy aún no hay nada, se cuenta desde ayer.
    cur_day = date.fromisoformat(days[-1]["date"])
    if not by_date.get(cur_day.isoformat()):
        cur_day -= timedelta(days=1)
    current = 0
    while by_date.get(cur_day.isoformat()):
        current += 1
        cur_day -= timedelta(days=1)

    best = max(days, key=lambda d: d["count"])
    monthly: OrderedDict[str, int] = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main() -> None:
    days = fetch_days()
    data = {
        "username": USERNAME,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "stats": stats(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    s = data["stats"]
    print(f"escrito {OUT.relative_to(ROOT)}: {s['total']} contribuciones, {len(days)} días")


if __name__ == "__main__":
    main()
