"""一键重建与检查（不联网）。改了 src/*.yaml 或封装后运行这一个脚本即可。

顺序：生成封装 → 生成 parts.csv → 原子符号库 → 四项检查 → 检查脚本自测 → 测试板 + DRC + 渲染 → preview.html → 常用元器件清单.md → reports/检查汇总.md
联网刷新价格库存另跑：python tools/fetch_evidence.py
用法：python tools/run_all.py
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PY, KPY, CLI = sys.executable, paths.KICAD_PY, paths.KICAD_CLI
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "STUDENTHW_DIR": str(ROOT)}


def step(name, cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    last = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-1:] or [""]
    print(f"{'✅' if r.returncode == 0 else '❌'} {name}：{last[0]}")
    return name, r.returncode == 0, last[0]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    tb = ROOT / "build" / "testboard" / "testboard.kicad_pcb"
    out = ROOT / "reports" / "testboard"
    out.mkdir(parents=True, exist_ok=True)
    res = [
        step("生成自建封装", [PY, "tools/gen_footprints.py"]),
        step("生成模块封装和符号", [PY, "tools/gen_modules.py"]),
        step("生成 parts.csv",[PY, "tools/build_csv.py"]),
        step("生成原子符号库", [PY, "tools/build_atomic.py"]),
        step("封装检查", [KPY, "tools/check_footprints.py"]),
        step("符号引脚检查", [PY, "tools/check_symbol_pins.py"]),
        step("证据检查", [PY, "tools/check_evidence.py"]),
        step("原子符号检查", [PY, "tools/check_atomic.py"]),
        step("兼容性速查", [PY, "tools/build_compat.py"]),
        step("价格与热度表", [PY, "tools/build_market.py"]),
        step("选型速查", [PY, "tools/build_selection.py"]),
        step("价格新鲜度（不联网）", [PY, "tools/refresh_prices.py", "--check"]),
        *[step(f"项目检查 {p.stem}", [PY, "tools/check_project.py", str(p)]) for p in sorted((ROOT / "projects").glob("*.yaml"))],
        *[step(f"项目成本 {p.stem}", [PY, "tools/project_cost.py", str(p)]) for p in sorted((ROOT / "projects").glob("*.yaml"))],
        step("检查脚本自测", [PY, "tools/selftest/run_selftest.py"]),
        step("测试板", [KPY, "tools/build_testboard.py"]),
        step("测试板 DRC", [CLI, "pcb", "drc", "--format", "json", "--exit-code-violations", "-o", str(out / "drc.json"), str(tb)]),
        step("渲染顶视图", [CLI, "pcb", "render", "--side", "top", "--width", "2400", "--height", "1700", "--quality", "high",
                       "-o", str(out / "render_top.png"), str(tb)]),
        step("渲染斜视图", [CLI, "pcb", "render", "--side", "top", "--rotate", "-45,0,20", "--perspective", "--width", "2400",
                       "--height", "1700", "--quality", "high", "-o", str(out / "render_iso.png"), str(tb)]),
        step("预览页", [PY, "tools/build_preview.py"]),
        step("清单文档", [PY, "tools/build_list.py"]),
    ]
    shutil.copy2(tb, out / "testboard.kicad_pcb")
    drc = json.loads((out / "drc.json").read_text(encoding="utf-8"))
    lines = [f"# 检查汇总（{datetime.date.today()}）", "", "| 步骤 | 结果 | 输出 |", "|---|---|---|"]
    lines += [f"| {n} | {'通过' if ok else '**失败**'} | {msg.replace('|', '/')} |" for n, ok, msg in res]
    lines += ["", f"测试板 DRC：违规 {len(drc.get('violations', []))} 条，未连接 {len(drc.get('unconnected_items', []))} 条。",
              "测试板文件、渲染图在 reports/testboard/。"]
    ev = json.loads((ROOT / "reports" / "check_evidence.json").read_text(encoding="utf-8"))
    if ev.get("pdf_missing_warn") or ev.get("jlc_missing_warn"):
        lines += ["", "**离线模式**（STUDENTHW_OFFLINE=1）：以下检查没做，只记为警告，不算通过。"
                  "联网后先跑 `python tools/fetch_evidence.py 编号…` 补齐，再不带该变量重跑。",
                  f"- 缺 datasheet.pdf（PDF 存在性和 PDF 文本型号未查）{len(ev.get('pdf_missing_warn', []))} 条："
                  + "、".join(ev.get("pdf_missing_warn", [])),
                  f"- 有 C 编号但没有 jlc.json（C 编号未用接口核实）{len(ev.get('jlc_missing_warn', []))} 条："
                  + ("、".join(ev.get("jlc_missing_warn", [])) or "无")]
    (ROOT / "reports" / "检查汇总.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    bad = [n for n, ok, _ in res if not ok]
    print("全部通过" if not bad else f"失败：{bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
