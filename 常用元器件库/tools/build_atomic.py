"""生成"一选全带"的原子符号库 kicad/StudentHW_Parts.kicad_sym（不许手改，改数据后重跑本脚本）。

每个条目（符号和封装都不是"不适用"的）生成一个原子符号；src/series.yaml 里的系列件按每个值各生成一个。
- 名字：编号_型号（系列件为 编号_值），只含字母、数字、-、_、.；
- 图形和引脚：从条目引用的基础符号（KiCad 官方库或 StudentHW.kicad_sym）整份复制；extends 展开；
  子单元改名为 新名字_单元号_样式号；
- 属性：Reference、Value、Footprint（= kicad_footprint）、Datasheet、Description、MPN、Manufacturer、LCSC、
  StudentHW_ID、Level、Price_CNY、Price_Date、Taobao_Keyword、Pin1；除 Reference、Value 外全部隐藏；
- ki_keywords：类别、中文名、淘宝关键词，方便在 KiCad 里用中文搜到；去掉 ki_fp_filters（封装已锁定）。
用法：python tools/build_atomic.py
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import market_lib  # noqa: E402
import paths  # noqa: E402
from sexpr import Q, child, children, dump, find_symbol, head, parse  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "kicad" / "StudentHW_Parts.kicad_sym"
LOCAL_SYM = ROOT / "kicad" / "StudentHW.kicad_sym"
PROP_ORDER = ["Reference", "Value", "Footprint", "Datasheet", "Description", "MPN", "Manufacturer", "LCSC",
              "StudentHW_ID", "Level", "Price_CNY", "Price_Date", "Taobao_Keyword", "Pin1", "ki_keywords"]
_libs: dict[str, list] = {}


def lib_node(lib: str):
    if lib not in _libs:
        path = LOCAL_SYM if lib == "StudentHW" else paths.SYM_OFF / f"{lib}.kicad_sym"
        _libs[lib] = parse(path.read_text(encoding="utf-8"))
    return _libs[lib]


def base_symbol(ref: str) -> list:
    """返回展开 extends 后的完整符号（深拷贝）。"""
    lib, name = ref.split(":", 1)
    s = find_symbol(lib_node(lib), name)
    if s is None:
        raise KeyError(f"符号不存在: {ref}")
    s = copy.deepcopy(s)
    ext = child(s, "extends")
    if ext is None:
        return s
    parent = base_symbol(f"{lib}:{ext[1]}")
    # 子符号只覆盖属性（以及少量标志）；图形和引脚全部来自父符号
    own_props = {p[1]: p for p in children(s, "property")}
    merged = [parent[0], Q(name)]
    for x in parent[2:]:
        if head(x) == "property" and x[1] in own_props:
            merged.append(own_props.pop(x[1]))
        else:
            merged.append(x)
    insert_at = max(i for i, x in enumerate(merged) if head(x) == "property") + 1
    for p in own_props.values():
        merged.insert(insert_at, p)
        insert_at += 1
    return merged


def safe(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s.replace("µ", "u").replace("Ω", "R"))
    return re.sub(r"-{2,}", "-", s).strip("-")


def prop(name: str, value: str, at=(0, 0, 0), hide=True) -> list:
    node = ["property", Q(name), Q(value), ["at", *[f"{v:g}" for v in at]], ["show_name", "no"], ["do_not_autoplace", "no"]]
    if hide:
        node.append(["hide", "yes"])
    node.append(["effects", ["font", ["size", "1.27", "1.27"]]])
    return node


def pins_of(sym: list) -> list[tuple[str, str]]:
    out = []
    for unit in children(sym, "symbol"):
        for p in children(unit, "pin"):
            out.append((child(p, "number")[1], child(p, "name")[1]))
    return out


def atomic(row: dict, name: str, value: str, lcsc: str, mpn: str, price: str, price_date: str, keywords: str) -> list:
    base = base_symbol(row["kicad_symbol"])
    sym = [base[0], Q(name)]
    old_props = {p[1]: p for p in children(base, "property")}
    for x in base[2:]:
        if head(x) in ("property", "extends"):
            continue
        if head(x) == "symbol":   # 子单元改名：旧名_单元_样式 → 新名_单元_样式
            x = copy.deepcopy(x)
            m = re.search(r"_(\d+)_(\d+)$", x[1])   # 父符号展开后子单元仍带父名，只取单元号和样式号
            x[1] = Q(f"{name}_{m.group(1)}_{m.group(2)}")
        sym.append(x)
    ref_at = [float(v) for v in child(old_props["Reference"], "at")[1:]] if "Reference" in old_props else [0, 2.54, 0]
    val_at = [float(v) for v in child(old_props["Value"], "at")[1:]] if "Value" in old_props else [0, -2.54, 0]
    ref = old_props.get("Reference", [None, None, Q("U")])[2]
    desc = f"{row['name']}；{row['key_params']}"
    values = {
        "Reference": ref, "Value": value, "Footprint": row["kicad_footprint"], "Datasheet": row["datasheet_url"],
        "Description": desc, "MPN": mpn, "Manufacturer": row["manufacturer"], "LCSC": lcsc,
        "StudentHW_ID": row["id"], "Level": row["level"], "Price_CNY": price, "Price_Date": price_date,
        "Taobao_Keyword": row["taobao_keyword"], "Pin1": row["pin1"], "ki_keywords": keywords,
    }
    props = []
    for k in PROP_ORDER:
        if k in ("Reference", "Value") and k in old_props:   # 沿用基础符号的位置和字体（含 justify）
            node = copy.deepcopy(old_props[k])
            node[2] = Q(values[k])
            node[:] = [x for x in node if head(x) != "hide"]
            props.append(node)
        elif k == "Reference":
            props.append(prop(k, values[k], ref_at, hide=False))
        elif k == "Value":
            props.append(prop(k, values[k], val_at, hide=False))
        else:
            props.append(prop(k, values[k]))
    # 属性放在标志之后、子单元之前
    first_unit = next(i for i, x in enumerate(sym) if head(x) == "symbol")
    return sym[:first_unit] + props + sym[first_unit:]


def price_text(m: dict) -> tuple[str, str]:
    p = m.get("price_lcsc")
    if p:
        q, v = p["tiers"][0]
        return f"{v:g}@{q}+（立创 {p['code']}）", p["date"]
    t = market_lib.taobao_ref_price(m)
    if t is not None:
        return f"{t:g}（淘宝参考中位数）", str(m.get("price_checked", ""))
    return "未核", ""


def items() -> list[tuple[dict, str, str, str, str, str, str, str]]:
    rows = market_lib.parts_rows()
    mk, hist, ser = market_lib.market(), market_lib.history(), market_lib.series()
    out = []
    for row in sorted(rows, key=lambda r: r["id"]):
        if row["kicad_symbol"].startswith("不适用") or row["kicad_footprint"].startswith("不适用"):
            continue
        kw = " ".join(x for x in (row["category"], row["name"], row["taobao_keyword"], row["part_number"]) if x)
        sd = ser.get(row["id"])
        if sd:
            vals = (ser.get(sd["same_as"]) or {}).get("values", []) if sd.get("same_as") else sd.get("values", [])
            for v in vals:
                p = market_lib.lcsc_price(row["id"], v["lcsc"], hist)
                if p is None:   # 母条目以外的值：去别的条目的 jlc.json 找同一 C 编号的记录
                    p = next((market_lib.lcsc_price(r["id"], v["lcsc"], hist) for r in rows
                              if market_lib.lcsc_price(r["id"], v["lcsc"], hist)), None)
                price, date = ((f"{p['tiers'][0][1]:g}@{p['tiers'][0][0]}+（立创 {v['lcsc']}）", p["date"]) if p else ("未核", ""))
                out.append((row, f"{row['id']}_{safe(v['value'])}", v["value"], v["lcsc"],
                            v.get("mpn") or "未核", price, date, f"{kw} {v['value']}"))
        else:
            m = market_lib.entry(row, mk, hist)
            price, date = price_text(m)
            lcsc = row["lcsc_id"] if row["lcsc_id"].startswith("C") else "无（非立创件）"
            out.append((row, f"{row['id']}_{safe(row['part_number'])}", row["sym_value"] or row["part_number"], lcsc,
                        row["part_number"], price, date, kw))
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    syms = []
    for row, name, value, lcsc, mpn, price, date, kw in items():
        syms.append(atomic(row, name, value, lcsc, mpn, price, date, kw))
    lib = ["kicad_symbol_lib", ["version", "20251024"], ["generator", Q("studenthw_atomic")], ["generator_version", Q("10.0")]] + syms
    OUT.write_text(dump(lib) + "\n", encoding="utf-8")
    print(f"原子符号 {len(syms)} 个 → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
