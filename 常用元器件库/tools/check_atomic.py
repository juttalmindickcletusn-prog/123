"""检查原子符号库 kicad/StudentHW_Parts.kicad_sym：
  1. 条目和原子符号一一对应（系列件按 src/series.yaml 每个值一个），不多不少；
  2. Footprint、LCSC、MPN 三个属性与 parts.csv（系列件与 series.yaml）完全一致；StudentHW_ID 指回条目；
  3. 原子符号的引脚号、引脚名与基础符号完全一致；引脚号集合 = 封装焊盘号集合；
  4. 除 Reference、Value 外的属性都隐藏；
  5. kicad-cli sym export svg 能导出整个库（证明 KiCad 能读）。
用法：python tools/check_atomic.py [库文件] [--no-cli]
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_atomic  # noqa: E402
import paths  # noqa: E402
from check_symbol_pins import footprint_pads  # noqa: E402
from sexpr import child, children, head, parse  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def props(sym) -> dict:
    return {p[1]: p for p in children(sym, "property")}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lib_path = Path(args[0]) if args else build_atomic.OUT
    no_cli = "--no-cli" in sys.argv
    errors: dict[str, list[str]] = {}

    def err(k, m):
        errors.setdefault(k, []).append(m)

    lib = parse(lib_path.read_text(encoding="utf-8"))
    have = {s[1]: s for s in children(lib, "symbol")}
    want = {name: (row, lcsc, mpn) for row, name, _v, lcsc, mpn, *_ in build_atomic.items()}
    for n in sorted(set(want) - set(have)):
        err(n, "缺原子符号")
    for n in sorted(set(have) - set(want)):
        err(n, "多出的原子符号（parts.csv / series.yaml 里没有对应条目）")
    for name in sorted(set(want) & set(have)):
        row, lcsc, mpn = want[name]
        sym = have[name]
        pr = props(sym)
        for key, exp in (("Footprint", row["kicad_footprint"]), ("LCSC", lcsc), ("MPN", mpn), ("StudentHW_ID", row["id"])):
            got = pr[key][2] if key in pr else None
            if got != exp:
                err(name, f"{key} 属性 {got!r} ≠ 应为 {exp!r}")
        for key, p in pr.items():
            hidden = child(p, "hide") is not None
            if key in ("Reference", "Value") and hidden:
                err(name, f"{key} 不应隐藏")
            if key not in ("Reference", "Value") and not hidden:
                err(name, f"{key} 应隐藏")
        if child(sym, "extends") is not None:
            err(name, "原子符号不能用 extends（跨库不能继承）")
        base = build_atomic.base_symbol(row["kicad_symbol"])
        a, b = sorted(build_atomic.pins_of(sym)), sorted(build_atomic.pins_of(base))
        if a != b:
            miss = sorted(set(b) - set(a))
            extra = sorted(set(a) - set(b))
            err(name, f"引脚与基础符号 {row['kicad_symbol']} 不一致：缺 {miss[:5]} 多 {extra[:5]}")
        pads = footprint_pads(row["kicad_footprint"])
        nums = {n for n, _ in a}
        if pads is None:
            err(name, f"封装不存在 {row['kicad_footprint']}")
        elif nums != pads:
            err(name, f"引脚号 {sorted(nums)} ≠ 封装焊盘号 {sorted(pads)}")
        for unit in children(sym, "symbol"):
            if not unit[1].startswith(name + "_"):
                err(name, f"子单元名 {unit[1]} 没改成 {name}_单元_样式")
    cli = "未运行（--no-cli）"
    if not no_cli:
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([paths.KICAD_CLI, "sym", "export", "svg", "--black-and-white", "-o", d, str(lib_path)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            n_svg = len(list(Path(d).glob("*.svg")))
        cli = f"kicad-cli 导出 {n_svg} 张 SVG"
        if r.returncode != 0 or n_svg < len(have):
            err("_库", f"kicad-cli 读不了或导出不全：{(r.stdout + r.stderr).strip()[-200:]}（导出 {n_svg}/{len(have)}）")
    for k, v in errors.items():
        print(f"✗ {k}: " + "；".join(v))
    out = ROOT / "reports" / ("check_atomic.json" if not args else "selftest_check_atomic.json")
    out.write_text(json.dumps({"symbols": len(have), "expected": len(want), "cli": cli, "errors": errors},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"原子符号 {len(have)} 个（应有 {len(want)}），{cli}，出错 {len(errors)} 处")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
