"""把规格书某一页（可裁剪）渲染成尺寸图证据 PNG。

用法：
  python tools/render_dim.py ID 页码                      整页预览 → build/preview/ID_p页码.png（不算证据）
  python tools/render_dim.py ID 页码 x0 y0 x1 y1 [名字]    按页面比例(0-1)裁剪 → evidence/ID/dim_名字.png
  python tools/render_dim.py ID 页码 x0 y0 x1 y1 名字 --pdf 路径   用其他条目的 PDF
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    args = sys.argv[1:]
    pdf = None
    if "--pdf" in args:
        i = args.index("--pdf")
        pdf = Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    pid, page = args[0], int(args[1])
    pdf = pdf or ROOT / "evidence" / pid / "datasheet.pdf"
    doc = fitz.open(pdf)
    pg = doc[page - 1]
    r = pg.rect
    if len(args) >= 6:
        x0, y0, x1, y1 = map(float, args[2:6])
        name = args[6] if len(args) > 6 else f"p{page}"
        clip = fitz.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        zoom = max(2.0, 1400 / clip.width)
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        out = ROOT / "evidence" / pid / f"dim_{name}.png"
    else:
        zoom = min(2.5, 1500 / r.width)
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        out = ROOT / "build" / "preview" / f"{pid}_p{page}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    pix.save(out)
    print(out, pix.width, pix.height, f"pages={doc.page_count}")


if __name__ == "__main__":
    main()
