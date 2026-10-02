"""生成 StudentHW 自建封装（尺寸全部来自 evidence/ 里的厂家图纸，见每个封装的 descr）。

两类：
  1. 改官方封装：只改焊盘/孔径，丝印碰到新焊盘的部分自动剪掉，重算 courtyard，3D 沿用官方模型；
  2. 按厂家推荐焊盘图新画：3D 用立创 EasyEDA 导出的模型（复制到 kicad/StudentHW.3dshapes），
     封装坐标系与 EasyEDA 原封装一致，保证模型对齐。

用法：python tools/gen_footprints.py      （会覆盖下面列出的封装，不动从 V1.1 复制来的 A 级封装）
"""
from __future__ import annotations

import math
import re
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "kicad" / "StudentHW.pretty"
OUT3D = ROOT / "kicad" / "StudentHW.3dshapes"
OFFICIAL = paths.FP_OFF
EASY3D = ROOT / "build" / "easyeda" / "EasyEDA.3dshapes"
VERSION = "20260206"
SILK_W, FAB_W, CRT_W = 0.12, 0.10, 0.05
SILK_CLEAR = 0.2  # 丝印离焊盘


def f(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------- 图元 ----------
def line(x1, y1, x2, y2, layer, w=None):
    w = w or {"F.SilkS": SILK_W, "F.Fab": FAB_W, "F.CrtYd": CRT_W}.get(layer, 0.1)
    return (f'\t(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) '
            f'(stroke (width {f(w)}) (type solid)) (layer "{layer}"))')


def rect_lines(x1, y1, x2, y2, layer):
    return [line(x1, y1, x2, y1, layer), line(x2, y1, x2, y2, layer),
            line(x2, y2, x1, y2, layer), line(x1, y2, x1, y1, layer)]


def circle(cx, cy, r, layer, w=None):
    w = w or {"F.SilkS": SILK_W, "F.Fab": FAB_W, "F.CrtYd": CRT_W}.get(layer, 0.1)
    return (f'\t(fp_circle (center {f(cx)} {f(cy)}) (end {f(cx + r)} {f(cy)}) '
            f'(stroke (width {f(w)}) (type solid)) (fill no) (layer "{layer}"))')


def text(s, x, y, layer, size=1.0, kind="user", hidden=False, rot=0):
    th = round(size * 0.15, 3)
    head = f'\t(fp_text user "{s}"' if kind == "user" else f'\t(property "{kind}" "{s}"'
    return (f'{head} (at {f(x)} {f(y)} {f(rot)}) (layer "{layer}"){" (hide yes)" if hidden else ""} '
            f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)}))))')


class Pad:
    def __init__(self, num, kind, shape, x, y, w, h, drill=None, rot=0):
        self.num, self.kind, self.shape = num, kind, shape
        self.x, self.y, self.w, self.h, self.drill, self.rot = x, y, w, h, drill, rot

    def bbox(self, grow=0.0):
        w, h = (self.h, self.w) if self.rot % 180 == 90 else (self.w, self.h)
        return (self.x - w / 2 - grow, self.y - h / 2 - grow, self.x + w / 2 + grow, self.y + h / 2 + grow)

    def sexpr(self):
        at = f"(at {f(self.x)} {f(self.y)}{' ' + f(self.rot) if self.rot else ''})"
        if self.kind == "smd":
            return (f'\t(pad "{self.num}" smd {self.shape} {at} (size {f(self.w)} {f(self.h)}) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask"))')
        if self.kind == "np_thru_hole":
            return (f'\t(pad "" np_thru_hole circle {at} (size {f(self.w)} {f(self.h)}) '
                    f'(drill {f(self.drill)}) (layers "*.Cu" "*.Mask"))')
        if isinstance(self.drill, tuple):
            dr = f"(drill oval {f(self.drill[0])} {f(self.drill[1])})"
        else:
            dr = f"(drill {f(self.drill)})"
        rr = " (roundrect_rratio 0.25)" if self.shape == "roundrect" else ""
        return (f'\t(pad "{self.num}" thru_hole {self.shape} {at} (size {f(self.w)} {f(self.h)}) {dr} '
                f'(layers "*.Cu" "*.Mask"){rr} (remove_unused_layers no))')


def clip_segment(x1, y1, x2, y2, pads, clear=SILK_CLEAR, step=0.02):
    """把丝印线段中离焊盘 < clear 的部分剪掉，返回剩下的线段。"""
    boxes = [p.bbox(clear) for p in pads]
    n = max(1, int(math.hypot(x2 - x1, y2 - y1) / step))
    keep, segs, start = [], [], None
    for i in range(n + 1):
        t = i / n
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        ok = not any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes)
        keep.append((ok, x, y))
    prev = None
    for ok, x, y in keep:
        if ok and start is None:
            start = (x, y)
        if not ok and start is not None:
            segs.append((start, prev))
            start = None
        prev = (x, y)
    if start is not None:
        segs.append((start, prev))
    return [(a, b) for a, b in segs if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.15]


def silk_lines_clipped(coords, pads):
    out = []
    for x1, y1, x2, y2 in coords:
        for (a, b) in clip_segment(x1, y1, x2, y2, pads):
            out.append(line(a[0], a[1], b[0], b[1], "F.SilkS"))
    return out


def rect_coords(x1, y1, x2, y2):
    return [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]


def courtyard(boxes, margin=0.25):
    x1 = min(b[0] for b in boxes) - margin
    y1 = min(b[1] for b in boxes) - margin
    x2 = max(b[2] for b in boxes) + margin
    y2 = max(b[3] for b in boxes) + margin
    r = lambda v, up: (math.ceil(v * 20) if up else math.floor(v * 20)) / 20  # 0.05 网格
    return rect_lines(r(x1, False), r(y1, False), r(x2, True), r(y2, True), "F.CrtYd")


def model(path, offset=(0, 0, 0), rot=(0, 0, 0)):
    return (f'\t(model "{path}" (offset (xyz {" ".join(f(v) for v in offset)})) '
            f'(scale (xyz 1 1 1)) (rotate (xyz {" ".join(f(v) for v in rot)})))')


def write_fp(name, descr, tags, attr, items, pads, ref_at, val_at, models):
    body = [f'(footprint "{name}"', f"\t(version {VERSION})", '\t(generator "studenthw_gen")', '\t(layer "F.Cu")',
            f'\t(descr "{descr}")', f'\t(tags "{tags}")',
            text("REF**", ref_at[0], ref_at[1], "F.SilkS", kind="Reference", rot=ref_at[2] if len(ref_at) > 2 else 0),
            text(name, val_at[0], val_at[1], "F.Fab", kind="Value", rot=val_at[2] if len(val_at) > 2 else 0),
            text("${REFERENCE}", val_at[0], val_at[1] + 1.5, "F.Fab"),
            f"\t(attr {attr})"]
    body += items + [p.sexpr() for p in pads] + models + [")"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.kicad_mod").write_text("\n".join(body) + "\n", encoding="utf-8")
    print("写出", name)


def easy_model(src_name, rot=(0, 0, 0), offset=(0, 0, 0)):
    OUT3D.mkdir(parents=True, exist_ok=True)
    if (EASY3D / src_name).exists():          # build/ 缓存可能被删；库里已有的模型直接沿用
        shutil.copy2(EASY3D / src_name, OUT3D / src_name)
    elif not (OUT3D / src_name).exists():
        raise FileNotFoundError(f"缺 3D 模型 {src_name}：先运行 fetch_evidence.py 导出 EasyEDA 模型")
    return model("${STUDENTHW_DIR}/kicad/StudentHW.3dshapes/" + src_name, offset, rot)


# ---------- 官方封装改焊盘 ----------
def _blocks(text_):
    """footprint 的一级子块。"""
    out, depth, start, instr = [], 0, None, False
    for i, c in enumerate(text_):
        if c == '"' and text_[i - 1] != "\\":
            instr = not instr
        if instr:
            continue
        if c == "(":
            depth += 1
            if depth == 2:
                start = i
        elif c == ")":
            if depth == 2:
                out.append(text_[start:i + 1])
            depth -= 1
    return out


def _nums(s):
    return [float(x) for x in s.split()]


def parse_pad(b):
    m = re.match(r'\(pad "([^"]*)" (\w+) (\w+)', b)
    at = _nums(re.search(r"\(at ([-\d. ]+)\)", b).group(1))
    size = _nums(re.search(r"\(size ([-\d. ]+)\)", b).group(1))
    d = re.search(r"\(drill (oval )?([-\d. ]+)\)", b)
    drill = None
    if d:
        v = _nums(d.group(2))
        drill = (v[0], v[1]) if d.group(1) else v[0]
    return Pad(m.group(1), m.group(2), m.group(3), at[0], at[1], size[0], size[1], drill, at[2] if len(at) > 2 else 0)


def from_official(lib, src, name, descr, pad_fn, extra=(), crt_margin=0.25, model_override=None, drop_model=False):
    """model_override=(EasyEDA 模型文件名, 旋转, 偏移)：官方 3D 模型缺失时改用立创 EDA 导出的模型。"""
    t = (OFFICIAL / f"{lib}.pretty" / f"{src}.kicad_mod").read_text(encoding="utf-8")
    blocks = _blocks(t)
    pads = [pad_fn(parse_pad(b)) for b in blocks if b.startswith("(pad")]
    items, boxes, models, ref_at, val_at = [], [p.bbox() for p in pads], [], (0, -3), (0, 3)
    tags = re.search(r'\(tags "([^"]*)"\)', t)
    for b in blocks:
        flat = re.sub(r"\s+", " ", b)
        if b.startswith("(property \"Reference\""):
            ref_at = tuple(_nums(re.search(r"\(at ([-\d. ]+)\)", b).group(1))[:3])
        elif b.startswith("(property \"Value\""):
            val_at = tuple(_nums(re.search(r"\(at ([-\d. ]+)\)", b).group(1))[:3])
        elif b.startswith("(model"):
            models.append("\t" + flat)
        elif b.startswith(("(fp_line", "(fp_rect", "(fp_circle", "(fp_arc", "(fp_poly")):
            layer = re.search(r'\(layer "([^"]+)"\)', b).group(1)
            if layer == "F.CrtYd":
                continue
            if layer == "F.Fab":
                items.append("\t" + flat)
                xs = [float(v) for v in re.findall(r"\((?:start|end|center|mid|xy) ([-\d.]+) [-\d.]+\)", b)]
                ys = [float(v) for v in re.findall(r"\((?:start|end|center|mid|xy) [-\d.]+ ([-\d.]+)\)", b)]
                if b.startswith("(fp_circle"):
                    c = _nums(re.search(r"\(center ([-\d. ]+)\)", b).group(1))
                    e = _nums(re.search(r"\(end ([-\d. ]+)\)", b).group(1))
                    r = math.hypot(e[0] - c[0], e[1] - c[1])
                    boxes.append((c[0] - r, c[1] - r, c[0] + r, c[1] + r))
                elif xs:
                    boxes.append((min(xs), min(ys), max(xs), max(ys)))
            elif layer == "F.SilkS":
                if b.startswith("(fp_line"):
                    s = _nums(re.search(r"\(start ([-\d. ]+)\)", b).group(1))
                    e = _nums(re.search(r"\(end ([-\d. ]+)\)", b).group(1))
                    items += silk_lines_clipped([(s[0], s[1], e[0], e[1])], pads)
                elif b.startswith("(fp_rect"):
                    s = _nums(re.search(r"\(start ([-\d. ]+)\)", b).group(1))
                    e = _nums(re.search(r"\(end ([-\d. ]+)\)", b).group(1))
                    items += silk_lines_clipped(rect_coords(s[0], s[1], e[0], e[1]), pads)
                else:  # 圆、弧、多边形：只在不碰焊盘时保留
                    pts = [(float(a), float(c)) for a, c in re.findall(r"\((?:start|end|center|mid|xy) ([-\d.]+) ([-\d.]+)\)", b)]
                    if all(clip_segment(x, y, x, y + 1e-3, pads) for x, y in pts):
                        items.append("\t" + flat)
            else:
                items.append("\t" + flat)
        elif b.startswith("(fp_text"):
            items.append("\t" + flat)
    items += list(extra)
    items += courtyard(boxes, crt_margin)
    if model_override:
        models = [easy_model(model_override[0], rot=model_override[1], offset=model_override[2])]
    if drop_model:
        models = []
    attr = "through_hole" if any(p.kind == "thru_hole" for p in pads) else "smd"
    write_fp(name, descr, tags.group(1) if tags else name, attr, items, pads, ref_at, val_at, models)


def set_pad(w=None, h=None, drill=None):
    def fn(p):
        if p.kind == "thru_hole" and p.num:
            if w:
                p.w = w
            if h:
                p.h = h
            if drill:
                p.drill = drill
        return p
    return fn


# ---------- 各封装 ----------
def to220_vertical(name, labels, descr_pins):
    """TO-220 立装：孔 1.2（引脚最宽 0.97，L7805 0.88），焊盘 1.9×3.0 长圆，向上下加长补焊锡面积。"""
    def fn(p):
        p.drill, p.w, p.h = 1.2, 1.9, 3.0
        return p
    extra = [text(s, i * 2.54, 2.55, "F.SilkS", 0.8) for i, s in enumerate(labels)]
    from_official("Package_TO_SOT_THT", "TO-220-3_Vertical", name,
                  f"TO-220-3 立装，脚距 2.54，孔 1.2，焊盘 1.9x3.0；{descr_pins}；尺寸见 evidence/REG-00x", fn, extra)


def main():
    to220_vertical("TO-220-3_Vertical_GND-OUT-IN", ["GND", "OUT", "IN"], "1=GND/ADJ 2=OUT 3=IN（LD1117V33、LM1085-3.3）")
    to220_vertical("TO-220-3_Vertical_IN-GND-OUT", ["IN", "GND", "OUT"], "1=IN 2=GND 3=OUT（L7805）")
    from_official("Potentiometer_THT", "Potentiometer_Bourns_3296W_Vertical", "Potentiometer_Bourns_3296W_Vertical_Pad1.6",
                  "Bourns 3296W，引脚 Φ0.51±0.03，孔 0.8，焊盘加大到 1.6（官方 1.44 环宽 0.32）", set_pad(1.6, 1.6))
    from_official("Diode_THT", "D_DO-41_SOD81_P10.16mm_Horizontal", "D_DO-41_SOD81_P10.16mm_Horizontal_Hole1.2",
                  "DO-41 卧装 10.16，孔 1.2 焊盘 2.4，用于引脚 Φ0.8±0.15 的玻封稳压管（1N4733A LGE）", set_pad(2.4, 2.4, 1.2))

    from_official("Battery", "BatteryHolder_MYOUNG_BS-07-A1BJ001_CR2032", "BatteryHolder_MYOUNG_BS-07-A1BJ001_CR2032_Pad2.6",
                  "美阳 BS-07-A1BJ001 CR2032 直插电池座，孔 1.5（厂家图 2-Φ1.50），焊盘加大到 2.6；1=+，2=-", set_pad(2.6, 2.6),
                  model_override=("BAT-TH_BS-07-A1BJ001.wrl", (0, 0, 180), (10.4, 0, 0)))
    # 官方 3D 模型在本机 KiCad 库里缺失的两个：铜皮与官方完全相同，只换成立创 EDA 的 3D 模型
    from_official("Connector_BarrelJack", "BarrelJack_CUI_PJ-102AH_Horizontal", "BarrelJack_CUI_PJ-102AH_Horizontal",
                  "CUI PJ-102AH，焊盘与 KiCad 官方封装相同（与 CUI 推荐 PCB 图一致），3D 用立创 EDA 模型", lambda p: p,
                  model_override=("DC-IN-TH_PJ-102AH.wrl", (0, 0, 180), (2.35, -3.0, 0)))
    from_official("Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                  "HRO TYPE-C-31-M-12，焊盘与 KiCad 官方封装相同，3D 用立创 EDA 模型", lambda p: p,
                  model_override=("USB-C_SMD-TYPE-C-31-M-12_1.wrl", (0, 0, 180), (0, 1.5, 0)))

    # 第二批：数码管（引脚 Φ0.51，孔 0.8 已够；官方焊盘环宽偏小，加大）、Arduino Nano（本机缺官方 3D，去掉模型引用）
    from_official("Display_7Segment", "7SegmentLED_LTS6760_LTS6780", "7Seg_0.56in_1Digit_10P",
                  "0.56 寸 1 位数码管 10 脚，排距 15.24，脚距 2.54（志浩 FJ5161AH/BH 图纸），孔 0.8 焊盘 1.6×2.52", set_pad(1.6, 2.52, 0.8))
    from_official("Display_7Segment", "CA56-12SRWA", "7Seg_0.56in_4Digit_12P",
                  "0.56 寸 4 位数码管 12 脚，排距 15.24，脚距 2.54（志浩 FJ5461AH/BH 图纸），孔 0.8 焊盘 1.6", set_pad(1.6, 1.6, 0.8))
    from_official("Module", "Arduino_Nano", "Arduino_Nano",
                  "Arduino Nano（含 CH340 兼容版），2×15 2.54，排距 15.24；与 KiCad 官方封装相同，去掉本机缺失的 3D 引用",
                  lambda p: p, drop_model=True)

    # DC-005（XKB DC-005-5A-2.0 推荐 PCB 图）。坐标系同 EasyEDA 原封装：插口朝 -X。
    # 厂家图：前端面到 2 脚 7.70、到 1 脚 13.60、到 3 脚 10.60（3 脚偏离轴线 4.70）；三孔 1.0x3.5 槽。
    ax = -2.35                     # 插头轴线 y
    front = -2.95 - 7.70           # 前端面 x
    p1 = Pad("1", "thru_hole", "rect", 2.95, ax, 2.0, 4.5, (1.0, 3.5))
    p2 = Pad("2", "thru_hole", "oval", -2.95, ax, 2.0, 4.5, (1.0, 3.5))
    p3 = Pad("3", "thru_hole", "oval", front + 10.60, ax + 4.70, 4.5, 2.0, (3.5, 1.0))
    pads = [p1, p2, p3]
    bx1, bx2, by1, by2 = front, front + 14.0, ax - 4.5, ax + 4.5
    items = rect_lines(bx1, by1, bx2, by2, "F.Fab")
    items += silk_lines_clipped(rect_coords(bx1 - 0.11, by1 - 0.11, bx2 + 0.11, by2 + 0.11), pads)
    # 板边对齐线和插口方向箭头
    items += [line(front, by1 - 2.5, front, by2 + 2.5, "F.Fab"), line(front, by1 - 2.5, front, by2 + 2.5, "F.SilkS"),
              text("EDGE", front + 1.6, by2 + 1.6, "F.SilkS", 0.8),
              line(front + 6, ax, front + 1.5, ax, "F.SilkS"), line(front + 1.5, ax, front + 2.7, ax - 0.8, "F.SilkS"),
              line(front + 1.5, ax, front + 2.7, ax + 0.8, "F.SilkS"),
              text("PLUG", front + 4.2, ax - 1.3, "F.Fab", 0.8), text("+", p1.x + 1.9, p1.y - 3.0, "F.SilkS", 1.0)]
    items += courtyard([(bx1, by1 - 2.5, bx2, by2 + 2.5)] + [p.bbox() for p in pads])
    write_fp("PowerJack_DC-005_XKB_5A_Horizontal", "XKB DC-005-5A-2.0 卧式电源座，按厂家推荐 PCB 图；插口朝 -X，前端面与板边对齐（EDGE 线）",
             "DC-005 barrel jack 5.5x2.1", "through_hole", items, pads, (front + 7, by1 - 1.6), (front + 7, by2 + 3.5),
             [model("${KICAD10_3DMODEL_DIR}/Connector_BarrelJack.3dshapes/BarrelJack_Horizontal.step", (2.95, -ax, 0))])
    # ↑ 官方通用 DC 座模型：官方封装 1 脚在原点、2 脚在 -6、3 脚在 (-3, 4.7)，与本封装只差平移（立创模型与厂家图对不上，未用）

    # Type-C 6P 仅供电（首韩 TYPE-C 6P，C456012）。坐标系同 EasyEDA 原封装，插口朝 +Y。
    ty = -1.78                      # 后排固定脚
    tf = ty + 3.80                  # 前排固定脚
    sig = [("B12", -2.7, 0.8), ("B9", -1.5, 0.7), ("A5", -0.5, 0.7), ("B5", 0.5, 0.7), ("A9", 1.5, 0.7), ("A12", 2.7, 0.8)]
    pads = [Pad(n, "smd", "rect", x, ty - 0.15, w, 1.2) for n, x, w in sig]   # 厂家 1.0 长，向后加长 0.2 便于烙铁
    pads += [Pad("SH", "thru_hole", "oval", sx, sy, 1.2, 2.0, (0.6, 1.4)) for sx in (-4.32, 4.32) for sy in (ty, tf)]
    edge = tf + 2.60
    bx1, bx2, by1, by2 = -4.47, 4.47, edge - 6.80, edge
    items = rect_lines(bx1, by1, bx2, by2, "F.Fab")
    items += silk_lines_clipped(rect_coords(bx1 - 0.11, by1 - 0.11, bx2 + 0.11, by2 + 0.11), pads)
    items += [line(-6, edge, 6, edge, "F.Fab"), line(-6, edge, 6, edge, "F.SilkS"), text("EDGE", 0, edge + 1.0, "F.SilkS", 0.8),
              text("VBUS", 1.5, ty - 1.6, "F.Fab", 0.5), text("CC", 0, ty - 2.4, "F.Fab", 0.5)]
    items += courtyard([(bx1, by1, bx2, edge + 0.5)] + [p.bbox() for p in pads])
    write_fp("USB_C_Receptacle_ShouHan_TYPE-C-6P_PowerOnly", "首韩 TYPE-C 6P 仅供电母座：6 个贴片信号脚 + 4 个直插固定脚，按厂家推荐 PCB 图；插口朝 +Y，前端与 EDGE 线对齐",
             "USB-C 6P power only", "through_hole", items, pads, (0, by1 - 1.6), (0, edge + 2.4),
             [easy_model("TYPE-C-SMD_6P-L8.9-W6.8-H3.2-P1.00.wrl", rot=(0, 0, 180))])

    # 无源蜂鸣器 Φ12x8.5 脚距 6.5（锋鸣 YS-MBZ12085C05R42）
    def buzzer(name, d, h, pitch, lead, mdl, descr):
        pads = [Pad("1", "thru_hole", "rect", -pitch / 2, 0, 2.0, 2.0, 1.0), Pad("2", "thru_hole", "circle", pitch / 2, 0, 2.0, 2.0, 1.0)]
        items = [circle(0, 0, d / 2, "F.Fab"), circle(0, 0, d / 2 + 0.11, "F.SilkS"),
                 text("+", -pitch / 2, -2.0, "F.SilkS", 1.2)]
        items += courtyard([(-d / 2, -d / 2, d / 2, d / 2)] + [p.bbox() for p in pads])
        write_fp(name, descr, "buzzer", "through_hole", items, pads, (0, -d / 2 - 1.2), (0, d / 2 + 1.2), [easy_model(mdl)])
    buzzer("Buzzer_D12.0mm_H8.5mm_P6.50mm", 12.0, 8.5, 6.5, 0.6, "BUZ-TH_D12.0-H8.5-P6.5.wrl",
           "无源电磁蜂鸣器 Φ12x8.5，脚距 6.5±0.2，引脚 Φ0.6（YS-MBZ12085C05R42）")
    buzzer("Buzzer_D9.0mm_H5.5mm_P5.00mm", 9.0, 5.5, 5.0, 0.6, "BUZ-TH_D9.0-H5.5-P5.0.wrl",
           "有源蜂鸣器 Φ9x5.5，脚距 5.0±0.2，引脚 Φ0.6±0.05，长脚为 +（华能 HNB09A05）")

    # 18650 单节电池盒（美阳 BH-18650-A1AJ005）：脚距 70.00±3，长圆槽孔吸收公差
    pads = [Pad("1", "thru_hole", "rect", 35.0, 0, 5.0, 2.4, (3.8, 1.2)), Pad("2", "thru_hole", "oval", -35.0, 0, 5.0, 2.4, (3.8, 1.2))]
    items = rect_lines(-37.75, -10.5, 37.75, 10.5, "F.Fab")
    items += silk_lines_clipped(rect_coords(-37.86, -10.61, 37.86, 10.61), pads)
    items += [text("+", 31.0, 0, "F.SilkS", 2.0), text("-", -31.0, 0, "F.SilkS", 2.0)]
    items += courtyard([(-37.75, -10.5, 37.75, 10.5)] + [p.bbox() for p in pads])
    write_fp("BatteryHolder_MYOUNG_BH-18650-A1AJ005", "美阳 BH-18650-A1AJ005 单节 18650 电池盒，脚距 70.00±3，槽孔 1.2x3.8 吸收公差；1=+（无弹簧端），2=-（弹簧端）",
             "18650 battery holder", "through_hole", items, pads, (0, -12), (0, 12),
             [easy_model("BAT-TH_BH-18650-A1AJ005.wrl")])


if __name__ == "__main__":
    main()
