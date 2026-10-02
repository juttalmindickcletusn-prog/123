"""生成 reports/兼容性速查.md（第 5 节）：I2C 地址与冲突、I2C 上拉、电平兼容、主控引脚约束、电流预算。
数据只读 src/electrical.yaml 和 src/mcu_pins.yaml（每个值的出处写在那里），本脚本不添加任何数值。
同时检查：模块和芯片类条目（主控、显示、传感、执行、通信、电源、稳压、工具、光耦）都要有电气数据，主控板都要有逐脚表。
用法：python tools/build_compat.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compat_lib as cl  # noqa: E402
import market_lib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "兼容性速查.md"
NEED_PREFIX = ("MCU", "DSP", "SEN", "ACT", "COM", "PMD", "REG", "TOOL", "OPT")


def fmt_i(d) -> str:
    if not d or d.get("value") is None:
        return "未核"
    return f"{d['value']:g}（{d.get('cond', '')}）"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = {r["id"]: r for r in market_lib.parts_rows()}
    E, M = cl.electrical(), cl.mcu_pins()
    problems = []
    for pid in rows:
        if pid.split("-")[0] in NEED_PREFIX and pid not in E:
            problems.append(f"{pid} 缺电气数据（src/electrical.yaml）")
        if pid.startswith("MCU") and pid not in M:
            problems.append(f"{pid} 缺逐脚表（src/mcu_pins.yaml）")
    for pid in list(E) + list(M):
        if pid not in rows:
            problems.append(f"{pid} 在电气/引脚数据里，但 parts.csv 没有这个条目")
    name = lambda i: rows[i]["name"] if i in rows else i

    L = ["# 兼容性速查", "",
         "由 `tools/build_compat.py` 从 `src/electrical.yaml`、`src/mcu_pins.yaml` 生成，不要手改。每个数值的出处见这两个文件的 `src_ref`/`sources`；",
         "写\"未核\"的是云端没有拿到可靠出处的值，不估。画原理图前用 `python tools/check_project.py projects/项目.yaml` 自动查一遍。", ""]

    # 1. I2C 地址
    i2c = {k: v for k, v in E.items() if v.get("i2c_addr")}
    L += ["## 1. I2C 地址总表", "", "| 编号 | 名称 | 默认地址 | 可改成 / 怎么改 |", "|---|---|---|---|"]
    for k, v in sorted(i2c.items()):
        L.append(f"| {k} | {name(k)} | {'、'.join(v['i2c_addr'])} | {v.get('i2c_addr_alt', '—')} |")
    L += ["", "### 地址冲突表（同一路 I2C 上不能同时用，除非按\"解决办法\"改）", "",
          "| 冲突地址 | 条目 A | 条目 B | 解决办法 |", "|---|---|---|---|"]
    n_conf = 0
    groups: dict[frozenset, list[str]] = {}
    for k, v in sorted(i2c.items()):
        groups.setdefault(frozenset(cl.addr_int(x) for x in v["i2c_addr"]), []).append(k)
    for addrs, ids in groups.items():       # 同型器件（地址完全相同的一组，如各种 I2C OLED）
        if len(ids) > 1:
            n_conf += 1
            v = i2c[ids[0]]
            fix = cl.i2c_fix(v, min(addrs), set(addrs))
            how = f"同一路只能有一块用默认地址，另一块改 {'、'.join(hex(f) for f in fix)}（{v.get('i2c_addr_alt', '')}）" if fix else "地址不可改：分两路 I2C 或只用一个"
            L.append(f"| {'、'.join(hex(x) for x in sorted(addrs))} | 同型器件任意两个：{'、'.join(ids)} | — | {how} |")
    for a, b in itertools.combinations(sorted(i2c), 2):
        da = {cl.addr_int(x) for x in i2c[a]["i2c_addr"]}
        db = {cl.addr_int(x) for x in i2c[b]["i2c_addr"]}
        both = da & db
        if not both or da == db:
            continue
        n_conf += 1
        fixes = []
        for x, other in ((a, db), (b, da)):
            for addr in sorted(both):
                free = cl.i2c_fix(i2c[x], addr, da | db)
                if free:
                    fixes.append(f"把 {x} 的 {hex(addr)} 改到 {'、'.join(hex(f) for f in free[:3])}（{i2c[x].get('i2c_addr_alt', '')}）")
        fixes.append("或分到两路 I2C（ESP32/STM32 都有第二路硬件 I2C）" if fixes else "两边地址都不可改：分到两路 I2C 或换型号")
        L.append(f"| {'、'.join(hex(x) for x in sorted(both))} | {a} {name(a)} | {b} {name(b)} | {'；'.join(fixes)} |")
    L += ["", f"共 {n_conf} 组默认地址冲突（同型器件算一组）。典型情况：MPU6050（0x68）与 DS3231（0x68）；MAX30102（0x57）与 ZS-042 板上 AT24C32（0x57）；"
          "PCF8574A 转接板跳线全短接（0x38）与 AHT20（0x38，不可改）。", ""]

    # 2. 上拉
    L += ["## 2. I2C 上拉", "",
          "**计算方法**：同一路总线上所有模块的上拉电阻是并联的，总阻值 R = 1 / Σ(1/Ri)。I2C 器件下拉能力按 3mA（VOL ≤0.4V）算，",
          "R 不能小于 (V上拉 − 0.4V) / 3mA：3.3V 时约 967Ω，5V 时约 1533Ω。小于这个值就拆掉多余模块上的上拉电阻（一般是 4.7k/10k 的 0603/0805 电阻）。", "",
          "**上拉到 5V 的风险**：模块 5V 供电且上拉接 VCC 时，SDA/SCL 高电平是 5V；ESP32、Pico 的 GPIO 不耐 5V，STM32 要用 FT 脚。",
          "处理：模块改 3.3V 供电（模块允许时）、拆掉模块上拉另在 3.3V 上加、或加 I2C 电平转换板。", "",
          "| 编号 | 名称 | 板上上拉 | 上拉到 | 说明 |", "|---|---|---|---|---|"]
    for k, v in sorted(i2c.items()):
        p = v.get("i2c_pullup") or {}
        ohm = f"{p['ohm'] / 1000:g}k" if p.get("ohm") else "未核"
        to = {"vcc": "模块 VCC（随供电）", "3.3": "板载 3.3V"}.get(str(p.get("to")), "未核")
        L.append(f"| {k} | {name(k)} | {ohm} | {to} | {p.get('note', '')} |")
    L.append("")

    # 3. 电平
    L += ["## 3. 电平兼容表", "",
          "\"接 3.3V 主控\"指 ESP32、ESP8266、Pico、STM32 非 FT 脚；\"5V 主控驱动\"指 Arduino Nano、STC89C52。", "",
          "| 编号 | 名称 | 供电 | 输出电平 | 接 3.3V 主控 | 5V 主控驱动它 |", "|---|---|---|---|---|---|"]
    for k, v in sorted(E.items()):
        if k.startswith(("MCU", "REG", "PMD", "TOOL", "BZ", "Q-", "OPT")):
            continue
        a, an = cl.direct_to_3v3(v)
        b, bn = cl.direct_from_5v(v)
        outs = "、".join(f"{p}={'随供电' if s == 'vcc' else ('未核' if s is None else f'{float(s):g}V')}" for p, s in (v.get("outputs") or {}).items()) or "—"
        L.append(f"| {k} | {name(k)} | {v.get('vcc_range', '')} | {outs} | **{a}**：{an} | **{b}**：{bn} |")
    L += ["", "例：HC-SR04（SEN-018）只能 5V 供电，Echo 输出 5V，接 ESP32 必须用电阻分压（如 1k/2k）或换 HC-SR04P 用 3.3V 供电。", ""]

    # 4. 主控引脚
    L += ["## 4. 主控引脚约束", ""]
    for mid, b in M.items():
        L += [f"### {mid} {b['board']}（{b['chip']}）", "",
              f"- 耐 5V：{b['five_v_tolerant']}", f"- ADC：{b.get('adc_range', '')}", f"- 默认串口：{b.get('uart_log', '')}"]
        if b.get("note"):
            L.append(f"- {b['note']}")
        L.append(f"- 出处：{'；'.join(b['sources'])}")
        L += ["", "| 排针脚 | GPIO | 结论 | 限制 | ADC | 耐 5V |", "|---|---|---|---|---|---|"]
        for g, p in b["pins"].items():
            L.append(f"| {p['header']} | {g} | {p['use']} | {p.get('note', '')} | {p.get('adc', '')} | {'是' if p.get('five_v_tolerant') else '否'} |")
        L += ["", f"放心用的脚：{'、'.join(b['safe']) or '无'}", ""]

    # 5. 电流
    L += ["## 5. 电流预算参考", "", "按规范：峰值相加后不超过供电能力的 70%（留 30% 余量）。", "",
          "### 供电能力", "", "| 来源 | 能力 mA | 70% 可用 mA | 说明 |", "|---|---|---|---|",
          "| 电脑 USB 2.0 口 | 500 | 350 | USB 2.0 规范每口 500mA |"]
    for k, v in sorted(E.items()):
        cap = v.get("supply_capacity_ma")
        if cap is None:
            continue
        val = cap.get("value")
        L.append(f"| {k} {name(k)} | {val if val is not None else '未核'} | {round(val * 0.7) if val else '—'} | {cap.get('note', '')} |")
    L += ["", "### 各模块电流", "", "| 编号 | 名称 | 典型 mA | 峰值 mA |", "|---|---|---|---|"]
    for k, v in sorted(E.items()):
        if v.get("supply_capacity_ma") is not None and not k.startswith("MCU"):
            continue
        L.append(f"| {k} | {name(k)} | {fmt_i(v.get('i_typ_ma'))} | {fmt_i(v.get('i_peak_ma'))} |")
    L.append("")
    if problems:
        L += ["## 数据缺口", ""] + [f"- {p}" for p in problems] + [""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    for p in problems:
        print("✗", p)
    print(f"兼容性速查：I2C 条目 {len(i2c)}，默认地址冲突 {n_conf} 组，主控 {len(M)} 块，缺口 {len(problems)} 处 → {OUT.relative_to(ROOT)}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
