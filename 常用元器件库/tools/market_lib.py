"""市场数据（价格、热度、替代、推荐店铺）的统一读取，只存一份，供各脚本共用。

数据来源与优先级：
  1. 立创商城价格、库存：src/price_history.csv 里该 C 编号最新的一条（refresh_prices.py 联网追加）；
     没有记录时退回 evidence/<id>/jlc.json（fetch_evidence.py 写的核实记录）。
  2. 系列件（阻值等）：src/series.yaml，每个值自己的 C 编号和价格。
  3. 淘宝价、热度、替代、推荐店铺：src/market.yaml（人工核实，写来源和日期）。
没有核到的字段一律返回"未核"并带原因，不估数。
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
# 自测可用环境变量 STUDENTHW_PRICE_HISTORY 指向固定价格的样例文件
HISTORY = Path(os.environ.get("STUDENTHW_PRICE_HISTORY") or ROOT / "src" / "price_history.csv")
HIST_FIELDS = ["date", "id", "lcsc", "tiers_cny", "stock", "source"]
NOT_CHECKED_TB = "淘宝未核（需登录）"


def parts_rows() -> list[dict]:
    with (ROOT / "parts.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_yaml(name: str) -> dict:
    p = ROOT / "src" / name
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def parse_tiers(s: str) -> list[tuple[int, float]]:
    out = []
    for t in (s or "").split("|"):
        if ":" in t:
            q, p = t.split(":", 1)
            out.append((int(q), float(p)))
    return sorted(out)


def fmt_tiers(tiers) -> str:
    return "|".join(f"{q}:{p:g}" for q, p in tiers)


def history() -> dict[str, dict]:
    """C 编号 → 最新一条价格记录。"""
    latest: dict[str, dict] = {}
    if not HISTORY.exists():
        return latest
    with HISTORY.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["lcsc"] and (r["lcsc"] not in latest or r["date"] >= latest[r["lcsc"]]["date"]):
                latest[r["lcsc"]] = r
    return latest


def jlc_record(pid: str, code: str) -> dict:
    p = ROOT / "evidence" / pid / "jlc.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    rec = dict(d.get("parts", {}).get(code) or {})
    if rec:
        rec["date"] = d.get("date", "")
    return rec


def lcsc_price(pid: str, code: str, hist: dict | None = None) -> dict | None:
    """立创商城价：{'code','tiers':[(起订量,单价)],'date','stock','source','complete'}；没有返回 None。"""
    if not (code or "").startswith("C"):
        return None
    hist = history() if hist is None else hist
    h = hist.get(code)
    if h and parse_tiers(h["tiers_cny"]):
        return {"code": code, "tiers": parse_tiers(h["tiers_cny"]), "date": h["date"], "stock": h["stock"],
                "source": f"立创商城 {code}（{h['source']}）", "complete": len(parse_tiers(h["tiers_cny"])) > 1}
    rec = jlc_record(pid, code)
    if rec.get("cny_price"):
        return {"code": code, "tiers": [(int(rec.get("cny_step") or 1), float(rec["cny_price"]))], "date": rec["date"],
                "stock": rec.get("szlcsc_stock", ""), "source": f"立创商城 {code}（evidence/{pid}/jlc.json）", "complete": False}
    return None


def pick_tier(tiers: list[tuple[int, float]], qty: int) -> tuple[int, float] | None:
    """按采购量选阶梯：取起订量 ≤ qty 的最高一档；qty 小于最低起订量时返回最低档（要按起订量买）。"""
    if not tiers:
        return None
    ok = [t for t in sorted(tiers) if t[0] <= qty]
    return ok[-1] if ok else sorted(tiers)[0]


def series() -> dict:
    return load_yaml("series.yaml")


def market() -> dict:
    return load_yaml("market.yaml")


def entry(row: dict, mk: dict | None = None, hist: dict | None = None) -> dict:
    """一个条目的市场信息（合并立创接口数据和人工数据）。"""
    mk = market() if mk is None else mk
    m = dict(mk.get(row["id"]) or {})
    m["price_lcsc"] = lcsc_price(row["id"], row["lcsc_id"], hist)
    m.setdefault("price_taobao_ref", NOT_CHECKED_TB)
    m.setdefault("price_taobao_min", NOT_CHECKED_TB)
    m.setdefault("price_unit_basis", "立创：单只单价、不含运费，按标注的起订档；淘宝：未核")
    m.setdefault("sales_level", "未核")
    m.setdefault("sales_evidence", "未核")
    m.setdefault("better_alt", "未写")
    m.setdefault("recommend_shop", "立创商城（按 C 编号下单）" if row["lcsc_id"].startswith("C") else "未核")
    m.setdefault("price_checked", (m["price_lcsc"] or {}).get("date", ""))
    return m


def taobao_ref_price(m: dict) -> float | None:
    ref = m.get("price_taobao_ref")
    if isinstance(ref, dict) and isinstance(ref.get("median"), (int, float)):
        return float(ref["median"])
    return None


def price_brief(m: dict) -> str:
    p = m.get("price_lcsc")
    if p:
        tiers = "，".join(f"¥{v:g}@{q}+" for q, v in p["tiers"])
        return f"{tiers}（{p['code']}，{p['date']}{'' if p['complete'] else '，仅核到起订档'}）"
    t = taobao_ref_price(m)
    if t is not None:
        return f"淘宝参考 ¥{t:g}（{m.get('price_checked', '')}）"
    return "未核"


def days_old(date_s: str, today: dt.date | None = None) -> int | None:
    try:
        d = dt.date.fromisoformat(date_s)
    except (TypeError, ValueError):
        return None
    return ((today or dt.date.today()) - d).days
