"""按 tools/module_defs.py 生成模块封装（StudentHW.pretty）和符号（StudentHW.kicad_sym）。

封装规则（规范第 5、7 条）：
- 焊盘按排针/排母：孔 1.0，焊盘 1.7，1 脚方焊盘；
- 丝印画模块实际外框；引脚名印在外框之外，模块插上后仍能看见；首尾脚和天线/USB 方向印出；
- Fab 层画外框、伸出部分（天线）和安装孔（只画不钻）；courtyard = 外框外扩 0.5；
- 属性 Module_Height 写明模块插上后底面离板高度。
用法：python tools/gen_modules.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_footprints import Pad, circle, courtyard, line, rect_lines, text, f, OUT, VERSION  # noqa: E402
from module_defs import MODULES, SYMBOLS, P  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SYM = ROOT / "kicad" / "StudentHW.kicad_sym"
HOLE, PAD = 1.0, 1.7
STEP = {"down": (0, 1), "up": (0, -1), "right": (1, 0), "left": (-1, 0)}


def pins_of(m):
    out = []
    for r in m["rows"]:
        dx, dy = STEP[r["dir"]]
        x0, y0 = r["start"]
        pitch = r.get("pitch", P)
        for i, nm in enumerate(r["names"]):
            out.append((str(r["first"] + i), x0 + dx * pitch * i, y0 + dy * pitch * i, nm, r["side"]))
    return out


def jtext(s, x, y, rot, just, size=0.8):
    th = round(size * 0.15, 3)
    j = f" (justify {just})" if just else ""
    return (f'\t(fp_text user "{s}" (at {f(x)} {f(y)} {f(rot)}) (layer "F.SilkS") '
            f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)})){j}))')


def footprint(m):
    x0, y0, x1, y1 = m["board"]
    pins = pins_of(m)
    hole, pad = m.get("hole", HOLE), m.get("pad", PAD)
    pads = [Pad(n, "thru_hole", "rect" if n == "1" else "circle", x, y, pad, pad, hole) for n, x, y, _, _ in pins]
    items = rect_lines(x0, y0, x1, y1, "F.Fab") + rect_lines(x0, y0, x1, y1, "F.SilkS")
    boxes = [(x0, y0, x1, y1)]
    if m.get("overhang"):
        ox0, oy0, ox1, oy1 = m["overhang"]
        items += rect_lines(ox0, oy0, ox1, oy1, "F.Fab")
        boxes.append((ox0, oy0, ox1, oy1))
    for hx, hy, hd in m.get("holes", []):
        items.append(circle(hx, hy, hd / 2, "F.Fab"))
        items.append(text("M", hx, hy, "F.Fab", 0.8))
    gap = 0.6
    for n, x, y, nm, side in pins:
        if side == "left":
            items.append(jtext(nm, x0 - gap, y, 0, "right"))
        elif side == "right":
            items.append(jtext(nm, x1 + gap, y, 0, "left"))
        elif side == "top":
            items.append(jtext(nm, x, y0 - gap, 90, "left"))
        else:
            items.append(jtext(nm, x, y1 + gap, 90, "right"))
    # 1 脚标记：外框外侧三角
    n, x, y, nm, side = pins[0]
    if side in ("left", "right"):
        ex = x0 - 0.3 if side == "left" else x1 + 0.3
        items += [line(ex, y - 0.5, ex, y + 0.5, "F.SilkS")]
    for s, lx, ly, rot in m.get("labels", []):
        items.append(jtext(s, lx, ly, rot, "", 1.0))
    # courtyard 要把外框外的引脚名也包进去，避免与相邻元件的丝印重叠
    longest = max(len(nm) for _, _, _, nm, _ in pins) * 0.8 * 0.75 + gap + 0.3
    sides = {p[4] for p in pins}
    cx0 = x0 - (longest if "left" in sides else 0)
    cx1 = x1 + (longest if "right" in sides else 0)
    cy0 = y0 - (longest if "top" in sides else 0)
    cy1 = y1 + (longest if "bottom" in sides else 0)
    lab = [(lx - len(s) * 0.45, ly - 0.7, lx + len(s) * 0.45, ly + 0.7) for s, lx, ly, rot in m.get("labels", []) if rot == 0]
    lab += [(lx - 0.7, ly - len(s) * 0.45, lx + 0.7, ly + len(s) * 0.45) for s, lx, ly, rot in m.get("labels", []) if rot == 90]
    items += courtyard(boxes + [(cx0, cy0, cx1, cy1)] + lab, 0.5)
    name = m["name"]
    body = [f'(footprint "{name}"', f"\t(version {VERSION})", '\t(generator "studenthw_gen")', '\t(layer "F.Cu")',
            f'\t(descr "{m["descr"]}")', f'\t(tags "module")',
            text("REF**", (x0 + x1) / 2, (y0 + y1) / 2 - 2, "F.Fab", kind="Reference"),
            text(name, (x0 + x1) / 2, (y0 + y1) / 2, "F.Fab", kind="Value", size=0.8),
            f'\t(property "Module_Height" "{m["height"]}" (at {f((x0 + x1) / 2)} {f((y0 + y1) / 2 + 2)} 0) (layer "F.Fab") (hide yes) '
            f'(effects (font (size 1 1) (thickness 0.15))))',
            "\t(attr through_hole)"]
    body += items + [p.sexpr() for p in pads] + [")"]
    (OUT / f"{name}.kicad_mod").write_text("\n".join(body) + "\n", encoding="utf-8")


def etype(nm):
    u = nm.upper()
    if u in ("GND", "G") or u.startswith("GND"):
        return "power_in"
    if u in ("3V3", "5V", "VCC", "VIN", "VBAT", "3.3V", "+5V"):
        return "power_in"
    if u in ("RSV", "NC"):
        return "no_connect"
    return "bidirectional"


def font():
    return "(effects (font (size 1.27 1.27)))"


def symbol(m):
    name = m["name"].replace("Module_", "")
    pins = pins_of(m)
    groups = m.get("sym_groups", [[0]])
    rows = m["rows"]
    per = []
    idx = 0
    starts = []
    for r in rows:
        starts.append(idx)
        idx += len(r["names"])
    sides = []
    for g in groups:
        lst = []
        for ri in g:
            lst += pins[starts[ri]:starts[ri] + len(rows[ri]["names"])]
        sides.append(lst)
    # 右侧排按物理自下而上编号，符号上按脚号从上到下更好查
    sides = [sorted(s, key=lambda p: int(p[0])) for s in sides]
    nmax = max(len(s) for s in sides)
    h = (nmax + 1) * P
    wname = max(len(p[3]) for p in pins) * 1.0 + 2
    w = max(10.16, math.ceil(wname * 2 / P) * P) if len(sides) == 2 else max(7.62, math.ceil(wname / P) * P + P)
    top = math.floor(h / 2 / P) * P
    x_l, x_r = -w / 2, w / 2
    out = [f'\t(symbol "{name}"', "\t\t(pin_names (offset 1.016))", "\t\t(exclude_from_sim no)", "\t\t(in_bom yes)",
           "\t\t(on_board yes)",
           f'\t\t(property "Reference" "U" (at 0 {f(top + 1.27)} 0) {font()})',
           f'\t\t(property "Value" "{name}" (at 0 {f(top - h - 1.27)} 0) {font()})',
           f'\t\t(property "Footprint" "StudentHW:{m["name"]}" (at 0 0 0) (hide yes) {font()})',
           '\t\t(property "Datasheet" "" (at 0 0 0) (hide yes) ' + font() + ")",
           f'\t\t(property "Description" "{m["descr"]}" (at 0 0 0) (hide yes) {font()})',
           f'\t\t(symbol "{name}_0_1"',
           f"\t\t\t(rectangle (start {f(x_l)} {f(top)}) (end {f(x_r)} {f(top - h)}) (stroke (width 0.254) (type default)) (fill (type background)))",
           "\t\t)", f'\t\t(symbol "{name}_1_1"']
    for si, s in enumerate(sides):
        for k, (n, _, _, nm, _) in enumerate(s):
            y = top - P * (k + 1)
            if si == 0:
                x, rot = x_l - P, 0
            else:
                x, rot = x_r + P, 180
            out.append(f'\t\t\t(pin {etype(nm)} line (at {f(x)} {f(y)} {rot}) (length 2.54) '
                       f'(name "{nm}" {font()}) (number "{n}" {font()}))')
    out += ["\t\t)", "\t\t(embedded_fonts no)", "\t)"]
    return "\n".join(out)


def plain_symbol(d):
    """只有符号的条目：左右两列引脚。"""
    name = d["name"]
    sides = [d["left"], d["right"]] if d["right"] else [d["left"]]
    nmax = max(len(s) for s in sides)
    h = (nmax + 1) * P
    w = 10.16
    top = math.floor(h / 2 / P) * P
    out = [f'	(symbol "{name}"', "		(pin_names (offset 1.016))", "		(exclude_from_sim no)", "		(in_bom yes)",
           "		(on_board yes)",
           f'		(property "Reference" "U" (at 0 {f(top + 1.27)} 0) {font()})',
           f'		(property "Value" "{name}" (at 0 {f(top - h - 1.27)} 0) {font()})',
           f'		(property "Footprint" "{d["fp"]}" (at 0 0 0) (hide yes) {font()})',
           '		(property "Datasheet" "" (at 0 0 0) (hide yes) ' + font() + ")",
           f'		(property "Description" "{d["descr"]}" (at 0 0 0) (hide yes) {font()})',
           f'		(symbol "{name}_0_1"',
           f"			(rectangle (start {f(-w / 2)} {f(top)}) (end {f(w / 2)} {f(top - h)}) (stroke (width 0.254) (type default)) (fill (type background)))",
           "		)", f'		(symbol "{name}_1_1"']
    for si, s in enumerate(sides):
        for k, (n, nm) in enumerate(s):
            y = top - P * (k + 1)
            x, rot = (-w / 2 - P, 0) if si == 0 else (w / 2 + P, 180)
            out.append(f'			(pin passive line (at {f(x)} {f(y)} {rot}) (length 2.54) '
                       f'(name "{nm}" {font()}) (number "{n}" {font()}))')
    out += ["		)", "		(embedded_fonts no)", "	)"]
    return "\n".join(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    syms = []
    for m in MODULES.values():
        footprint(m)
        syms.append(symbol(m))
    for d in SYMBOLS.values():
        syms.append(plain_symbol(d))
    SYM.write_text("(kicad_symbol_lib\n\t(version 20251024)\n\t(generator \"studenthw_gen\")\n\t(generator_version \"10.0\")\n"
                   + "\n".join(syms) + "\n)\n", encoding="utf-8")
    print(f"模块封装 {len(MODULES)} 个，符号 {len(syms)} 个 → {SYM.name}")


if __name__ == "__main__":
    main()
