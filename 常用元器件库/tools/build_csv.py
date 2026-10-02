"""由 src/*.yaml（人工核对的数据）+ evidence/<id>/jlc.json（接口核实的型号、价格、库存）生成 parts.csv。

型号、厂家、价格、库存、规格书链接一律取自 jlc.json，不手填，避免抄错。
用法：python tools/build_csv.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "id", "category", "name", "part_number", "manufacturer", "lcsc_id", "jlc_library", "price_cny", "stock",
    "taobao_keyword", "taobao_price", "alternatives", "key_params", "supply", "logic_level", "pin_count", "pinout",
    "pitch_mm", "row_spacing_mm", "lead_size_mm", "hole_mm", "pad_mm", "body_mm", "mount", "seated_height_mm",
    "kicad_symbol", "kicad_footprint", "kicad_3d", "datasheet_url", "dim_source", "evidence", "level", "pitfalls",
    "checked_date", "notes",
    # 机器检查用的附加列
    "polarized", "lead_max_mm", "check_pads", "pdf_keyword", "ring_min_mm",
]
MANUAL = ["key_params", "supply", "logic_level", "pin_count", "pinout", "pitch_mm", "row_spacing_mm", "lead_size_mm",
          "body_mm", "mount", "seated_height_mm", "kicad_symbol", "kicad_footprint", "dim_source",
          "level", "pitfalls", "notes", "taobao_keyword"]
LIB = {"base": "基础库", "expand": "扩展库"}


def model_of(fp_ref: str) -> str:
    if ":" not in fp_ref:
        return ""
    lib, name = fp_ref.split(":", 1)
    path = (ROOT / "kicad" / "StudentHW.pretty" if lib == "StudentHW" else
            paths.FP_OFF / f"{lib}.pretty") / f"{name}.kicad_mod"
    if not path.exists():
        return ""
    m = re.findall(r'\(model "([^"]+)"', path.read_text(encoding="utf-8"))
    return ";".join(m)


def fp_file(fp_ref: str) -> Path | None:
    if ":" not in fp_ref:
        return None
    lib, name = fp_ref.split(":", 1)
    path = (ROOT / "kicad" / "StudentHW.pretty" if lib == "StudentHW" else
            paths.FP_OFF / f"{lib}.pretty") / f"{name}.kicad_mod"
    return path if path.exists() else None


def holes_pads(fp_ref: str) -> tuple[str, str]:
    """从封装文件读出孔径和焊盘尺寸（不手填，保证与封装一致）。"""
    path = fp_file(fp_ref)
    if path is None:
        return "", ""
    text = path.read_text(encoding="utf-8")
    holes, pads = [], []
    for chunk in text.split('(pad "')[1:]:
        num, rest = chunk.split('"', 1)
        if not num:
            continue
        kind = rest.split()[0]
        size = re.search(r"\(size ([\d.]+) ([\d.]+)\)", rest)
        drill = re.search(r"\(drill (oval )?([\d.]+)(?: ([\d.]+))?\)", rest)
        sz = f"{float(size.group(1)):g}×{float(size.group(2)):g}" if size else "?"
        if kind == "smd":
            pads.append(f"贴片 {sz}")
        elif drill:
            h = f"{float(drill.group(2)):g}" + (f"×{float(drill.group(3)):g} 槽" if drill.group(1) else "")
            holes.append(h)
            pads.append(sz)
    uniq = lambda xs: "、".join(dict.fromkeys(xs))
    return uniq(holes) or "无（贴片）", uniq(pads)


def price(rec: dict) -> str:
    if rec.get("cny_price"):
        return f"¥{rec['cny_price']}@{rec.get('cny_step') or 1}+（立创商城）"
    if rec.get("usd_prices"):
        n, p = rec["usd_prices"][0]
        return f"${p}@{n}+（嘉立创海外价，美元）"
    return "未查到"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parts = []
    for f in sorted((ROOT / "src").glob("*.yaml")):
        parts += yaml.safe_load(f.read_text(encoding="utf-8")) or []
    rows, problems = [], []
    for p in parts:
        ev = ROOT / "evidence" / p["id"]
        jl = json.loads((ev / "jlc.json").read_text(encoding="utf-8")) if (ev / "jlc.json").exists() else {"parts": {}}
        main_rec = jl["parts"].get(p.get("lcsc", ""), {})
        alts = []
        for a in p.get("alternatives") or []:
            r = jl["parts"].get(a.get("lcsc", ""), {})
            if r:
                alts.append(f"{r['mpn']}（{r['brand']}）/ {r['code']}" + (f"：{a['note']}" if a.get("note") else ""))
            elif a.get("text"):
                alts.append(a["text"])
        row = {k: "" for k in FIELDS}
        row.update({
            "id": p["id"], "category": p["category"], "name": p["name"],
            "part_number": p.get("part_number") or main_rec.get("mpn", ""),
            "manufacturer": p.get("manufacturer") or main_rec.get("brand", ""),
            "lcsc_id": p.get("lcsc", "") or "无",
            "jlc_library": LIB.get(main_rec.get("library"), "不适用"),
            "price_cny": p.get("price") or price(main_rec),
            "stock": p.get("stock") or (f"立创商城 {main_rec['szlcsc_stock']}，嘉立创 {main_rec['jlc_stock']}" if main_rec.get("szlcsc_stock")
                                      else (f"嘉立创 {main_rec.get('jlc_stock')}" if main_rec else "未查到")),
            "taobao_price": p.get("taobao_price", "未查询（淘宝需登录，按关键词自查）"),
            "alternatives": "；".join(alts) or p.get("alternatives_text", "无合适替代"),
            "datasheet_url": p.get("datasheet_url") or main_rec.get("datasheet", ""),
            "checked_date": jl.get("date", ""),
            "polarized": p.get("polarized", "否"),
            "lead_max_mm": str(p.get("lead_max_mm", "")),
            "check_pads": p.get("check_pads", "1,2"),
            "pdf_keyword": p.get("pdf_keyword", ""),
            "ring_min_mm": str(p.get("ring_min_mm", "")),
        })
        for k in MANUAL:
            v = p.get(k)
            if v is None:
                problems.append(f"{p['id']}: 缺 {k}")
                v = ""
            row[k] = str(v)
        hm, pm = holes_pads(row["kicad_footprint"])
        row["hole_mm"] = str(p.get("hole_mm") or hm or "不适用")
        row["pad_mm"] = str(p.get("pad_mm") or pm or "不适用")
        row["kicad_3d"] = p.get("kicad_3d") or model_of(row["kicad_footprint"]) or "无"
        files = sorted(x.relative_to(ROOT).as_posix() for x in ev.glob("*") if x.suffix in (".pdf", ".png", ".txt")) if ev.exists() else []
        files += p.get("evidence_extra", [])
        row["evidence"] = ";".join(files)
        rows.append(row)
    with (ROOT / "parts.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    for x in problems:
        print("缺字段", x)
    print(f"写出 parts.csv：{len(rows)} 条，缺字段 {len(problems)} 处")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
