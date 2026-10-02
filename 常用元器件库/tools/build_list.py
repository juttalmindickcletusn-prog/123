"""由 parts.csv 生成 常用元器件清单.md（按类别分表，一行一个条目，供选型时快速查）。

用法：python tools/build_list.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader((ROOT / "parts.csv").open(encoding="utf-8-sig")))
    date = max(r["checked_date"] for r in rows)
    out = ["# 常用元器件清单", "",
           f"共 {len(rows)} 条，价格和库存核实于 {date}（立创商城，单价按最小起订档）。完整字段见 parts.csv，带图的版本见 reports/preview.html。",
           "", "级别：A = V1.1 底板实焊验证；B = 按厂家图纸核对，脚本检查通过；C = 厂家图纸缺关键尺寸，到货后要量。", ""]
    cats = []
    for r in rows:
        if r["category"] not in cats:
            cats.append(r["category"])
    cell = lambda s: (s or "").replace("|", "/").replace("\n", " ")
    for c in cats:
        out += [f"## {c}", "", "| 编号 | 名称 | 型号（厂家） | 立创编号 | 单价 | 封装 | 级别 | 注意 |", "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["category"] != c:
                continue
            fp = r["kicad_footprint"].split(":", 1)[-1]
            out.append(f"| {r['id']} | {cell(r['name'])} | {cell(r['part_number'])}（{cell(r['manufacturer'])}） | {r['lcsc_id']} | "
                       f"{cell(r['price_cny'].split('（')[0])} | {cell(fp)} | {r['level']} | {cell(r['pitfalls'])} |")
        out.append("")
    (ROOT / "常用元器件清单.md").write_text("\n".join(out), encoding="utf-8")
    print(f"常用元器件清单.md：{len(rows)} 条，{len(cats)} 类")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
