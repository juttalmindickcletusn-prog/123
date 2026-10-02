"""检查脚本自测：从 parts.csv 取真实条目，故意改错一处，确认对应脚本报错（退出码非 0 且报出预期原因）。

用法：python tools/selftest/run_selftest.py      （结果写 reports/selftest.md）
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
KICAD_PY = paths.KICAD_PY
PY = sys.executable


def rows():
    with (ROOT / "parts.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def row(rid):
    return dict(next(r for r in rows() if r["id"] == rid))


def write_csv(name, rs):
    FIX.mkdir(parents=True, exist_ok=True)
    path = FIX / f"{name}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0].keys()))
        w.writeheader()
        w.writerows(rs)
    return path


def make_pdf(path: Path, text: str = "", image_only: bool = False) -> None:
    """自测用的合成 PDF（不依赖 evidence/ 里的真规格书，精简包也能跑）。"""
    try:
        import fitz
    except ImportError:
        import pymupdf as fitz
    doc = fitz.open()
    page = doc.new_page()
    if image_only:  # 只有一张图、没有文字层，模拟扫描件
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 100), 0)
        pix.clear_with(200)
        page.insert_image(fitz.Rect(50, 50, 450, 250), pixmap=pix)
    else:
        page.insert_text((72, 72), text)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def run(script, csv_path, extra=()):
    exe = KICAD_PY if script == "check_footprints.py" else PY
    r = subprocess.run([exe, str(ROOT / "tools" / script), str(csv_path), *extra], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, r.stdout + r.stderr


def case_footprint(title, rid, changes, expect):
    r = row(rid)
    r.update(changes)
    return title, "check_footprints.py", write_csv(f"fp_{rid}_{len(title)}", [r]), (), expect


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    shutil.rmtree(FIX, ignore_errors=True)
    cases = [
        case_footprint("脚距写错（XH 写成 2.54）", "XH-005", {"pitch_mm": "2.54"}, "脚距"),
        case_footprint("脚数不符", "TERM-002", {"pin_count": "2"}, "焊盘编号数"),
        case_footprint("引脚太粗、孔太小", "DIO-004", {"kicad_footprint": "StudentHW:D_DO-41_SOD81_P10.16mm_Horizontal"}, "孔"),
        case_footprint("环宽不足且没写理由", "HDR-001", {"ring_min_mm": ""}, "环宽"),
        case_footprint("放宽环宽但 notes 没写理由", "XH-002", {"notes": "无"}, "notes 没写理由"),
        case_footprint("有极性但 1 脚不是方焊盘", "CAP-001", {"polarized": "是"}, "方焊盘"),
        case_footprint("封装不存在", "RES-001", {"kicad_footprint": "StudentHW:NoSuchFootprint"}, "封装不存在"),
        case_footprint("没有 3D 也没说明", "FUS-001", {"notes": "无"}, "3D"),
        case_footprint("贴片封装（0805 电阻）", "RES-001", {"kicad_footprint": "Resistor_SMD:R_0805_2012Metric",
                                                     "kicad_3d": "无", "notes": "无 3D"}, "禁止贴片"),
        case_footprint("mount 写贴片", "RES-002", {"mount": "贴片"}, "禁止贴片"),
    ]
    # 符号
    r = row("LED-001"); r["kicad_symbol"] = "Connector_Generic:Conn_01x03"
    cases.append(("符号引脚与焊盘不符", "check_symbol_pins.py", write_csv("sym_mismatch", [r]), (), "≠ 焊盘"))
    r = row("Q-001"); r["kicad_symbol"] = "Transistor_BJT:NoSuchPart"
    cases.append(("符号不存在", "check_symbol_pins.py", write_csv("sym_missing", [r]), (), "符号不存在"))
    # 证据：复制两份相同的 PNG 冒充两个条目
    ev = FIX / "evidence"
    for rid in ("CAP-001", "CAP-002"):
        (ev / rid).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "evidence" / rid / "jlc.json", ev / rid / "jlc.json")
        make_pdf(ev / rid / "datasheet.pdf", row(rid)["part_number"])
        shutil.copy2(ROOT / "evidence" / "CAP-001" / "dim_disc104.png", ev / rid / "dim_same.png")
    rs = []
    for rid in ("CAP-001", "CAP-002"):
        r = row(rid)
        r["evidence"] = f"tools/selftest/fixtures/evidence/{rid}/dim_same.png"
        rs.append(r)
    cases.append(("两个条目用同一张尺寸图", "check_evidence.py", write_csv("ev_dup", rs), (str(ev),), "内容完全相同"))
    r = row("RES-001"); r["part_number"] = "MFR0W4F1002A50"
    cases.append(("型号与 C 编号不符", "check_evidence.py", write_csv("ev_mpn", [r]), (), "型号不符"))
    (ev / "RES-002").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "evidence" / "RES-002" / "jlc.json", ev / "RES-002" / "jlc.json")
    (ev / "RES-002" / "datasheet.pdf").write_text("<html>viewer page</html>", encoding="utf-8")
    r = row("RES-002"); r["evidence"] = "evidence/RES-001/dim_MFR_1-4W.png"
    cases.append(("规格书是网页不是 PDF", "check_evidence.py", write_csv("ev_html", [r]), (str(ev),), "不是 PDF"))
    (ev / "SW-001").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "evidence" / "SW-001" / "jlc.json", ev / "SW-001" / "jlc.json")
    make_pdf(ev / "SW-001" / "datasheet.pdf", image_only=True)
    r = row("SW-001"); r["dim_source"] = "厂家规格书"
    cases.append(("图片型 PDF 未注明人工读图", "check_evidence.py", write_csv("ev_img", [r]), (str(ev),), "人工读图"))
    r = row("DSP-002"); r["datasheet_url"] = ""
    cases.append(("规格书链接为空", "check_evidence.py", write_csv("ev_nourl", [r]), (), "datasheet_url 为空"))
    r = row("BZ-002"); r["evidence"] = "evidence/BZ-002/datasheet.pdf"
    cases.append(("缺尺寸图", "check_evidence.py", write_csv("ev_nodim", [r]), (), "缺尺寸图"))

    lines = ["# 检查脚本自测", "", "每一行把一个真实条目故意改错一处，脚本必须报错。", "",
             "| 结果 | 故意制造的错误 | 脚本 | 期望报出 | 实际输出（节选） |", "|---|---|---|---|---|"]
    fails = 0
    for title, script, path, extra, expect in cases:
        code, out = run(script, path, extra)
        ok = code != 0 and expect in out
        fails += not ok
        msg = next((l.strip() for l in out.splitlines() if l.startswith("✗")), out.strip()[:80]).replace("|", "/")
        lines.append(f"| {'✅ 抓到' if ok else '❌ 漏报'} | {title} | {script} | {expect} | {msg[:110]} |")
        print(("OK  " if ok else "FAIL"), title, "|", msg[:100])
    # 正向对照：真实 parts.csv 必须全部通过
    for script in ("check_footprints.py", "check_symbol_pins.py", "check_evidence.py"):
        exe = KICAD_PY if script == "check_footprints.py" else PY
        r = subprocess.run([exe, str(ROOT / "tools" / script)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        ok = r.returncode == 0
        fails += not ok
        last = (r.stdout.strip().splitlines() or [""])[-1]
        lines.append(f"| {'✅ 通过' if ok else '❌ 不通过'} | 正向对照：真实 parts.csv | {script} | 0 错误 | {last} |")
        print(("OK  " if ok else "FAIL"), "正向对照", script, last)
    lines += ["", f"合计 {len(cases)} 个故意错误 + 3 个正向对照，失败 {fails} 项。"]
    if __import__("os").environ.get("STUDENTHW_PDF_MISSING_OK") == "1":
        lines += ["", "注意：本次在精简包上运行（STUDENTHW_PDF_MISSING_OK=1），证据检查的正向对照把缺 PDF 记为警告而非错误。"]
    (ROOT / "reports" / "selftest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
