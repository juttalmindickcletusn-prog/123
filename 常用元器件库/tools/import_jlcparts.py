"""嘉立创接口不通时的替补：从 jlcparts 公开镜像（GitHub yaqwsx/jlcparts 的 gh-pages 分支 data/cache.zip 里的
cache.sqlite3）读出 C 编号的型号、厂家、库存和嘉立创海外阶梯价（美元），写成 evidence/<id>/jlc.json。

- 只用于"C 编号 ↔ 型号"核实和嘉立创库存/美元价参考；立创商城人民币价不在镜像里，不会写。
- 镜像只收了一部分料号（主要是 C6000000 以后的新编号），查不到的如实报"镜像里没有"。
- 已有 jlc.json（fetch_evidence.py 联网抓的）的条目不覆盖。
- 记录里写明来源 "jlcparts 镜像"、镜像抓取该料的时间。联网后应再跑 fetch_evidence.py 用正式接口复核。

取镜像：git clone --depth 1 --branch gh-pages https://github.com/yaqwsx/jlcparts ；7z x data/cache.zip
用法：python tools/import_jlcparts.py 路径/cache.sqlite3 编号 [编号 ...]
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_evidence  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    db, ids = sys.argv[1], set(sys.argv[2:])
    con = sqlite3.connect(db)
    cols = [r[1] for r in con.execute("pragma table_info(jlc_components)")]
    for p in fetch_evidence.load_parts():
        if p["id"] not in ids:
            continue
        d = ROOT / "evidence" / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        if (d / "jlc.json").exists() and "jlcparts" not in (d / "jlc.json").read_text(encoding="utf-8"):
            print(f"{p['id']}: 已有接口核实的 jlc.json，不覆盖")
            continue
        record = {"date": "", "source": "jlcparts 镜像（github.com/yaqwsx/jlcparts gh-pages data/cache.zip）", "parts": {}}
        lines = [f"# {p['id']} {p['name']}", "来源: jlcparts 公开镜像（嘉立创数据），不是立创商城接口；人民币价未核", ""]
        for i, code in enumerate(fetch_evidence.codes_of(p)):
            r = con.execute("select * from jlc_components where lcsc=?", (int(code[1:]),)).fetchone()
            if not r:
                lines.append(f"{code}: 镜像里没有")
                continue
            x = dict(zip(cols, r))
            fetched = dt.datetime.fromtimestamp(x["fetched_at"], dt.timezone.utc).date().isoformat()
            tiers = []
            for t in x["price"].split(","):
                q, v = t.split(":")
                tiers.append([int(q.split("-")[0]), float(v)])
            rec = {"role": "主选" if i == 0 else "替代", "code": code, "mpn": x["mfr"], "brand": x["manufacturer"],
                   "package": x["package"], "describe": x["description"], "jlc_stock": x["stock"],
                   "library": x["library_type"], "usd_prices": tiers[:3], "cny_price": None, "cny_step": None,
                   "szlcsc_stock": None, "datasheet": x["datasheet"], "mirror_fetched": fetched}
            record["parts"][code] = rec
            record["date"] = record["date"] or fetched
            lines += [f"[{rec['role']}] {code}（镜像抓取 {fetched}）", f"  型号: {rec['mpn']}", f"  厂家: {rec['brand'] or '（镜像未给）'}",
                      f"  描述: {rec['describe']}", f"  嘉立创库存: {rec['jlc_stock']}  美元阶梯: {tiers[:3]}", ""]
        if not record["parts"]:
            print(f"{p['id']}: 镜像里查不到 {fetch_evidence.codes_of(p)}，未写")
            continue
        (d / "jlc.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        (d / "jlc.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{p['id']}: 写出 jlc.json（{', '.join(record['parts'])}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
