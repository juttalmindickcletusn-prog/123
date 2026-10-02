"""嘉立创/立创公开接口（免登录）的查询封装。只读查询，不下单、不登录。

用法：
  python tools/lcsc_api.py search 关键词 [关键词 ...] [--pkg 封装子串] [--n 15]
  python tools/lcsc_api.py detail C6186
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "api_cache"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}


def _get(url: str, data: bytes | None = None, retries: int = 4) -> bytes:
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as exc:  # 429 或网络抖动：退避重试
            if i == retries - 1:
                raise
            time.sleep(3 * (i + 1))
    raise RuntimeError("unreachable")


def search(keyword: str, page_size: int = 30) -> list[dict]:
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": page_size,
                       "searchSource": "search"}).encode()
    raw = _get("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList", body)
    d = json.loads(raw)
    return (d.get("data") or {}).get("componentPageInfo", {}).get("list") or []


def detail(code: str, use_cache: bool = True) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"jlc_{code}.json"
    if use_cache and f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    raw = _get(f"https://cart.jlcpcb.com/shoppingCart/smtGood/getComponentDetail?componentCode={code}")
    d = json.loads(raw).get("data") or {}
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def szlcsc(code: str, use_cache: bool = True) -> dict:
    """立创商城（国内）人民币价格与库存，取自立创 EDA 专业版的商品搜索接口（与商城同源）。"""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"lceda_{code}.json"
    if use_cache and f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
    else:
        raw = _get(f"https://pro.lceda.cn/api/eda/product/search?keyword={code}", retries=2)
        d = json.loads(raw)
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    hit = next((x for x in (d.get("result") or {}).get("productList") or [] if x.get("code") == code), None)
    if not hit:
        return {"szlcsc": {}, "lcsc": {}, "title": ""}
    pl = hit.get("priceList") or [{}]
    pdf = hit.get("pdfFileUrl") or ""
    return {"szlcsc": {"price": pl[0].get("price"), "min": pl[0].get("startNumber"), "stock": hit.get("stockNumber")},
            "lcsc": {}, "title": hit.get("model", ""),
            "pdf": ("https://atta.szlcsc.com" + pdf) if pdf.startswith("/") else pdf}


def price_str(prices: list[dict]) -> str:
    if not prices:
        return ""
    p = prices[0]
    return f"${p['productPrice']}@{p['startNumber']}+"


def _main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "search":
        pkg, n, kws = None, 15, []
        it = iter(args[1:])
        for a in it:
            if a == "--pkg":
                pkg = next(it)
            elif a == "--n":
                n = int(next(it))
            else:
                kws.append(a)
        rows = []
        for kw in kws:
            rows += search(kw)
        seen, out = set(), []
        for r in rows:
            if r["componentCode"] in seen:
                continue
            seen.add(r["componentCode"])
            if pkg and pkg.lower() not in (r.get("componentSpecificationEn") or "").lower():
                continue
            out.append(r)
        out.sort(key=lambda r: -(r.get("stockCount") or 0))
        for r in out[:n]:
            print(f"{r['componentCode']:10} stock={r.get('stockCount',0):>8} {price_str(r.get('componentPrices')):14} "
                  f"{r.get('componentLibraryType',''):6} {r.get('componentSpecificationEn','')[:18]:18} "
                  f"{r.get('componentBrandEn','')[:22]:22} {r.get('componentModelEn','')[:34]:34} | {(r.get('describe') or '')[:110]}")
    elif args[0] == "detail":
        for code in args[1:]:
            d = detail(code, use_cache=False)
            s = szlcsc(code, use_cache=False)
            print(f"{code}: {d.get('componentBrandEn')} | {d.get('componentModelEn')} | {d.get('componentSpecificationEn')} | "
                  f"stock={d.get('stockCount')} lib={d.get('componentLibraryType')} | szlcsc ¥{s['szlcsc'].get('price')} stock={s['szlcsc'].get('stock')}")
            print("   ", d.get("describe"))
            print("   ", d.get("dataManualUrl"))


if __name__ == "__main__":
    _main()
