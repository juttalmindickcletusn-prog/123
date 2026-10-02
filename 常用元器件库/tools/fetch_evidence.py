"""按 src/parts.yaml 抓取每个条目的立创证据。

对每个条目：
  1. 主型号和替代型号：嘉立创详情接口核实型号/厂家/封装/描述/库存/价格，立创商城人民币价和库存；
  2. 主型号规格书 PDF 存到 evidence/<id>/datasheet.pdf（>30 MB 只记链接）；
  3. 写 evidence/<id>/jlc.txt（人可读的核实记录，含查询日期）；
  4. easyeda2kicad 导出该 C 编号的立创封装和 3D 到 build/easyeda/（用于与 KiCad 封装交叉核对）。

用法：python tools/fetch_evidence.py [ID ...]   不带参数则处理全部条目。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import time
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lcsc_api  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
EASY = ROOT / "build" / "easyeda"
TODAY = dt.date.today().isoformat()
PYLIB = paths.PYLIB


def load_parts() -> list[dict]:
    out = []
    for f in sorted((ROOT / "src").glob("*.yaml")):
        _d = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        if isinstance(_d, list):  # 条目文件是列表；market/series 等是字典，跳过
            out += _d
    return out


def codes_of(p: dict) -> list[str]:
    codes = [p["lcsc"]] if p.get("lcsc", "").startswith("C") else []
    for a in p.get("alternatives") or []:
        if str(a.get("lcsc", "")).startswith("C"):
            codes.append(a["lcsc"])
    return codes


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download(url: str, dest: Path) -> str:
    # www.lcsc.com/datasheet/... 返回的是网页查看器，不是 PDF；换成文件服务器地址。
    data = b""
    if "/datasheet/lcsc_datasheet_" in url:
        rest = url.split("/datasheet/lcsc_datasheet_", 1)[1]
        try:
            data = _fetch("https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/" + rest)
        except Exception:
            data = b""
        if not data.startswith(b"%PDF"):
            import re
            page = _fetch(url).decode("utf-8", "replace")
            m = re.search(r"https://datasheet\.lcsc\.com/datasheet/pdf/[0-9a-f]+\.pdf\?productCode=C\d+", page)
            data = _fetch(m.group(0)) if m else b""
    else:
        data = _fetch(url)
    if not data.startswith(b"%PDF"):
        return "非PDF（未保存）"
    if len(data) > 30 * 1024 * 1024:
        return f"PDF {len(data)//1024} KB >5MB，只记链接"
    dest.write_bytes(data)
    return f"已保存 {len(data)//1024} KB"


def easyeda_export(code: str) -> str:
    EASY.mkdir(parents=True, exist_ok=True)
    out = EASY / "EasyEDA"
    if list((EASY / "EasyEDA.pretty").glob(f"*{code}*")) if (EASY / "EasyEDA.pretty").exists() else []:
        return "已存在"
    env = dict(os.environ, PYTHONPATH=PYLIB, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "easyeda2kicad", "--lcsc_id", code, "--footprint", "--3d",
                        "--output", str(out), "--overwrite", "--use-cache"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(EASY))
    return "ok" if r.returncode == 0 else ("失败: " + (r.stderr or r.stdout)[-200:])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    want = set(sys.argv[1:])
    for p in load_parts():
        if want and p["id"] not in want:
            continue
        d = EV / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        lines = [f"# {p['id']} {p['name']}", f"查询日期: {TODAY}", "来源: 嘉立创元件接口 + 立创商城（立创 EDA 商品接口）", ""]
        record = {"date": TODAY, "parts": {}}
        for i, code in enumerate(codes_of(p)):
            time.sleep(1.5)
            try:
                j = lcsc_api.detail(code, use_cache=True)
            except Exception as exc:  # 网络问题如实记录
                lines.append(f"{code}: 查询失败 {exc}")
                continue
            try:
                s = lcsc_api.szlcsc(code, use_cache=True)
            except Exception:
                s = {"szlcsc": {}}
            role = "主选" if i == 0 else "替代"
            sz = s["szlcsc"]
            rec = {
                "role": role, "code": code, "mpn": j.get("componentModelEn"), "brand": j.get("componentBrandEn"),
                "package": j.get("componentSpecificationEn"), "describe": j.get("describe"),
                "jlc_stock": j.get("stockCount"), "library": j.get("componentLibraryType"),
                "usd_prices": [(x["startNumber"], x["productPrice"]) for x in (j.get("prices") or [])][:3],
                "cny_price": sz.get("price"), "cny_step": sz.get("min"), "szlcsc_stock": sz.get("stock"),
                "datasheet": j.get("dataManualUrl") or s.get("pdf"),
            }
            record["parts"][code] = rec
            lines += [f"[{role}] {code}", f"  型号: {rec['mpn']}", f"  厂家: {rec['brand']}", f"  封装: {rec['package']}",
                      f"  描述: {rec['describe']}", f"  立创商城: ¥{rec['cny_price']} 起订{rec['cny_step']}  库存 {rec['szlcsc_stock']}",
                      f"  嘉立创库存: {rec['jlc_stock']}  贴片库: {rec['library']}", f"  规格书: {rec['datasheet']}", ""]
            if i == 0 and rec["datasheet"] and not (d / "datasheet.pdf").exists():
                try:
                    lines.append("  规格书下载: " + download(rec["datasheet"], d / "datasheet.pdf"))
                except Exception as exc:
                    lines.append(f"  规格书下载失败: {exc}")
        (d / "jlc.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (d / "jlc.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        main_rec = record["parts"].get(p.get("lcsc", ""), {})
        print(f"{p['id']:10} {p.get('lcsc',''):10} {str(main_rec.get('mpn'))[:30]:30} ¥{main_rec.get('cny_price')} 库存{main_rec.get('szlcsc_stock')} "
              f"{'PDF' if (d/'datasheet.pdf').exists() else 'noPDF'}", flush=True)


if __name__ == "__main__":
    main()
