"""证据检查：
  1. evidence/<id>/jlc.json 存在，主 C 编号与 CSV 一致，嘉立创返回的型号与 part_number 一致；
  2. 规格书：datasheet.pdf 存在且是真 PDF（或 notes 写明"规格书缺"原因）；
  3. 尺寸图：evidence/<id>/ 下至少一张 dim*.png（level A 可用 V1.1 实物记录代替：notes 含"V1.1"）；
  4. 所有 PNG 的 SHA1 不得重复（同一张图冒充多个条目）、不得小于 5 KB（报错页/空白页）；
  5. PDF 文本中能搜到型号关键字（图片型 PDF 需在 dim_source 写"人工读图"）；
  6. datasheet_url 不能为空（模块也必须给出厂家或商品资料链接）。

离线模式（云端网络拦了立创、厂家站点，或拿到的是不带 PDF 的精简包）：设环境变量 STUDENTHW_OFFLINE=1
（旧名 STUDENTHW_PDF_MISSING_OK=1 同义）时，下面两项降为警告，单独计数、写进报告，其余检查照常：
  - 缺 datasheet.pdf（PDF 文本型号检查因此也没做）；
  - 有 C 编号但缺 jlc.json（C 编号还没用接口核实）。
正式验收必须在联网、完整包上先跑 fetch_evidence.py 补齐，再不带该变量运行。
"不上板"的配件（封装写"不适用"、notes 写"不上板"）不要求尺寸图。

用法：python tools/check_evidence.py [parts.csv]
"""
from __future__ import annotations

import csv
import hashlib
import os
import json
import re
import sys
from pathlib import Path

try:
    import fitz
except ImportError:  # Debian/Ubuntu 的 python3-pymupdf 只提供 pymupdf 名字
    import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]


def norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "parts.csv"
    ev_root = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "evidence"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    report = {"checked": 0, "errors": {}, "pdf_missing_warn": [], "jlc_missing_warn": []}
    pdf_ok = os.environ.get("STUDENTHW_OFFLINE") == "1" or os.environ.get("STUDENTHW_PDF_MISSING_OK") == "1"
    hashes: dict[str, str] = {}
    for row in rows:
        errs = []
        d = ev_root / row["id"]
        code = row["lcsc_id"]
        if code.startswith("C"):
            j = d / "jlc.json"
            if not j.exists():
                if pdf_ok:
                    report["jlc_missing_warn"].append(row["id"])
                else:
                    errs.append("缺 jlc.json")
            else:
                rec = json.loads(j.read_text(encoding="utf-8")).get("parts", {}).get(code)
                if not rec:
                    errs.append(f"jlc.json 中没有主型号 {code}")
                elif norm(rec.get("mpn")) != norm(row["part_number"]):
                    errs.append(f"型号不符：嘉立创 {rec.get('mpn')} ≠ CSV {row['part_number']}")
        pdf = d / "datasheet.pdf"
        if pdf.exists():
            data = pdf.read_bytes()
            if not data.startswith(b"%PDF"):
                errs.append("datasheet.pdf 不是 PDF")
            else:
                try:
                    text = norm("".join(p.get_text() for p in fitz.open(pdf)))
                except Exception:
                    text = ""
                key = norm(row.get("pdf_keyword") or row["part_number"])
                if key and key not in text and "人工读图" not in row["dim_source"]:
                    errs.append(f"PDF 文本里找不到 {row.get('pdf_keyword') or row['part_number']}，且 dim_source 未注明人工读图")
        elif "规格书缺" not in row["notes"] and row["level"] != "A":
            if pdf_ok:
                report["pdf_missing_warn"].append(row["id"])
            else:
                errs.append("缺 datasheet.pdf，notes 也未说明")
        if not (row.get("datasheet_url") or "").strip():
            errs.append("datasheet_url 为空")
        listed = [x for x in row["evidence"].split(";") if x]
        pngs = [ROOT / x for x in listed if x.endswith(".png")]
        for x in listed:
            if not (ROOT / x).exists():
                if pdf_ok and x.endswith(".pdf"):
                    report["pdf_missing_warn"].append(row["id"])
                else:
                    errs.append(f"证据文件不存在: {x}")
        off_board = row["kicad_footprint"].startswith("不适用") and "不上板" in row["notes"]
        if not [q for q in pngs if q.name.startswith("dim")] and not (row["level"] == "A" and "V1.1" in row["notes"]) and not off_board:
            errs.append("缺尺寸图 dim*.png")
        for q in pngs:
            if not q.exists():
                continue
            if q.stat().st_size < 5000:
                errs.append(f"{q.name} 小于 5 KB，疑似空白或报错页")
            h = hashlib.sha1(q.read_bytes()).hexdigest()
            if h in hashes and hashes[h] != str(q):
                errs.append(f"{q.name} 与 {hashes[h]} 内容完全相同")
            hashes.setdefault(h, str(q))
        report["checked"] += 1
        if errs:
            report["errors"][row["id"]] = errs
            print(f"✗ {row['id']:9} " + "；".join(errs))
    report["pdf_missing_warn"] = sorted(set(report["pdf_missing_warn"]))
    report["jlc_missing_warn"] = sorted(set(report["jlc_missing_warn"]))
    out = ROOT / "reports" / ("check_evidence.json" if len(sys.argv) == 1 else "selftest_check_evidence.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    warn = f"；离线警告：缺 PDF {len(report['pdf_missing_warn'])} 条" if report["pdf_missing_warn"] else ""
    if report["jlc_missing_warn"]:
        warn += f"，C 编号未接口核实 {len(report['jlc_missing_warn'])} 条"
    print(f"检查 {report['checked']} 条，出错 {len(report['errors'])} 条{warn}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
