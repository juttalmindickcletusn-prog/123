"""刷新立创商城价格和库存，追加到 src/price_history.csv（只读查询，不登录、不下单、不加购物车）。

用法：
  python tools/refresh_prices.py                 # 刷新 parts.csv 全部 C 编号 + series.yaml 各值
  python tools/refresh_prices.py RES-001 LED-001 # 只刷这几个条目（含其系列值）
  python tools/refresh_prices.py --check         # 不联网：只看最新记录，报"超过 30 天""库存低"
  python tools/refresh_prices.py --from-json DIR # 不联网：用 DIR/<C编号>.json 代替接口返回（自测用）

接口：https://pro.lceda.cn/api/eda/product/search?keyword=<C编号>（交接文档第 9 节），取 priceList[].startNumber/price
和 stockNumber。限速（buy_rules.yaml refresh.delay_s），缓存到 build/api_cache/（refresh.cache_hours 内不重复请求）。
报警：库存低于 refresh.low_stock_qty；与上一条记录比任一档价格变化超过 refresh.change_pct%；核实日期超过 price_max_age_days。
起订递增量（倍数）的接口字段没有核实过，不读不写；project_cost.py 按 1 处理。
有报警时退出码仍为 0（报警不是错误）；联网失败的编号列出来，退出码 1。
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import market_lib as ml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "api_cache"
API = "https://pro.lceda.cn/api/eda/product/search?keyword={}"
SOURCE = "refresh_prices.py（pro.lceda.cn 商品搜索接口）"


def targets(only: list[str]) -> list[tuple[str, str]]:
    """（条目编号，C 编号）列表，去重。"""
    out, seen = [], set()
    rows = ml.parts_rows()
    ser = ml.series()
    for r in rows:
        if only and r["id"] not in only:
            continue
        codes = [r["lcsc_id"]] if r["lcsc_id"].startswith("C") else []
        s = ser.get(r["id"]) or {}
        if s.get("same_as"):
            s = {}
        codes += [v["lcsc"] for v in s.get("values") or [] if str(v.get("lcsc", "")).startswith("C")]
        for c in codes:
            if c not in seen:
                seen.add(c)
                out.append((r["id"], c))
    return out


def fetch(code: str, R: dict, from_dir: Path | None) -> dict:
    if from_dir:
        return json.loads((from_dir / f"{code}.json").read_text(encoding="utf-8"))
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"lceda_{code}.json"
    if f.exists() and time.time() - f.stat().st_mtime < float(R.get("cache_hours", 12)) * 3600:
        return json.loads(f.read_text(encoding="utf-8"))
    req = urllib.request.Request(API.format(code), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    f.write_bytes(raw)
    time.sleep(float(R.get("delay_s", 1.5)))
    return json.loads(raw)


def parse(d: dict, code: str) -> tuple[list[tuple[int, float]], str] | None:
    hit = next((x for x in (d.get("result") or {}).get("productList") or [] if x.get("code") == code), None)
    if not hit:
        return None
    tiers = sorted((int(p["startNumber"]), float(p["price"])) for p in hit.get("priceList") or []
                   if p.get("startNumber") is not None and p.get("price") is not None)
    return tiers, str(hit.get("stockNumber", ""))


def compare(old: dict | None, tiers, stock: str, R: dict, Rall: dict) -> list[str]:
    w = []
    low = int(R.get("low_stock_qty", 200))
    if stock.isdigit() and int(stock) < low:
        w.append(f"库存 {stock} 低于 {low}")
    if old:
        prev = dict(ml.parse_tiers(old["tiers_cny"]))
        for q, p in tiers:
            if q in prev and prev[q] and abs(p - prev[q]) / prev[q] * 100 > float(R.get("change_pct", 10)):
                w.append(f"{q}+ 档价格 ¥{prev[q]:g} → ¥{p:g}（变化 {round((p - prev[q]) / prev[q] * 100)}%，上次 {old['date']}）")
    return w


def check_only(Rall: dict) -> int:
    hist = ml.history()
    R = Rall.get("refresh") or {}
    max_age = int(Rall.get("price_max_age_days", 30))
    old, low = [], []
    for pid, code in targets([]):
        h = hist.get(code)
        if not h:
            continue
        age = ml.days_old(h["date"])
        if age is not None and age > max_age:
            old.append(f"{pid} {code}（{h['date']}，{age} 天）")
        if h["stock"].isdigit() and int(h["stock"]) < int(R.get("low_stock_qty", 200)):
            low.append(f"{pid} {code} 库存 {h['stock']}（{h['date']}）")
    n = len(targets([]))
    have = sum(1 for _, c in targets([]) if c in hist)
    for x in old:
        print("! 超过", max_age, "天：", x)
    for x in low:
        print("! 库存低：", x)
    print(f"价格新鲜度：C 编号 {n} 个，有记录 {have} 个，超过 {max_age} 天 {len(old)} 个，库存低 {len(low)} 个"
          f"（联网刷新：python tools/refresh_prices.py）")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    Rall = ml.load_yaml("buy_rules.yaml")
    R = Rall.get("refresh") or {}
    if "--check" in args:
        return check_only(Rall)
    from_dir = None
    if "--from-json" in args:
        i = args.index("--from-json")
        from_dir = Path(args[i + 1])
        del args[i:i + 2]
    hist = ml.history()
    today = dt.date.today().isoformat()
    new_rows, warns, fails = [], [], []
    for pid, code in targets(args):
        try:
            got = parse(fetch(code, R, from_dir), code)
        except Exception as exc:  # 网络被拦、限流等
            fails.append(f"{pid} {code}：{type(exc).__name__} {exc}"[:160])
            continue
        if not got or not got[0]:
            fails.append(f"{pid} {code}：接口没有返回这个编号的价格")
            continue
        tiers, stock = got
        for w in compare(hist.get(code), tiers, stock, R, Rall):
            warns.append(f"{pid} {code} {w}")
        new_rows.append({"date": today, "id": pid, "lcsc": code, "tiers_cny": ml.fmt_tiers(tiers), "stock": stock, "source": SOURCE})
    if new_rows:
        exists = ml.HISTORY.exists()
        with ml.HISTORY.open("a", encoding="utf-8-sig" if not exists else "utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ml.HIST_FIELDS)
            if not exists:
                w.writeheader()
            w.writerows(new_rows)
    for w in warns:
        print("!", w)
    for x in fails:
        print("✗", x)
    print(f"刷新：成功 {len(new_rows)} 个，报警 {len(warns)} 条，失败 {len(fails)} 个 → {ml.HISTORY.name}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
