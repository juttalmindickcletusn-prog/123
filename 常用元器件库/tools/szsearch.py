"""立创商城（中文）商品搜索：python build/szsearch.py 关键词 [N]"""
import json,sys,urllib.request,urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
kw=sys.argv[1];n=int(sys.argv[2]) if len(sys.argv)>2 else 12
u='https://pro.lceda.cn/api/eda/product/search?keyword='+urllib.parse.quote(kw)+'&pageSize=50'
d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read())
pl=d['result']['productList'];pl.sort(key=lambda p:-int(p.get('stockNumber') or 0))
for p in pl[:n]:
    pr=(p.get('priceList') or [{}])[0].get('price')
    print(f"{p['code']:10} stock={p.get('stockNumber'):>7} ¥{pr} {p.get('brandName','')[:14]:14} {p.get('model','')[:34]:34} | {p.get('name','')[:40]} | {p.get('standard','')}")
