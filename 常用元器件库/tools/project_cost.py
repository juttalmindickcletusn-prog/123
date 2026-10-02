"""项目成本和采购清单：python tools/project_cost.py projects/<项目名>.yaml

输出到 projects/<项目名>/：
  成本.md        每行：编号、名称、用量、实际采购量、所用单价（立创哪一档 / 淘宝参考价）、来源、核实日期、小计；
                 立创、淘宝分开小计，再加项目里手填的 extra_cost，给总计。缺价的行单独列出，总计旁写"总价不完整"。
  立创配单.csv   有 C 编号的件，列：商品编号、用量、预设备损量、位号（列名说明见下）。
  淘宝清单.md    没有 C 编号的件：搜索关键词、候选店铺、参考价、数量、规格选项提醒（取自 parts.csv 的 pitfalls）。

采购量规则见 src/buy_rules.yaml。价格只读市场数据（market_lib），本脚本不写任何价格。
立创配单表列名：立创商城 BOM 配单"下载模板"后只需填"商品编号"/"自定义编号"和"用量"，"预设备损量""位号"选填
（2026-10-02 由搜索引擎摘要得知；云端打不开 szlcsc.com，没能下载模板原件核对列顺序）。
本表"用量"已含套数和备损，网站上的套数填 1。只生成文件，不下单、不加购物车。
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import market_lib as ml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LCSC_COLS = ["商品编号", "用量", "预设备损量", "位号"]


def rules() -> dict:
    return ml.load_yaml("buy_rules.yaml")


def merge_items(items: list[dict]) -> list[dict]:
    """同一编号同一值的行合并用量，备注拼起来。"""
    out: dict[tuple, dict] = {}
    for it in items:
        key = (it["id"], str(it.get("value", "")))
        if key not in out:
            out[key] = {"id": it["id"], "value": str(it.get("value", "")), "qty": 0, "notes": []}
        out[key]["qty"] += int(it.get("qty", 1))
        if it.get("note"):
            out[key]["notes"].append(str(it["note"]))
    return list(out.values())


def series_code(pid: str, value: str, ser: dict) -> str | None:
    s = ser.get(pid) or {}
    if s.get("same_as"):
        s = ser.get(s["same_as"]) or {}
    for v in s.get("values") or []:
        if str(v.get("value")) == value:
            return v.get("lcsc") or None
    return None


def buy_qty(need: int, pid: str, unit: float | None, min_q: int, R: dict) -> tuple[int, str]:
    """返回（采购量，说明）。"""
    why = []
    if pid.split("-")[0] in R.get("module_prefixes", []):
        spare = int(R.get("module_spare", 0))
        if spare:
            why.append(f"模块备用 +{spare}")
    elif unit is not None and unit < float(R.get("small_price_cny", 0.5)):
        spare = max(math.ceil(need * float(R.get("small_spare_pct", 10)) / 100), int(R.get("small_spare_min", 2)))
        why.append(f"小件备损 +{spare}")
    else:
        spare = int(R.get("other_spare", 0))
        if spare:
            why.append(f"备损 +{spare}")
    q = need + spare
    if unit is not None and unit < float(R.get("small_price_cny", 0.5)) and q < int(R.get("small_min_buy", 10)):
        q = int(R.get("small_min_buy", 10))
        why.append(f"小件至少 {q}")
    if min_q and q < min_q:
        q = min_q
        why.append(f"立创起订 {min_q}")
    return q, "，".join(why)


def cost(prj: dict, today=None) -> dict:
    R = rules()
    rows = {r["id"]: r for r in ml.parts_rows()}
    mk, hist, ser = ml.market(), ml.history(), ml.series()
    sets = int(prj.get("sets", 1))
    lines, missing, warns = [], [], []
    for it in merge_items(prj.get("items") or []):
        pid, val = it["id"], it["value"]
        r = rows.get(pid)
        if not r:
            missing.append({"id": pid, "name": "（parts.csv 里没有这个编号）", "why": "库外件，没有价格"})
            continue
        name = r["name"] + (f" {val}" if val else "")
        code = r["lcsc_id"]
        if val:
            code = series_code(pid, val, ser) or ""
            if not code:
                missing.append({"id": pid, "name": name, "why": f"src/series.yaml 里没有 {val} 这个值"})
                continue
        need = it["qty"] * sets
        m = ml.entry(r, mk, hist)
        p = ml.lcsc_price(pid, code, hist) if code.startswith("C") else None
        base = {"id": pid, "name": name, "code": code, "per_set": it["qty"], "need": need, "notes": it["notes"], "row": r, "m": m}
        if p:
            tiers = p["tiers"]
            min_q = tiers[0][0]
            q, why = buy_qty(need, pid, tiers[0][1], min_q, R)
            tq, tp = ml.pick_tier(tiers, q)
            tier_txt = f"{tq}+ 档 ¥{tp:g}"
            if not p["complete"] and q > tq:
                tier_txt += "（只核到起订档，更高档未核，实际可能更低）"
            age = ml.days_old(p["date"], today)
            if age is not None and age > int(R.get("price_max_age_days", 30)):
                warns.append(f"{pid} {code} 立创价核实于 {p['date']}，已 {age} 天，先跑 python tools/refresh_prices.py")
            lines.append({**base, "shop": "立创", "buy": q, "why": why, "unit": tp, "tier": tier_txt,
                          "src": p["source"], "date": p["date"], "sub": round(q * tp, 4)})
            continue
        if code.startswith("C"):
            missing.append({**base, "shop": "立创", "why": f"{code} 没有价格记录（跑 refresh_prices.py）"})
            continue
        t = ml.taobao_ref_price(m)
        if t is not None:
            q, why = buy_qty(need, pid, None, 0, R)
            lines.append({**base, "shop": "淘宝", "buy": q, "why": why, "unit": t, "tier": "淘宝参考价（中位数）",
                          "src": "src/market.yaml 淘宝店铺明细", "date": m.get("price_checked", ""), "sub": round(q * t, 4)})
        else:
            q, why = buy_qty(need, pid, None, 0, R)
            missing.append({**base, "shop": "淘宝", "buy": q, "why": str(m.get("price_taobao_ref"))})
    lc = round(sum(x["sub"] for x in lines if x["shop"] == "立创"), 2)
    tb = round(sum(x["sub"] for x in lines if x["shop"] == "淘宝"), 2)
    ex = prj.get("extra_cost") or {}
    extra = round(sum(float(v) for k, v in ex.items() if k != "note" and isinstance(v, (int, float))), 2)
    return {"lines": lines, "missing": missing, "warns": warns, "lcsc": lc, "taobao": tb, "extra": extra,
            "total": round(lc + tb + extra, 2), "complete": not missing, "sets": sets}


def write(prj: dict, path: Path, c: dict) -> Path:
    out = path.parent / path.stem
    out.mkdir(parents=True, exist_ok=True)
    name = prj.get("name") or path.stem
    esc = lambda s: str(s).replace("|", "/")
    L = [f"# {name}：成本", "", f"做 {c['sets']} 套。由 `tools/project_cost.py` 生成；价格来源和规则见 `src/market.yaml`、`src/price_history.csv`、`src/buy_rules.yaml`。", ""]
    if c["warns"]:
        L += ["## 提醒", ""] + [f"- {w}" for w in c["warns"]] + [""]
    for shop in ("立创", "淘宝"):
        xs = [x for x in c["lines"] if x["shop"] == shop]
        L += [f"## {shop}", ""]
        if not xs:
            L += ["无", ""]
            continue
        L += ["| 编号 | 名称 | 每套 | 需要 | 实际采购 | 采购量说明 | 所用单价 | 价格档 | 来源 | 核实日期 | 小计 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in xs:
            L.append(f"| {x['id']} | {esc(x['name'])} | {x['per_set']} | {x['need']} | {x['buy']} | {x['why'] or '—'} | ¥{x['unit']:g} | {esc(x['tier'])} | {esc(x['src'])} | {x['date']} | ¥{x['sub']:.2f} |")
        L += ["", f"**{shop}小计：¥{c['lcsc' if shop == '立创' else 'taobao']:.2f}**", ""]
    L += ["## 缺价（没算进总价）", ""]
    if c["missing"]:
        L += ["| 编号 | 名称 | 需要 | 原因 |", "|---|---|---|---|"]
        L += [f"| {x['id']} | {esc(x['name'])} | {x.get('need', '')} | {esc(x['why'])} |" for x in c["missing"]]
    else:
        L.append("无")
    ex = prj.get("extra_cost") or {}
    L += ["", "## 总计", "", f"- 立创小计 ¥{c['lcsc']:.2f}", f"- 淘宝小计 ¥{c['taobao']:.2f}",
          f"- 其他（extra_cost，手填）¥{c['extra']:.2f} {ex.get('note', '')}",
          f"- **总计 ¥{c['total']:.2f}**" + ("" if c["complete"] else f"（总价不完整：缺 {len(c['missing'])} 行价格）"),
          "", "不含运费。立创价是立创商城单只标价；淘宝价是 market.yaml 记录的多家中位数。"]
    (out / "成本.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    with (out / "立创配单.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(LCSC_COLS)
        for x in c["lines"]:
            if x["shop"] == "立创":
                w.writerow([x["code"], x["buy"], "", ""])
        for x in c["missing"]:
            if x.get("shop") == "立创" and x.get("code"):
                w.writerow([x["code"], x.get("buy") or x.get("need", ""), "", ""])

    T = [f"# {name}：淘宝清单", "", "云端不能登录淘宝，下列价格未核的要自己搜。按\"规格选项提醒\"选对版本，针序选错了板子就白打。", "",
         "| 编号 | 名称 | 数量 | 搜索关键词 | 候选店铺 | 参考价 | 规格选项提醒 |", "|---|---|---|---|---|---|---|"]
    tb_items = [x for x in c["lines"] if x["shop"] == "淘宝"] + [x for x in c["missing"] if x.get("shop") == "淘宝"]
    for x in tb_items:
        r, m = x["row"], x["m"]
        ref = f"¥{x['unit']:g}" if "unit" in x else str(m.get("price_taobao_ref"))
        tip = r.get("pitfalls") or "—"
        T.append(f"| {x['id']} | {esc(x['name'])} | {x.get('buy', x['need'])} | {esc(r.get('taobao_keyword', ''))} | {esc(m.get('recommend_shop', ''))} | {esc(ref)} | {esc(tip)} |")
    if not tb_items:
        T.append("| — | 无 | | | | | |")
    (out / "淘宝清单.md").write_text("\n".join(T) + "\n", encoding="utf-8")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    prj = yaml.safe_load(path.read_text(encoding="utf-8"))
    c = cost(prj)
    out = write(prj, path, c)
    for w in c["warns"]:
        print("!", w)
    for x in c["missing"]:
        print("缺价", x["id"], x["name"], x["why"])
    try:
        shown = out.resolve().relative_to(ROOT)
    except ValueError:
        shown = out
    print(f"{prj.get('name') or path.stem}：立创小计 ¥{c['lcsc']:.2f}，淘宝小计 ¥{c['taobao']:.2f}，其他 ¥{c['extra']:.2f}，"
          f"总计 ¥{c['total']:.2f}{'' if c['complete'] else '（总价不完整，缺价 ' + str(len(c['missing'])) + ' 行）'} → {shown}")
    exp = prj.get("expect_total")       # 自测用：手算总价
    if exp is not None and abs(float(exp) - c["total"]) > 0.005:
        print(f"✗ 总价 {c['total']:.2f} 与手算 {float(exp):.2f} 不一致")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
