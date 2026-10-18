"""Prepara una foto para convertirla en arte ASCII.

1. Aísla a la persona del fondo (rembg si está instalado; si no, GrabCut de OpenCV,
   que funciona bien con fondos lisos).
2. Sube el contraste local con CLAHE para que una cara con luz plana tenga
   luces y sombras.
3. Compone sobre blanco puro para que el fondo caiga en el extremo vacío de la rampa.

Uso: python scripts/prep_photo.py source-photo.jpg  ->  source-prepped.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"
MAX_SIDE = 900


def subject_mask(rgb: np.ndarray) -> np.ndarray:
    """Devuelve una máscara 0..1 (float) de la persona."""
    try:
        from rembg import remove  # opcional: descarga un modelo de ~170 MB

        rgba = np.array(remove(Image.fromarray(rgb)))
        return rgba[:, :, 3].astype(np.float32) / 255.0
    except ImportError:
        pass

    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.04), int(h * 0.03), int(w * 0.92), h - int(h * 0.03) - 1)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # Quédate con la mancha más grande y rellena huecos.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(labels == biggest, 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    fg = cv2.GaussianBlur(fg, (7, 7), 0)
    return fg.astype(np.float32) / 255.0


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("uso: python scripts/prep_photo.py <foto>")
    img = Image.open(sys.argv[1]).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    rgb = np.array(img)

    alpha = subject_mask(rgb)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    out = gray * alpha + 255.0 * (1.0 - alpha)
    Image.fromarray(out.clip(0, 255).astype(np.uint8), "L").save(OUT)
    print(f"escrito {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
