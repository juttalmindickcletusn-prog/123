# 方向 A 数据试算工具

四个脚本按顺序运行，目的是在 1–2 天内回答"多城市体育公园的评论语料够不够"。

```bash
pip install requests playwright
export AMAP_KEY=...      # 高德开放平台 Web 服务 Key（个人认证即可）
export BAIDU_AK=...      # 百度地图开放平台服务端 AK
python 01_amap_sports_parks.py --cities 杭州 成都 武汉 长沙 --out poi_amap.csv
python 02_baidu_popularity.py --in poi_amap.csv --out poi_baidu.csv --limit 90
python 03_dianping_count_pilot.py --in poi_baidu.csv --out dianping_pilot.csv   # 需手动登录
python 04_pilot_summary.py --in dianping_pilot.csv
```

- 步骤 1 产出候选名录；务必与市体育局公告交叉核对后再定稿。
- 步骤 2 的百度评论数可先替代点评做快速判断：`python 04_pilot_summary.py --in poi_baidu.csv --col baidu_comment_num`。
- 步骤 3 只读公开汇总数字，不下载评论正文；每页停留 8 秒以上。
- 所有脚本只依赖 requests / playwright，Python 3.9+。
