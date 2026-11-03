# -*- coding: utf-8 -*-
"""
步骤 2：用百度地图地点检索（scope=2 详情）为每个体育公园补充百度评论数与评分，作为第一轮"使用/感知"代理，
同时交叉核对名录。

用法：
    export BAIDU_AK=你的百度地图服务端AK
    python 02_baidu_popularity.py --in poi_amap.csv --out poi_baidu.csv

说明：
- 接口：https://api.map.baidu.com/place/v2/search  (query=公园名, region=城市, scope=2)
- detail_info.comment_num / overall_rating 即百度地图上的评论数与评分（并非大众点评）。
- 个人开发者约 100 次/日（以控制台为准）；200 个公园要分 2–3 天，或申请企业试用额度。
- 若 comment_num 中位数就已 ≥50，大众点评数据量通常更高，可直接进入正式采集。
"""
import argparse
import csv
import os
import sys
import time

import requests

from coord import bd09_to_wgs84

API = "https://api.map.baidu.com/place/v2/search"


def lookup(ak, name, city):
    params = {"query": name, "region": city, "output": "json", "scope": 2, "page_size": 3, "ak": ak}
    r = requests.get(API, params=params, timeout=20)
    r.raise_for_status()
    js = r.json()
    if js.get("status") != 0:
        print(f"[warn] {city}/{name}: {js.get('message')}", file=sys.stderr)
        return None
    res = js.get("results") or []
    if not res:
        return None
    # 取名称最接近的一条
    res.sort(key=lambda x: (name not in (x.get("name") or ""), ))
    p = res[0]
    d = p.get("detail_info", {}) or {}
    loc = p.get("location") or {}
    wlng, wlat = bd09_to_wgs84(loc.get("lng", 0), loc.get("lat", 0)) if loc else ("", "")
    return {
        "baidu_name": p.get("name"),
        "baidu_uid": p.get("uid"),
        "baidu_comment_num": d.get("comment_num", ""),
        "baidu_rating": d.get("overall_rating", ""),
        "baidu_tag": d.get("tag", ""),
        "baidu_lng_wgs84": round(wlng, 6) if wlng else "",
        "baidu_lat_wgs84": round(wlat, 6) if wlat else "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="poi_amap.csv")
    ap.add_argument("--out", default="poi_baidu.csv")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 条（配额有限时用）")
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    ak = os.environ.get("BAIDU_AK")
    if not ak:
        sys.exit("请先 export BAIDU_AK=...")

    with open(args.inp, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    out = []
    for i, row in enumerate(rows, 1):
        info = lookup(ak, row["name"], row["city"]) or {}
        out.append({**row, **info})
        print(f"{i}/{len(rows)} {row['city']} {row['name']} -> 评论 {info.get('baidu_comment_num', 'NA')} 评分 {info.get('baidu_rating', 'NA')}")
        time.sleep(args.sleep)

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"已写入 {args.out}")


if __name__ == "__main__":
    main()
