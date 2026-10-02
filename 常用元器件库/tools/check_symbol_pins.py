"""检查每个条目的符号：符号必须存在（官方或 StudentHW），且引脚号集合 = 封装焊盘号集合。

焊盘号取封装文件中所有非空编号（同号算一个）。符号的 extends 会追到父符号。
用法：python tools/check_symbol_pins.py [parts.csv]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SYM_DIR = paths.SYM_OFF
FP_DIR = paths.FP_OFF
LOCAL_SYM = ROOT / "kicad" / "StudentHW.kicad_sym"
LOCAL_FP = ROOT / "kicad" / "StudentHW.pretty"
_cache: dict[Path, str] = {}


def _text(p: Path) -> str:
    if p not in _cache:
        _cache[p] = p.read_text(encoding="utf-8")
    return _cache[p]


def _block(text: str, start: int) -> str:
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def symbol_pins(ref: str) -> set[str] | None:
    if ":" not in ref:
        return None
    lib, name = ref.split(":", 1)
    path = LOCAL_SYM if lib == "StudentHW" else SYM_DIR / f"{lib}.kicad_sym"
    if not path.exists():
        return None
    text = _text(path)
    m = re.search(r'\(symbol "' + re.escape(name) + r'"\s', text)
    if not m:
        return None
    blk = _block(text, m.start())
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    if ext:
        return symbol_pins(f"{lib}:{ext.group(1)}")
    return set(re.findall(r'\(number "([^"]*)"', blk))


def footprint_pads(ref: str) -> set[str] | None:
    if ":" not in ref:
        return None
    lib, name = ref.split(":", 1)
    path = (LOCAL_FP if lib == "StudentHW" else FP_DIR / f"{lib}.pretty") / f"{name}.kicad_mod"
    if not path.exists():
        return None
    return {n for n in re.findall(r'\(pad "([^"]*)"', _text(path)) if n}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "parts.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    report = {"checked": 0, "errors": {}}
    for row in rows:
        errs = []
        if row["kicad_footprint"].startswith("不适用") and row["kicad_symbol"].startswith("不适用"):
            report["checked"] += 1
            continue
        sp = symbol_pins(row["kicad_symbol"])
        fp = footprint_pads(row["kicad_footprint"])
        if sp is None:
            errs.append(f"符号不存在: {row['kicad_symbol']}")
        if fp is None:
            errs.append(f"封装不存在: {row['kicad_footprint']}")
        if sp is not None and fp is not None and sp != fp:
            errs.append(f"符号引脚 {sorted(sp)} ≠ 焊盘 {sorted(fp)}")
        report["checked"] += 1
        if errs:
            report["errors"][row["id"]] = errs
            print(f"✗ {row['id']:9} " + "；".join(errs))
    out = ROOT / "reports" / ("check_symbol_pins.json" if len(sys.argv) == 1 else "selftest_check_symbol_pins.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"检查 {report['checked']} 条，出错 {len(report['errors'])} 条")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
