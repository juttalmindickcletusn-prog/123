"""生成 reports/价格与热度表.md 和 价格与热度.csv，并校验市场数据。
数据只存一份：立创价来自 src/price_history.csv（没有时退回 evidence/<id>/jlc.json），热度/替代/店铺/淘宝来自 src/market.yaml，
系列件（阻值）各值的 C 编号来自 src/series.yaml。本脚本不添加任何数字。

校验（有错退出 1）：
  - parts.csv 每个条目在 market.yaml 里都有：sales_level（大众/常用/冷门/未核）、sales_evidence、better_alt、recommend_shop；
  - sales_level 不是"未核"时，sales_evidence 不能是空或"未核"开头；
  - better_alt 里引用的库内编号（如 SEN-004）必须在 parts.csv 里；
  - 淘宝价如已填（字典），至少 3 家店，每家有 shop/url/price/spec，median 与各家价格的中位数一致，min 不大于 median；
  - market.yaml 里没有 parts.csv 以外的编号。
用法：python tools/build_market.py              # 校验并生成
      python tools/build_market.py 某.yaml       # 只用该文件代替 src/market.yaml 做校验，不写输出（自测用）
"""
from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import market_lib as ml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "reports" / "价格与热度表.md"
OUT_CSV = ROOT / "价格与热度.csv"
LEVELS = ("大众", "常用", "冷门", "未核")
REF = re.compile(r"\b([A-Z]{1,4}-\d{3})\b")
QTYS = (1, 10, 100)


def at_qty(tiers: list[tuple[int, float]], complete: bool, q: int) -> str:
    """数量 q 时的立创单价。只核到起订档时，超过起订量的价格只能写上限。"""
    if not tiers:
        return "未核"
    lo_q, lo_p = tiers[0]
    if q < lo_q:
        return f"需买 {lo_q}，¥{lo_p:g}"
    q_, p_ = ml.pick_tier(tiers, q)
    if not complete and q > lo_q:
        return f"≤¥{p_:g}（更高档未核）"
    return f"¥{p_:g}"


def tb_check(pid: str, m: dict, errs: list[str]) -> None:
    for key in ("price_taobao_ref", "price_taobao_min"):
        v = m.get(key)
        if isinstance(v, (int, float)):
            errs.append(f"{pid} {key} 只写了一个数字，必须写店铺明细（shops）")
    ref = m.get("price_taobao_ref")
    if not isinstance(ref, dict):
        return
    shops = ref.get("shops") or []
    if len(shops) < 3:
        errs.append(f"{pid} 淘宝参考价只有 {len(shops)} 家，至少 3 家")
    for s in shops:
        miss = [k for k in ("shop", "url", "price", "spec") if not s.get(k)]
        if miss:
            errs.append(f"{pid} 淘宝店铺记录缺 {'、'.join(miss)}：{s}")
    prices = [float(s["price"]) for s in shops if isinstance(s.get("price"), (int, float))]
    if prices and abs(statistics.median(prices) - float(ref.get("median", -1))) > 0.005:
        errs.append(f"{pid} 淘宝参考价 median={ref.get('median')} 与各家价格中位数 {statistics.median(prices):g} 不符")
    mn = m.get("price_taobao_min")
    if isinstance(mn, dict) and isinstance(mn.get("price"), (int, float)) and prices and mn["price"] > statistics.median(prices):
        errs.append(f"{pid} 淘宝最低可靠价 {mn['price']} 大于参考价中位数")


def tb_text(v) -> str:
    if isinstance(v, dict):
        if "median" in v:
            return f"¥{v['median']:g}（{len(v.get('shops', []))} 家中位数）"
        if "price" in v:
            return f"¥{v['price']:g}（{v.get('shop', '')}）"
    return str(v)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = ml.parts_rows()
    ids = {r["id"] for r in rows}
    prefixes = {i.split("-")[0] for i in ids}       # 只核对库内编号格式（DC-005 这类型号名不算）
    alt_mk = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    mk = ml.yaml.safe_load(alt_mk.read_text(encoding="utf-8")) if alt_mk else ml.market()
    hist, ser = ml.history(), ml.series()
    errs: list[str] = []
    for pid in mk:
        if pid not in ids:
            errs.append(f"market.yaml 里的 {pid} 不在 parts.csv")
    out = []
    for r in rows:
        pid = r["id"]
        raw = mk.get(pid)
        if not raw:
            errs.append(f"{pid} 在 market.yaml 里没有记录")
            raw = {}
        for k in ("sales_level", "sales_evidence", "better_alt", "recommend_shop"):
            if not raw.get(k):
                errs.append(f"{pid} 缺 {k}")
        if raw.get("sales_level") and raw["sales_level"] not in LEVELS:
            errs.append(f"{pid} sales_level={raw['sales_level']} 不是 {'/'.join(LEVELS)}")
        if raw.get("sales_level") not in (None, "未核") and str(raw.get("sales_evidence", "")).startswith("未核"):
            errs.append(f"{pid} 定为{raw['sales_level']}，但依据写的是未核")
        for ref in REF.findall(str(raw.get("better_alt", ""))):
            if ref.split("-")[0] in prefixes and ref not in ids:
                errs.append(f"{pid} better_alt 引用的 {ref} 不在 parts.csv")
        tb_check(pid, raw, errs)
        m = ml.entry(r, mk, hist)
        p = m["price_lcsc"]
        tiers, complete = (p["tiers"], p["complete"]) if p else ([], False)
        age = ml.days_old(p["date"]) if p else None
        out.append({
            "id": pid, "name": r["name"], "lcsc": r["lcsc_id"],
            "price_lcsc": ml.fmt_tiers(tiers) if tiers else "未核",
            **{f"lcsc_{q}": at_qty(tiers, complete, q) for q in QTYS},
            "lcsc_note": ("已核到多档" if complete else "只核到起订档（立创接口在云端被拦，1/10/100 档待 refresh_prices.py 联网刷新）") if p else
                         ("无 C 编号（模块/离板件，立创未售或未建档）" if not r["lcsc_id"].startswith("C") else "该 C 编号无价格记录"),
            "price_taobao_ref": tb_text(m["price_taobao_ref"]), "price_taobao_min": tb_text(m["price_taobao_min"]),
            "taobao_keyword": r.get("taobao_keyword", ""),
            "price_unit_basis": m["price_unit_basis"], "price_checked": m["price_checked"] or "未核",
            "price_age_days": "" if age is None else age,
            "sales_level": m["sales_level"], "sales_evidence": m["sales_evidence"],
            "better_alt": m["better_alt"], "recommend_shop": m["recommend_shop"],
        })
    # 系列件：每个值单独一行（价格来自 series.yaml 的 C 编号对应的历史记录）
    ser_rows = []
    for sid, sv in ser.items():
        vals = sv.get("values") if isinstance(sv, dict) else None
        for v in vals or []:
            pp = ml.lcsc_price(sid, v.get("lcsc", ""), hist)
            ser_rows.append((sid, v.get("value"), v.get("lcsc", ""), ml.fmt_tiers(pp["tiers"]) + f"（{pp['date']}）" if pp else "未核"))

    if alt_mk:
        for e in errs:
            print("✗", e)
        print(f"市场数据校验（{alt_mk.name}）：错误 {len(errs)}")
        return 1 if errs else 0
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    lv = Counter(o["sales_level"] for o in out)
    n_lcsc = sum(o["price_lcsc"] != "未核" for o in out)
    n_full = sum(o["lcsc_note"] == "已核到多档" for o in out)
    n_tb = sum(not o["price_taobao_ref"].startswith(ml.NOT_CHECKED_TB) for o in out)
    old = [o["id"] for o in out if isinstance(o["price_age_days"], int) and o["price_age_days"] > 30]
    L = ["# 价格与热度表", "",
         "由 `tools/build_market.py` 生成，不要手改。改数据改 `src/market.yaml`（热度、替代、店铺、淘宝）和 `src/price_history.csv`（立创价，`tools/refresh_prices.py` 追加）。", "",
         "## 汇总", "",
         f"- 条目 {len(out)} 条；有立创价 {n_lcsc} 条（其中核到多档 {n_full} 条，其余只核到起订档）；淘宝价核到 {n_tb} 条。",
         f"- 热度：{'，'.join(f'{k} {lv.get(k, 0)}' for k in LEVELS)}。热度规则见 `src/market.yaml` 文件头。",
         f"- 核实日期超过 30 天的立创价：{len(old)} 条{('：' + '、'.join(old)) if old else ''}。",
         "- 口径：立创价为立创商城单只标价，不含运费，按该档起订量；“需买 N”表示该数量不够起订量，要按起订量买。"
         "“≤¥x（更高档未核）”表示只知道起订档价格，更大量的阶梯价只会更低，但具体值没核到。",
         "- 淘宝：云端不能登录，价格和销量全部“淘宝未核（需登录）”。下表给了搜索关键词和候选店铺，登录后按 `src/market.yaml` 头部格式填 3 家以上。", ""]
    if errs:
        L += ["## 校验错误", ""] + [f"- {e}" for e in errs] + [""]
    L += ["## 明细", "",
          "| 编号 | 名称 | 立创 C 编号 | 1 个 | 10 个 | 100 个 | 立创核实日期 | 淘宝参考价 | 热度 | 热度依据 | 更好的替代 | 推荐店铺 | 淘宝搜索词 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    esc = lambda s: str(s).replace("|", "/")
    for o in out:
        L.append("| " + " | ".join(esc(x) for x in (o["id"], o["name"], o["lcsc"], o["lcsc_1"], o["lcsc_10"], o["lcsc_100"],
                                                     o["price_checked"], o["price_taobao_ref"], o["sales_level"], o["sales_evidence"],
                                                     o["better_alt"], o["recommend_shop"], o["taobao_keyword"])) + " |")
    if ser_rows:
        L += ["", "## 系列件各值（src/series.yaml）", "", "| 条目 | 值 | 立创 C 编号 | 已核价格档（起订量:单价） |", "|---|---|---|---|"]
        L += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in ser_rows]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    for e in errs:
        print("✗", e)
    print(f"价格与热度：{len(out)} 条，立创价 {n_lcsc}（多档 {n_full}），淘宝 {n_tb}，"
          f"{'，'.join(f'{k} {lv.get(k, 0)}' for k in LEVELS)}，错误 {len(errs)} → {OUT_MD.relative_to(ROOT)}、{OUT_CSV.name}")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
