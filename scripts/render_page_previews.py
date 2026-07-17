#!/usr/bin/env python3
"""Render configured preview and hybrid pages to WebP without altering the PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "source" / "policy-agri-loan-handbook-114.pdf"
RULES = ROOT / "data" / "114" / "page-rendering-rules.json"
PAGES = ROOT / "data" / "114" / "pages.json"
OUTPUT = ROOT / "assets" / "page-previews" / "114"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    pages = json.loads(PAGES.read_text(encoding="utf-8"))
    page_by_number = {p["pdfPage"]: p for p in pages}
    configured = {item["pdfPage"]: item for item in rules["pages"]}
    targets = sorted(n for n, item in configured.items() if item["renderMode"] in {"preview", "hybrid"})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(PDF)
    width, quality = rules["preview"]["width"], rules["preview"]["quality"]
    manifest = []
    for number in targets:
        source_page = doc[number - 1]
        page_width, page_height = source_page.get_size()
        height = round(width * page_height / page_width)
        image = source_page.render(scale=width / page_width, fill_color=(255, 255, 255, 255)).to_pil().convert("RGB")
        if image.size != (width, height):
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        target = OUTPUT / f"pdf-page-{number:03d}.webp"
        image.save(target, "WEBP", quality=quality, method=6, exact=True, exif=b"")
        stats = ImageStat.Stat(image.convert("L"))
        manifest.append({
            "pdfPage": number, "printedPage": page_by_number[number]["printedPage"],
            "renderMode": configured[number]["renderMode"], "file": target.name,
            "width": image.width, "height": image.height, "sha256": sha256(target),
            "sourcePdfSha256": sha256(PDF), "meanLuminance": round(stats.mean[0], 2),
            "reason": configured[number]["reason"],
        })
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered {len(manifest)} page previews")


if __name__ == "__main__":
    main()
