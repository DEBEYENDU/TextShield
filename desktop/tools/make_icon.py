"""Render the TextShield SVG icon to PNG and ICO."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ICON_DIR = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "textshield_desktop"
    / "resources"
    / "icons"
)
SIZES = [256, 128, 64, 48, 32, 24, 16]


def render_png(svg_path: Path, png_path: Path, size: int) -> None:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer = QSvgRenderer(str(svg_path))
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    if not image.save(str(png_path)):
        raise RuntimeError(f"Could not save {png_path}")


def main() -> int:
    app = QGuiApplication(sys.argv)
    svg_path = ICON_DIR / "textshield.svg"
    png_path = ICON_DIR / "textshield.png"
    ico_path = ICON_DIR / "textshield.ico"
    if not svg_path.exists():
        raise SystemExit(f"Missing source icon: {svg_path}")

    render_png(svg_path, png_path, 256)
    with Image.open(png_path) as image:
        image.save(ico_path, format="ICO", sizes=[(size, size) for size in SIZES])

    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
