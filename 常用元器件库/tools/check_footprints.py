"""逐条检查 parts.csv 引用的封装（用 KiCad 自带 Python 运行：D:/kicad/bin/python.exe）。

检查项（任一不过即报错）：
  1. 封装文件存在；
  2. 焊盘编号集合大小 = pin_count（同号焊盘算一个；编号为空的机械孔不计）；
  3. 脚距：check_pads 指定的两焊盘中心距 = pitch_mm（±0.02，能分出 XH 的 2.50 和 2.54）；
  4. 孔径 ≥ lead_max_mm + 0.2；
  5. 环宽：孔 ≤0.9 mm 时 ≥0.4，孔更大时 ≥0.5（A 级封装豁免，已实物验证）；
     脚距放不下大焊盘的（排针、XH/PH 等），可在 ring_min_mm 写更小的下限，notes 必须含"环宽"说明理由；
  6. 有极性的条目（polarized=是）：1 脚为方形/圆角方形焊盘；
  7. 有 F.Courtyard 和 F.Fab 图形；
  8. 3D 模型文件存在（kicad_3d 写"无"的条目除外，需在 notes 说明）。
  kicad_footprint 写"不适用"的配件（如跳线帽）跳过以上检查，但 notes 必须含"不上板"。

用法：D:/kicad/bin/python.exe tools/check_footprints.py [parts.csv]
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = paths.FP_OFF
OFFICIAL_3D = str(paths.MODELS_3D)
LOCAL = ROOT / "kicad" / "StudentHW.pretty"


def fp_path(ref: str) -> tuple[Path, str] | None:
    if ":" not in ref:
        return None
    lib, name = ref.split(":", 1)
    return (LOCAL if lib == "StudentHW" else OFFICIAL / f"{lib}.pretty"), name


def resolve_3d(path: str) -> str:
    for var in ("${KICAD10_3DMODEL_DIR}", "${KICAD9_3DMODEL_DIR}", "${KICAD8_3DMODEL_DIR}"):
        path = path.replace(var, OFFICIAL_3D)
    return path.replace("${STUDENTHW_DIR}", str(ROOT))


def num(s: str) -> float | None:
    m = re.search(r"\d+(\.\d+)?", s or "")
    return float(m.group(0)) if m else None


def check_row(row: dict) -> tuple[list[str], dict]:
    errs: list[str] = []
    info: dict = {}
    if row["kicad_footprint"].startswith("不适用"):
        return ([] if "不上板" in row["notes"] else ["封装写不适用，但 notes 未说明不上板"]), info
    loc = fp_path(row["kicad_footprint"])
    if loc is None:
        return [f"封装字段无效: {row['kicad_footprint']}"], info
    lib, name = loc
    if not (lib / f"{name}.kicad_mod").exists():
        return [f"封装不存在: {row['kicad_footprint']}"], info
    fp = pcbnew.FootprintLoad(str(lib), name)
    pads = list(fp.Pads())
    numbers = {p.GetNumber() for p in pads if p.GetNumber()}
    info["pads"] = sorted(numbers)
    try:
        want = int(row["pin_count"])
    except ValueError:
        want = -1
    if want != len(numbers):
        errs.append(f"焊盘编号数 {len(numbers)} ≠ pin_count {row['pin_count']}")
    # 脚距
    pair = (row.get("check_pads") or "1,2").split(",")
    pitch = num(row["pitch_mm"])
    byno = {}
    for p in pads:
        byno.setdefault(p.GetNumber(), p)
    if pitch is not None and len(pair) == 2 and all(x in byno for x in pair):
        a, b = byno[pair[0]].GetPosition(), byno[pair[1]].GetPosition()
        d = math.hypot(a.x - b.x, a.y - b.y) / 1e6
        info["pitch_measured"] = round(d, 3)
        if abs(d - pitch) > 0.02:
            errs.append(f"脚距 {d:.3f} ≠ CSV {pitch}（焊盘 {pair[0]}-{pair[1]}）")
    elif pitch is not None:
        errs.append(f"无法测脚距：焊盘 {pair} 不存在")
    # 孔径与环宽
    lead = num(row.get("lead_max_mm", ""))
    a_level = row["level"] == "A"
    for p in pads:
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH or not p.GetNumber():
            continue
        d = p.GetDrillSize()
        hole = min(d.x, d.y) / 1e6
        size = p.GetSize()
        ring = (min(size.x, size.y) / 1e6 - hole) / 2
        if lead is not None and hole + 1e-6 < lead + 0.2:
            errs.append(f"焊盘{p.GetNumber()} 孔 {hole:.2f} < 引脚 {lead}+0.2")
        need = 0.4 if hole <= 0.9 + 1e-6 else 0.5
        if num(row.get("ring_min_mm", "")) is not None:
            need = num(row["ring_min_mm"])
            if "环宽" not in row["notes"]:
                errs.append("ring_min_mm 放宽了环宽，但 notes 没写理由")
        if not a_level and ring + 1e-6 < need:
            errs.append(f"焊盘{p.GetNumber()} 环宽 {ring:.2f} < {need}（孔 {hole:.2f}）")
    # 1 脚方焊盘
    if row.get("polarized") == "是":
        p1 = byno.get("1")
        if p1 is None or p1.GetShape() not in (pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_ROUNDRECT):
            errs.append("有极性但 1 脚不是方焊盘")
    layers = {g.GetLayerName() for g in fp.GraphicalItems()}
    for need_layer in ("F.Courtyard", "F.Fab"):
        if need_layer not in layers:
            errs.append(f"缺 {need_layer}")
    if row["kicad_3d"].startswith("无"):
        if "3D" not in row["notes"]:
            errs.append("没有 3D 模型且 notes 未说明")
    else:
        models = [m.m_Filename for m in fp.Models()]
        if not models:
            errs.append("封装没有 3D 模型引用")
        for m in models:
            if not os.path.exists(resolve_3d(m)):
                errs.append(f"3D 文件不存在: {m}")
    return errs, info


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "parts.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    report = {"csv": str(csv_path), "checked": 0, "errors": {}, "info": {}}
    for row in rows:
        errs, info = check_row(row)
        report["checked"] += 1
        report["info"][row["id"]] = info
        if errs:
            report["errors"][row["id"]] = errs
            print(f"✗ {row['id']:9} {row['kicad_footprint']}: " + "；".join(errs))
    out = ROOT / "reports" / ("check_footprints.json" if len(sys.argv) == 1 else "selftest_check_footprints.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"检查 {report['checked']} 条，出错 {len(report['errors'])} 条")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
