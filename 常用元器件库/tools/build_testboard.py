"""把 parts.csv 引用的全部封装摆到一块测试板上（用 KiCad 自带 Python 运行），之后用 kicad-cli 跑 DRC、渲染。

用法：D:/kicad/bin/python.exe tools/build_testboard.py
输出：build/testboard/testboard.kicad_pcb
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "testboard"
OFFICIAL = paths.FP_OFF
LOCAL = ROOT / "kicad" / "StudentHW.pretty"
MM = 1_000_000
GAP, WIDTH = 4.0, 230.0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader((ROOT / "parts.csv").open(encoding="utf-8-sig")))
    refs: dict[str, list[str]] = {}
    for r in rows:
        if ":" in r["kicad_footprint"]:
            refs.setdefault(r["kicad_footprint"], []).append(r["id"])
    board = pcbnew.BOARD()
    fps = []
    for ref, ids in refs.items():
        lib, name = ref.split(":", 1)
        fp = pcbnew.FootprintLoad(str(LOCAL if lib == "StudentHW" else OFFICIAL / f"{lib}.pretty"), name)
        fp.SetReference(ids[0])
        fp.SetValue(name)
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
        fps.append((bb.GetHeight(), fp, bb))
    fps.sort(key=lambda t: -t[0])
    x = y = 5.0
    row_h = 0.0
    for _, fp, bb in fps:
        w, h = bb.GetWidth() / MM, bb.GetHeight() / MM
        if x + w > WIDTH:
            x, y, row_h = 5.0, y + row_h + GAP, 0.0
        # 把 courtyard 左上角放到 (x, y)
        dx = x * MM - bb.GetLeft()
        dy = y * MM - bb.GetTop()
        fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x + int(dx), fp.GetPosition().y + int(dy)))
        board.Add(fp)
        # 同一位置叠放的焊盘（如 Type-C 的 A1/B12）实际同属一个网络，测试板上给它们同一个网络
        groups: dict[tuple, list] = {}
        for pad in fp.Pads():
            groups.setdefault((pad.GetPosition().x, pad.GetPosition().y), []).append(pad)
        for k, pads in groups.items():
            if len({p.GetNumber() for p in pads}) > 1:
                net = pcbnew.NETINFO_ITEM(board, f"{fp.GetReference()}_" + "_".join(sorted(p.GetNumber() for p in pads)))
                board.Add(net)
                for p in pads:
                    p.SetNet(net)
        x += w + GAP
        row_h = max(row_h, h)
    H = y + row_h + 5.0
    for (x1, y1, x2, y2) in [(0, 0, WIDTH + 5, 0), (WIDTH + 5, 0, WIDTH + 5, H), (WIDTH + 5, H, 0, H), (0, H, 0, 0)]:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(int(x1 * MM), int(y1 * MM)))
        s.SetEnd(pcbnew.VECTOR2I(int(x2 * MM), int(y2 * MM)))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(int(0.1 * MM))
        board.Add(s)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "testboard.kicad_pcb"
    board.Save(str(path))
    print(f"测试板：{len(fps)} 个封装（{len(rows)} 条目），板子 {WIDTH + 5:.0f}×{H:.0f} mm → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
