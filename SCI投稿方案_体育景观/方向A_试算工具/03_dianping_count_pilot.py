# -*- coding: utf-8 -*-
"""
步骤 3：大众点评评论量试算（半人工 + Playwright 读取已登录浏览器中的公开页面）。

目的：只读取每个体育公园在点评上的"评价数"和"评分"两个公开汇总数字，判断评论语料是否够用
（判定门槛：每园评论数中位数 ≥ 50，且 ≥ 70% 的公园 ≥ 20 条）。本脚本不下载评论正文。

合规边界（写进论文 Methods 的内容也一样）：
- 用自己正常登录的浏览器会话，不绕过登录/验证码；每页停留 ≥ 8 秒；只读公开汇总数字；不采集用户身份信息。
- 正式语料采集阶段同样只取公开评论文本与时间，匿名化后保存，仅限学术用途。

用法：
    pip install playwright && playwright install chromium
    python 03_dianping_count_pilot.py --in poi_baidu.csv --out dianping_pilot.csv
    第一次运行会打开浏览器，请手动登录点评并完成可能的验证，然后回到终端按回车。

如果不想用脚本：也可以直接在点评 App 逐个搜索公园名，把"评价数""评分"手填进 CSV 的
dp_review_count / dp_rating 两列，再运行 04_pilot_summary.py。
"""
import argparse
import csv
import re
import time
import urllib.parse

from playwright.sync_api import sync_playwright

SEARCH = "https://www.dianping.com/search/keyword/{cityid}/0_{kw}"
# 常用城市 ID（点评）；其他城市请在浏览器地址栏确认后补充
CITY_ID = {"上海": 1, "北京": 2, "杭州": 3, "南京": 5, "武汉": 6, "成都": 8, "深圳": 7, "广州": 4,
           "重庆": 9, "西安": 17, "长沙": 344, "郑州": 160, "济南": 22, "青岛": 21, "合肥": 110,
           "福州": 14, "厦门": 15, "昆明": 24, "南昌": 19, "贵阳": 258, "沈阳": 18, "哈尔滨": 20,
           "天津": 10, "苏州": 11, "宁波": 13}

NUM_RE = re.compile(r"(\d+)\s*条?评价")
RATING_RE = re.compile(r"(\d\.\d)\s*分")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="poi_baidu.csv")
    ap.add_argument("--out", default="dianping_pilot.csv")
    ap.add_argument("--dwell", type=float, default=8.0)
    ap.add_argument("--profile", default="./dp_profile", help="持久化浏览器目录（保存登录态）")
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(args.profile, headless=False)
        page = ctx.new_page()
        page.goto("https://www.dianping.com/")
        input("请在浏览器中登录大众点评，完成后回到终端按回车继续...")

        for i, row in enumerate(rows, 1):
            city, name = row["city"], row["name"]
            cid = CITY_ID.get(city)
            row.setdefault("dp_review_count", "")
            row.setdefault("dp_rating", "")
            row.setdefault("dp_matched_name", "")
            if not cid:
                print(f"[skip] 未知城市 ID：{city}")
                continue
            url = SEARCH.format(cityid=cid, kw=urllib.parse.quote(name))
            try:
                page.goto(url, timeout=30000)
                time.sleep(args.dwell)
                txt = page.inner_text("body")
                # 取第一条结果附近的文字
                m_num = NUM_RE.search(txt)
                m_rate = RATING_RE.search(txt)
                row["dp_review_count"] = m_num.group(1) if m_num else ""
                row["dp_rating"] = m_rate.group(1) if m_rate else ""
                row["dp_matched_name"] = name
                print(f"{i}/{len(rows)} {city} {name}: 评价 {row['dp_review_count'] or 'NA'} 评分 {row['dp_rating'] or 'NA'}")
            except Exception as e:  # noqa: BLE001
                print(f"[error] {city} {name}: {e}")
        ctx.close()

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"已写入 {args.out}；若正则未匹配到数字，请打开页面人工核对并手填。")


if __name__ == "__main__":
    main()
