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
    exe = KICAD_PY if script in ("check_footprints.py",) else PY
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

    # 原子符号库：复制真库，各注入一种错误
    sys.path.insert(0, str(ROOT / "tools"))
    from sexpr import children as _ch, dump as _dump, parse as _parse, Q as _Q
    def atomic_case(title, mutate, expect):
        lib = _parse((ROOT / "kicad" / "StudentHW_Parts.kicad_sym").read_text(encoding="utf-8"))
        mutate({s_[1]: s_ for s_ in _ch(lib, "symbol")})
        path = FIX / f"atomic_{len(cases)}.kicad_sym"
        path.write_text(_dump(lib) + "\n", encoding="utf-8")
        cases.append((title, "check_atomic.py", path, ("--no-cli",), expect))
    def set_prop(sym, key, val):
        for p_ in _ch(sym, "property"):
            if p_[1] == key:
                p_[2] = _Q(val)
    def drop_pin(sym):
        for unit in _ch(sym, "symbol"):
            pins = [x for x in unit if isinstance(x, list) and x and x[0] == "pin"]
            if pins:
                unit.remove(pins[-1])
                return
    atomic_case("原子符号封装属性写错", lambda d: set_prop(d["Q-001_S8050"], "Footprint", "Package_TO_SOT_THT:TO-92_Inline"), "Footprint 属性")
    atomic_case("原子符号少一个引脚", lambda d: drop_pin(d["REG-002_LD1117V33"]), "引脚与基础符号")
    atomic_case("原子符号 C 编号写错", lambda d: set_prop(d["RES-001_10k"], "LCSC", "C57435"), "LCSC 属性")

    # 项目检查：故意出错的样例项目（tools/selftest/projects/bad_*.yaml），每种错误都要报出来
    for fn, title, expect in (("bad_i2c.yaml", "I2C 地址冲突（MPU6050 与 DS3231 同为 0x68）", "冲突"),
                              ("bad_level.yaml", "5V 输出接不耐 5V 的脚（HC-SR04 Echo → ESP32）", "不耐 5V"),
                              ("bad_pin.yaml", "用 Flash 脚", "别用"),
                              ("bad_pin.yaml", "只能输入的脚接输出信号", "只能输入"),
                              ("bad_pin.yaml", "同一个脚分两次", "同时分给了"),
                              ("bad_current.yaml", "电流超 70%（USB 带 MG996R）", "超过 70%"),
                              ("bad_pullup.yaml", "I2C 上拉到 5V 接 ESP32", "上拉到 5V")):
        cases.append((title, "check_project.py", HERE / "projects" / fn, (), expect))

    # 市场数据：拿真实 market.yaml 改坏一处
    import yaml
    mk0 = yaml.safe_load((ROOT / "src" / "market.yaml").read_text(encoding="utf-8"))
    def bad_market(tag, pid, **kw):
        mk = {k: dict(v) for k, v in mk0.items()}
        mk[pid].update(kw)
        p_ = FIX / f"market_{tag}.yaml"
        p_.write_text(yaml.safe_dump(mk, allow_unicode=True), encoding="utf-8")
        return p_
    shops2 = [{"shop": "店A", "url": "https://example.invalid/a", "price": 1.0, "spec": "1 个"},
              {"shop": "店B", "url": "https://example.invalid/b", "price": 2.0, "spec": "1 个"}]
    shops3 = shops2 + [{"shop": "店C", "url": "https://example.invalid/c", "price": 3.0, "spec": "1 个"}]
    cases.append(("热度定为大众但依据写未核", "build_market.py", bad_market("lvl", "SEN-030", sales_level="大众"), (), "依据写的是未核"))
    cases.append(("淘宝参考价只取 2 家", "build_market.py", bad_market("tb2", "SEN-014", price_taobao_ref={"shops": shops2, "median": 1.5}), (), "至少 3 家"))
    cases.append(("淘宝中位数算错", "build_market.py", bad_market("tbmed", "SEN-014", price_taobao_ref={"shops": shops3, "median": 2.5}), (), "中位数"))
    cases.append(("淘宝价只写一个数字", "build_market.py", bad_market("tbnum", "SEN-014", price_taobao_ref=9.9), (), "店铺明细"))
    cases.append(("替代料引用不存在的编号", "build_market.py", bad_market("alt", "SEN-001", better_alt="SEN-999 更好"), (), "不在 parts.csv"))
    cases.append(("热度等级写错字", "build_market.py", bad_market("lvlname", "RES-001", sales_level="热门"), (), "不是 大众"))

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
    # 正向对照：真实 parts.csv、样例项目必须全部通过
    positives = [(s_, []) for s_ in ("check_footprints.py", "check_symbol_pins.py", "check_evidence.py", "check_atomic.py")]
    positives += [("check_project.py", [str(p_)]) for p_ in sorted((ROOT / "projects").glob("*.yaml"))]
    for script, args in positives:
        exe = KICAD_PY if script in ("check_footprints.py",) else PY
        r = subprocess.run([exe, str(ROOT / "tools" / script), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        ok = r.returncode == 0
        fails += not ok
        last = (r.stdout.strip().splitlines() or [""])[-1]
        what = "样例项目 " + Path(args[0]).stem if args else "真实 parts.csv"
        lines.append(f"| {'✅ 通过' if ok else '❌ 不通过'} | 正向对照：{what} | {script} | 0 错误 | {last} |")
        print(("OK  " if ok else "FAIL"), "正向对照", what, script, last)
    lines += ["", f"合计 {len(cases)} 个故意错误 + {len(positives)} 个正向对照，失败 {fails} 项。"]
    _env = __import__("os").environ
    if _env.get("STUDENTHW_OFFLINE") == "1" or _env.get("STUDENTHW_PDF_MISSING_OK") == "1":
        lines += ["", "注意：本次在离线模式运行（STUDENTHW_OFFLINE=1），证据检查的正向对照把缺 PDF、缺 jlc.json 记为警告而非错误。"]
    (ROOT / "reports" / "selftest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
