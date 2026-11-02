# -*- coding: utf-8 -*-
"""
步骤 1：用高德 Web 服务 API 按关键字抓取各城市的"体育公园"POI，生成名录初稿。

用法：
    export AMAP_KEY=你的高德Web服务Key
    python 01_amap_sports_parks.py --cities 杭州 成都 武汉 长沙 --out poi_amap.csv

说明：
- 接口：搜索 POI 2.0  https://restapi.amap.com/v5/place/text
- 关键字策略：先用"体育公园"，再用"运动公园""全民健身中心""体育主题公园"补漏，结果按 id 去重。
- 个人认证 Key 日配额较低（登录控制台查看），4 个城市 × 4 关键字 × ≤10 页 ≈ 160 次，一般一天能跑完。
- 输出含 GCJ-02 原始坐标与转换后的 WGS-84 坐标，以及高德评分（business.rating，可能为空）。
- 名录必须再与市体育局/政府公告交叉核对，论文中注明名录构成方式。
"""
import argparse
import csv
import os
import sys
import time

import requests

from coord import gcj02_to_wgs84

API = "https://restapi.amap.com/v5/place/text"
KEYWORDS = ["体育公园", "运动公园", "体育主题公园", "全民健身中心"]
# 高德 POI 类型码：080000 体育休闲服务；110100 公园广场。用于过滤明显无关结果。
KEEP_TYPE_PREFIX = ("08", "1101")


def fetch_city(key, city, keyword, page_size=25, max_pages=10, sleep=0.35):
    rows = []
    for page in range(1, max_pages + 1):
        params = {
            "key": key,
            "keywords": keyword,
            "region": city,
            "city_limit": "true",
            "page_size": page_size,
            "page_num": page,
            "show_fields": "business,children",
        }
        r = requests.get(API, params=params, timeout=20)
        r.raise_for_status()
        js = r.json()
        if js.get("status") != "1":
            print(f"[warn] {city}/{keyword} p{page}: {js.get('info')} ({js.get('infocode')})", file=sys.stderr)
            break
        pois = js.get("pois", [])
        if not pois:
            break
        for p in pois:
            lng, lat = map(float, p["location"].split(","))
            wlng, wlat = gcj02_to_wgs84(lng, lat)
            biz = p.get("business", {}) or {}
            rows.append({
                "city": city,
                "keyword": keyword,
                "id": p.get("id"),
                "name": p.get("name"),
                "typecode": p.get("typecode"),
                "type": p.get("type"),
                "address": p.get("address"),
                "adname": p.get("adname"),
                "lng_gcj02": lng,
                "lat_gcj02": lat,
                "lng_wgs84": round(wlng, 6),
                "lat_wgs84": round(wlat, 6),
                "amap_rating": biz.get("rating", ""),
                "amap_opentime": biz.get("opentime_today", ""),
            })
        if len(pois) < page_size:
            break
        time.sleep(sleep)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", nargs="+", required=True)
    ap.add_argument("--out", default="poi_amap.csv")
    ap.add_argument("--keywords", nargs="*", default=KEYWORDS)
    ap.add_argument("--no-filter", action="store_true", help="不按类型码过滤")
    args = ap.parse_args()

    key = os.environ.get("AMAP_KEY")
    if not key:
        sys.exit("请先 export AMAP_KEY=...")

    seen, out = set(), []
    for city in args.cities:
        for kw in args.keywords:
            rows = fetch_city(key, city, kw)
            n_new = 0
            for row in rows:
                if row["id"] in seen:
                    continue
                if not args.no_filter and not str(row["typecode"]).startswith(KEEP_TYPE_PREFIX):
                    continue
                # 名称里必须含"公园"或"体育/运动/健身"，排除"XX体育公园店"这类商铺
                nm = row["name"] or ""
                if nm.endswith("店") or "停车场" in nm or "公交站" in nm or "地铁站" in nm:
                    continue
                seen.add(row["id"])
                out.append(row)
                n_new += 1
            print(f"{city} / {kw}: 抓到 {len(rows)} 条，新增 {n_new} 条")

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["city"])
        w.writeheader()
        w.writerows(out)
    print(f"共 {len(out)} 个候选体育公园，已写入 {args.out}")


if __name__ == "__main__":
    main()
