"""画原理图前的项目检查（第 5 节）：python tools/check_project.py projects/项目.yaml

查：
  1. 条目存在（库外件写 ext: true 时只提醒）；主控在 src/mcu_pins.yaml 里；
  2. I2C 地址冲突（按 i2c_bus 分总线；条目可用 i2c_addr 覆盖为实际设置的地址）；
  3. 电平：模块输出（electrical.yaml 的 outputs）接到不耐 5V 的主控脚；5V 主控驱动只能 3.3V 的模块；
  4. 引脚：用到"别用"的脚（Flash/PSRAM、USB、SWD、板上已占用）报错；用到"慎用"的脚（启动脚、默认串口、只能输入等）提醒；
     只能输入的脚接了需要主控输出的信号报错；同一个脚分给两个信号报错（同一总线的 SDA/SCL/SCK/MOSI/MISO 可以共用）；
  5. 电流：各条目典型值、峰值（×数量）分别相加，超过供电能力的 70% 报错；电流未核的条目单独列出；
  6. I2C 上拉：同一总线上各模块上拉并联后的阻值、上拉电压；上拉到 5V 而主控脚不耐 5V 报错；
  7. 提醒：贴片件、C 级件（要到货实测）、库外件。
有错误时退出码 1。结果同时写 projects/<项目名>/检查结果.md。

项目文件格式见 README（与 project_cost.py 共用）。条目可选字段：
  vcc: 3.3 / 5            给模块的供电电压（不写时按模块允许的最低档：最低供电 >3.6V 按 5V，否则按 3.3V，并提醒）
  i2c_bus: 0              所在 I2C 总线编号（不写时按 SDA 接到的主控脚自动分组，都没有就算第 0 路）
  i2c_addr: [0x69]        实际设置的地址（改过 AD0/跳线时写）
  rail: 3V3 / 5V          从哪路电源取电（不写按 vcc）
pins 写法："条目编号.模块脚名: 主控脚"，如 "SEN-018.ECHO: GPIO5"；同一编号多个时用 "SEN-018#2.ECHO"。
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compat_lib as cl  # noqa: E402
import market_lib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def load_project(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def item_key(it: dict, idx: int, counts: dict) -> str:
    n = counts.get(it["id"], 0)
    return it["id"] if n <= 1 else f"{it['id']}#{idx}"


def check(prj: dict) -> tuple[list[str], list[str], list[str]]:
    rows = {r["id"]: r for r in market_lib.parts_rows()}
    E, M = cl.electrical(), cl.mcu_pins()
    errs, warns, info = [], [], []
    items = prj.get("items") or []
    mcu_id = prj.get("mcu")
    board = M.get(mcu_id)
    if mcu_id not in rows:
        errs.append(f"主控 {mcu_id} 不在库里")
    if board is None:
        errs.append(f"主控 {mcu_id} 没有逐脚表（src/mcu_pins.yaml），引脚和电平检查做不了")
    mcu_5v = bool(board) and str(board.get("five_v_tolerant", "")).startswith("是")

    # 条目实例
    counts: dict[str, int] = {}
    for it in items:
        counts[it["id"]] = counts.get(it["id"], 0) + 1
    seen: dict[str, int] = {}
    inst = {}
    for it in items:
        seen[it["id"]] = seen.get(it["id"], 0) + 1
        key = item_key(it, seen[it["id"]], counts)
        inst[key] = it
        pid = it["id"]
        if pid not in rows:
            msg = "库外件（BOM 里标“库外件”）" if it.get("ext") else "不在库里（库外件要写 ext: true）"
            (warns if it.get("ext") else errs).append(f"{key}：{msg}")
            continue
        r = rows[pid]
        if "贴片" in r.get("mount", ""):
            warns.append(f"{key}：贴片件（用户只焊直插）")
        if r["level"] == "C":
            info.append(f"{key} {r['name']}：C 级，到货后按实物核对针序和尺寸")
        e = E.get(pid)
        if e and "vcc" not in it and e.get("vcc_min") is not None and pid != mcu_id:
            it["_vcc"] = 5.0 if e["vcc_min"] > cl.V_SAFE_3V3 else 3.3
            if e.get("vcc_max") and e["vcc_max"] >= 4.5 and e["vcc_min"] <= cl.V_SAFE_3V3:
                warns.append(f"{key}：没写 vcc，按 {it['_vcc']:g}V 供电检查（该模块 3.3V/5V 都能用，写明实际供电）")
        else:
            it["_vcc"] = it.get("vcc")

    # 引脚
    used: dict[str, list[str]] = {}
    pins = prj.get("pins") or {}
    for sig, mpin in pins.items():
        key, _, mod_pin = sig.partition(".")
        it = inst.get(key)
        if it is None:
            errs.append(f"pins：{sig} 的条目 {key} 不在 items 里")
            continue
        used.setdefault(str(mpin), []).append(sig)
        if not board:
            continue
        p = board["pins"].get(str(mpin))
        if p is None:
            errs.append(f"{sig} → {mpin}：{mcu_id} 排针上没有这个脚")
            continue
        flags = set(p.get("flags", []))
        if p["use"] == "别用":
            errs.append(f"{sig} → {mpin}：别用（{p.get('note', '')}）")
        elif p["use"] == "慎用":
            warns.append(f"{sig} → {mpin}：慎用（{p.get('note', '')}）")
        e = E.get(it["id"], {})
        outs = e.get("outputs") or {}
        if "input_only" in flags and mod_pin not in outs and mod_pin not in cl.BUS_SIGNALS:
            errs.append(f"{sig} → {mpin}：该脚只能输入，但 {mod_pin} 需要主控输出")
        if mod_pin in outs:
            lv = cl.out_level(outs[mod_pin], it.get("_vcc"))
            if lv is None:
                warns.append(f"{sig}：模块输出电平未核")
            elif lv > cl.V_SAFE_3V3 and not p.get("five_v_tolerant"):
                errs.append(f"{sig} → {mpin}：模块输出 {lv:g}V，{mpin} 不耐 5V（加分压/电平转换，或模块改 3.3V 供电）")
        elif mcu_5v and e and e.get("vcc_max") is not None and e["vcc_max"] <= cl.V_SAFE_3V3 \
                and not str(e.get("io_5v_tolerant", "")).startswith("是") and mod_pin not in ("GND", "VCC", "3V3", "VIN"):
            errs.append(f"{sig} → {mpin}：5V 主控驱动只能 {e['vcc_max']:g}V 的模块输入，要电平转换")
        if e.get("inputs", {}).get(mod_pin) and not mcu_5v:
            warns.append(f"{sig}：{e['inputs'][mod_pin]}")
        if "adc2" in flags and "Wi-Fi" in (E.get(mcu_id, {}).get("interface") or []) and mod_pin in ("AO", "AOUT", "OUT", "SIG", "OUTPUT"):
            warns.append(f"{sig} → {mpin}：ADC2 通道，开 Wi-Fi 时读不了，模拟量改接 ADC1")
    for mpin, sigs in used.items():
        if len(sigs) > 1:
            names = {s.partition(".")[2] for s in sigs}
            if not names <= cl.BUS_SIGNALS or len(names) > 1:
                errs.append(f"{mpin} 同时分给了 {'、'.join(sigs)}")

    # I2C 地址与上拉
    buses: dict[str, list[str]] = {}
    sda_of = {k.partition(".")[0]: str(v) for k, v in pins.items() if k.endswith(".SDA")}
    for key, it in inst.items():
        e = E.get(it["id"], {})
        if not e.get("i2c_addr"):
            continue
        bus = str(it.get("i2c_bus", sda_of.get(key, "0")))
        buses.setdefault(bus, []).append(key)
    for bus, keys in buses.items():
        owner: dict[int, str] = {}
        for key in keys:
            it, e = inst[key], E[inst[key]["id"]]
            addrs = it.get("i2c_addr") or e["i2c_addr"]
            opts = {cl.addr_int(x) for x in e.get("i2c_addr_options", e["i2c_addr"])}
            for a in addrs:
                ai = cl.addr_int(a) if isinstance(a, str) else int(a)
                if ai not in opts:
                    errs.append(f"{key}：地址 {hex(ai)} 不在该模块可设地址 {sorted(hex(o) for o in opts)} 里")
                if ai in owner:
                    tips = []
                    for k2 in (key, owner[ai]):
                        e2 = E[inst[k2]["id"]]
                        free = cl.i2c_fix(e2, ai, set(owner) | {ai})
                        if free:
                            tips.append(f"把 {k2} 改到 {'、'.join(hex(f) for f in free[:3])}（{e2.get('i2c_addr_alt', '')}），并在 items 里写 i2c_addr")
                    tips.append("或分两路 I2C" if tips else "两边都不能改：分两路 I2C 或换型号")
                    errs.append(f"I2C 总线 {bus}：{hex(ai)} 冲突（{owner[ai]} 与 {key}）→ {'；'.join(tips)}")
                else:
                    owner[ai] = key
        # 上拉
        rs, volts, unknown = [], [], []
        for key in keys:
            it, e = inst[key], E[inst[key]["id"]]
            p = e.get("i2c_pullup") or {}
            if not p.get("ohm") or p.get("to") is None:
                unknown.append(key)
            if p.get("ohm"):
                rs.append(p["ohm"])
            to = p.get("to")
            if to == "vcc" and it.get("_vcc"):
                volts.append((key, float(it["_vcc"])))
            elif to not in (None, "vcc"):
                volts.append((key, float(to)))
        rp = cl.parallel(rs)
        if rp:
            vmax = max([v for _, v in volts] or [3.3])
            line = f"I2C 总线 {bus}：已知上拉并联 {rp:.0f}Ω（{len(rs)} 个），上拉电压最高 {vmax:g}V"
            if rp < cl.r_min(vmax):
                warns.append(line + f"，低于 {cl.r_min(vmax):.0f}Ω（3mA 灌电流限值），拆掉多余模块的上拉")
            else:
                info.append(line)
        if unknown:
            warns.append(f"I2C 总线 {bus}：{'、'.join(unknown)} 的板上上拉阻值或上拉电压未核，到货看板上电阻")
        if board:
            sda_pins = {str(pins.get(f"{k}.SDA")) for k in keys if pins.get(f"{k}.SDA")}
            for key, v in volts:
                if v > cl.V_SAFE_3V3:
                    for sp in sda_pins:
                        bp = board["pins"].get(sp)
                        if bp and not bp.get("five_v_tolerant"):
                            errs.append(f"I2C 总线 {bus}：{key} 上拉到 {v:g}V，主控 {sp} 不耐 5V（模块改 3.3V 供电或加电平转换）")

    # 电流
    pw = prj.get("power") or {}
    cap = pw.get("capacity_ma")
    typ = peak = 0.0
    unk = []
    for key, it in inst.items():
        e = E.get(it["id"])
        q = it.get("qty", 1)
        if e is None:
            if it["id"].split("-")[0] in ("MCU", "DSP", "SEN", "ACT", "COM", "BZ", "LED") or it.get("ext"):
                unk.append(key)
            continue
        t = (e.get("i_typ_ma") or {}).get("value")
        pk = (e.get("i_peak_ma") or {}).get("value")
        if t is None and pk is None:
            unk.append(key)
            continue
        typ += (t if t is not None else pk) * q
        peak += (pk if pk is not None else t) * q
    if cap:
        lim = cap * 0.7
        line = f"电流：典型合计 {typ:g}mA，峰值合计 {peak:g}mA；{pw.get('source', '电源')} {cap}mA 的 70% = {lim:g}mA"
        if peak > lim or typ > lim:
            errs.append(line + " → 超过 70%，换更大电源或分路供电")
        else:
            info.append(line)
    else:
        warns.append("power.capacity_ma 没写，电流预算没法查")
    if unk:
        warns.append("电流未核（没算进合计）：" + "、".join(unk))
    return errs, warns, info


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    path = Path(sys.argv[1])
    prj = load_project(path)
    errs, warns, info = check(prj)
    name = prj.get("name") or path.stem
    out = path.parent / path.stem / "检查结果.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    L = [f"# {name}：画图前检查", "", f"主控 {prj.get('mcu')}；错误 {len(errs)}，提醒 {len(warns)}。", ""]
    for title, xs in (("错误（必须改）", errs), ("提醒", warns), ("信息", info)):
        L += [f"## {title}", ""] + ([f"- {x}" for x in xs] or ["- 无"]) + [""]
    out.write_text("\n".join(L), encoding="utf-8")
    for x in errs:
        print("✗", x)
    for x in warns:
        print("!", x)
    try:
        shown = out.resolve().relative_to(ROOT)
    except ValueError:
        shown = out
    print(f"{name}：错误 {len(errs)}，提醒 {len(warns)} → {shown}")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
