"""生成 reports/preview.html：每个条目一张卡片，含封装图、符号图、尺寸证据图、关键字段。

用法：python tools/build_preview.py      （需要 D:/kicad/bin/kicad-cli.exe）
"""
from __future__ import annotations

import csv
import html
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLI = paths.KICAD_CLI
OUT = ROOT / "reports" / "preview"
FP_OFF = paths.FP_OFF
SYM_OFF = paths.SYM_OFF


def run(args):
    env = {**os.environ, "STUDENTHW_DIR": str(ROOT)}
    return subprocess.run([CLI, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def export_fp(ref: str) -> str:
    lib, name = ref.split(":", 1)
    d = OUT / "fp"
    d.mkdir(parents=True, exist_ok=True)  # kicad-cli 不会自己建输出目录
    target = d / f"{name}.svg"
    if not target.exists():
        src = ROOT / "kicad" / "StudentHW.pretty" if lib == "StudentHW" else FP_OFF / f"{lib}.pretty"
        run(["fp", "export", "svg", "--fp", name, "--layers", "F.Cu,F.SilkS,F.Fab,F.CrtYd,Edge.Cuts", "--sp", "--black-and-white",
             "-o", str(d), str(src)])
    return f"preview/fp/{name}.svg" if target.exists() else ""


def export_sym(ref: str) -> str:
    lib, name = ref.split(":", 1)
    d = OUT / "sym" / lib
    d.mkdir(parents=True, exist_ok=True)
    want = [d / f"{name}_unit1.svg", d / f"{name}.svg"]  # 只认完全同名的文件，避免 C 误取 C_Polarized
    if not any(w.exists() for w in want):
        src = ROOT / "kicad" / "StudentHW.kicad_sym" if lib == "StudentHW" else SYM_OFF / f"{lib}.kicad_sym"
        run(["sym", "export", "svg", "--black-and-white", "--symbol", name, "-o", str(d), str(src)])
    hit = next((w for w in want if w.exists()), None)
    return f"preview/sym/{lib}/{hit.name}" if hit else ""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader((ROOT / "parts.csv").open(encoding="utf-8-sig")))
    cards, cats = [], []
    for r in rows:
        fp = export_fp(r["kicad_footprint"]) if ":" in r["kicad_footprint"] else ""
        sym = export_sym(r["kicad_symbol"]) if ":" in r["kicad_symbol"] else ""
        dims = [x for x in r["evidence"].split(";") if x.endswith(".png")]
        pdf = next((x for x in r["evidence"].split(";") if x.endswith(".pdf")), "")
        if r["category"] not in cats:
            cats.append(r["category"])
        e = lambda k: html.escape(r.get(k, ""))
        imgs = "".join(f'<a href="../{html.escape(d)}" target="_blank"><img class="dim" src="../{html.escape(d)}" alt="尺寸图" loading="lazy"></a>' for d in dims[:2])
        fp_img = f'<img class="fp" src="{fp}" alt="封装" loading="lazy">' if fp else '<div class="na">无封装（配件）</div>'
        sym_img = f'<img class="sym" src="{sym}" alt="符号" loading="lazy">' if sym else '<div class="na">无符号</div>'
        cards.append(f'''
<article class="card" data-cat="{e('category')}" data-text="{html.escape((r['id'] + r['name'] + r['part_number'] + r['lcsc_id'] + r['kicad_footprint']).lower())}">
  <header><span class="id">{e('id')}</span><span class="lvl lvl-{e('level')}">{e('level')} 级</span><h2>{e('name')}</h2></header>
  <p class="pn"><b>{e('part_number')}</b>（{e('manufacturer')}）· 立创 <a href="https://item.szlcsc.com/search.html?k={e('lcsc_id')}" target="_blank">{e('lcsc_id')}</a> · {e('jlc_library')} · {e('price_cny')} · 库存 {e('stock')}</p>
  <div class="imgs"><figure>{fp_img}<figcaption>封装 {e('kicad_footprint')}</figcaption></figure>
  <figure>{sym_img}<figcaption>符号 {e('kicad_symbol')}</figcaption></figure></div>
  <div class="dims">{imgs}</div>
  <dl>
    <dt>参数</dt><dd>{e('key_params')}</dd>
    <dt>引脚</dt><dd>{e('pinout')}</dd>
    <dt>尺寸</dt><dd>脚距 {e('pitch_mm')}；引脚 {e('lead_size_mm')}；孔 {e('hole_mm')}；焊盘 {e('pad_mm')}；本体 {e('body_mm')}；安装高 {e('seated_height_mm')}</dd>
    <dt>驱动</dt><dd>{e('logic_level')}</dd>
    <dt>坑</dt><dd class="pit">{e('pitfalls')}</dd>
    <dt>备注</dt><dd>{e('notes')}</dd>
    <dt>依据</dt><dd>{e('dim_source')}{f' · <a href="../{html.escape(pdf)}" target="_blank">规格书</a>' if pdf else ''} · 核实 {e('checked_date')}</dd>
    <dt>替代</dt><dd>{e('alternatives')}</dd>
    <dt>淘宝</dt><dd>{e('taobao_keyword')}</dd>
  </dl>
</article>''')
    buttons = "".join(f'<button data-cat="{html.escape(c)}">{html.escape(c)}</button>' for c in cats)
    levels = {lv: sum(r["level"] == lv for r in rows) for lv in "ABC"}
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>常用元器件库预览</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--fg:#1d2329;--mute:#5d6873;--line:#dde2e7;--acc:#1f6feb;--a:#1a7f37;--b:#9a6700;--c:#cf222e;--img:#fff}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0f1419;--card:#171d24;--fg:#e6edf3;--mute:#9aa7b4;--line:#2b333c;--acc:#58a6ff;--a:#3fb950;--b:#d29922;--c:#f85149;--img:#f4f4f4}}}}
:root[data-theme="dark"]{{--bg:#0f1419;--card:#171d24;--fg:#e6edf3;--mute:#9aa7b4;--line:#2b333c;--acc:#58a6ff;--a:#3fb950;--b:#d29922;--c:#f85149;--img:#f4f4f4}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 system-ui,"Microsoft YaHei",sans-serif}}
.top{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;z-index:2}}
h1{{font-size:18px;margin:0 0 6px}}.sum{{color:var(--mute);margin:0 0 8px}}
input{{width:100%;max-width:420px;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
.cats{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}}button{{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:14px;padding:3px 10px;cursor:pointer}}
button.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,520px),1fr));gap:14px;padding:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-width:0}}
header{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}}h2{{font-size:15px;margin:0;flex-basis:100%}}
.id{{font-weight:700;color:var(--acc)}}.lvl{{font-size:12px;padding:1px 8px;border-radius:10px;color:#fff}}.lvl-A{{background:var(--a)}}.lvl-B{{background:var(--b)}}.lvl-C{{background:var(--c)}}
.pn{{color:var(--mute);margin:6px 0;word-break:break-all}}a{{color:var(--acc)}}
.imgs{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}figure{{margin:0;background:var(--img);border:1px solid var(--line);border-radius:6px;padding:6px;text-align:center}}
figure img{{width:100%;height:150px;object-fit:contain}}figcaption{{font-size:11px;color:#555;word-break:break-all}}.na{{height:150px;display:grid;place-items:center;color:#888}}
.dims{{display:flex;gap:8px;margin-top:8px;overflow-x:auto}}.dim{{height:120px;border:1px solid var(--line);border-radius:6px;background:#fff}}
dl{{display:grid;grid-template-columns:3em 1fr;gap:2px 8px;margin:10px 0 0}}dt{{color:var(--mute)}}dd{{margin:0;word-break:break-word}}.pit{{color:var(--c)}}
</style></head><body>
<div class="top"><h1>常用元器件库预览（第一批：通用元件）</h1>
<p class="sum">{len(rows)} 条 · A 级 {levels["A"]} · B 级 {levels["B"]} · C 级 {levels["C"]} · 点尺寸图看原图 · 数据源 parts.csv</p>
<input id="q" placeholder="搜索编号 / 名称 / 型号 / C 编号 / 封装名">
<div class="cats"><button data-cat="" class="on">全部</button>{buttons}</div></div>
<main id="list">{"".join(cards)}</main>
<script>
const q=document.getElementById('q');let cat='';
function f(){{const t=q.value.trim().toLowerCase();document.querySelectorAll('.card').forEach(c=>{{c.style.display=(!cat||c.dataset.cat===cat)&&(!t||c.dataset.text.includes(t))?'':'none'}})}}
q.addEventListener('input',f);
document.querySelectorAll('.cats button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.cats button').forEach(x=>x.classList.remove('on'));b.classList.add('on');cat=b.dataset.cat;f()}});
</script></body></html>'''
    (ROOT / "reports" / "preview.html").write_text(page, encoding="utf-8")
    miss = [r["id"] for r in rows if ":" in r["kicad_footprint"] and not export_fp(r["kicad_footprint"])]
    miss_s = [r["id"] for r in rows if ":" in r["kicad_symbol"] and not export_sym(r["kicad_symbol"])]
    print(f"preview.html：{len(rows)} 张卡片；缺封装图 {miss}；缺符号图 {miss_s}")
    return 1 if miss or miss_s else 0


if __name__ == "__main__":
    raise SystemExit(main())
