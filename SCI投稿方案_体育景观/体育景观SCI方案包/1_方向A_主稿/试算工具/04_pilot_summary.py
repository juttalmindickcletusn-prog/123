# -*- coding: utf-8 -*-
"""
步骤 4：汇总试算结果，给出"继续 / 调整 / 放弃"判断。

用法：python 04_pilot_summary.py --in dianping_pilot.csv
判定规则（写在总方案第五部分）：
- 每城市体育公园数 ≥ 8，且总数 ≥ 100（多城市研究的最低样本量）；
- 点评评论数中位数 ≥ 50，且 ≥ 70% 的公园 ≥ 20 条 → 继续；
- 中位数 20–50 → 调整：只保留省会/副省级城市，或加入百度评论、携程评论合并计数；
- 中位数 < 20 → 感知维度改用问卷或热力图，评论仅作补充。
"""
import argparse
import csv
import statistics
from collections import defaultdict


def to_int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="dianping_pilot.csv")
    ap.add_argument("--col", default="dp_review_count", help="评论数列名，可换成 baidu_comment_num")
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    by_city = defaultdict(list)
    for r in rows:
        by_city[r["city"]].append(to_int(r.get(args.col)))

    print(f"{'城市':<6}{'公园数':>6}{'有数据':>8}{'中位数':>8}{'≥20占比':>9}{'≥50占比':>9}")
    all_vals = []
    for city, vals in by_city.items():
        v = [x for x in vals if x is not None]
        all_vals += v
        med = statistics.median(v) if v else float("nan")
        p20 = sum(x >= 20 for x in v) / len(v) if v else 0
        p50 = sum(x >= 50 for x in v) / len(v) if v else 0
        print(f"{city:<6}{len(vals):>6}{len(v):>8}{med:>8.0f}{p20:>9.0%}{p50:>9.0%}")

    if not all_vals:
        print("\n没有可用的评论数，请先完成步骤 2/3。")
        return
    med = statistics.median(all_vals)
    p20 = sum(x >= 20 for x in all_vals) / len(all_vals)
    n_city_ok = sum(len(v) >= 8 for v in by_city.values())
    print(f"\n总体：公园 {len(rows)} 个，有数据 {len(all_vals)} 个，中位数 {med:.0f}，≥20 条占比 {p20:.0%}，满足≥8园的城市 {n_city_ok}/{len(by_city)}")
    if med >= 50 and p20 >= 0.7 and len(rows) >= 100:
        print("判断：继续。评论语料足够支撑'使用 + 感知'两个维度。")
    elif med >= 20:
        print("判断：调整。收缩到评论量高的城市，或合并百度/携程评论数；感知维度仍可用文本。")
    else:
        print("判断：评论量不足。感知维度改用问卷或百度热力图，评论只作补充案例。")


if __name__ == "__main__":
    main()
