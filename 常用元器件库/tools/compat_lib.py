"""兼容性数据（src/electrical.yaml、src/mcu_pins.yaml）的读取和通用计算，build_compat.py 与 check_project.py 共用。"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
I2C_SINK_MA = 3.0          # I2C 标准模式/快速模式下拉能力 3mA（I2C 规范，VOL ≤0.4V）
V_SAFE_3V3 = 3.6           # 3.3V 器件输入一般允许到 VDD+0.3，超过按 5V 信号处理
BUS_SIGNALS = {"SDA", "SCL", "SCK", "MOSI", "MISO", "SDI_MOSI", "SDO_MISO", "D0_SCK", "D1_MOSI", "SDA(I2C)"}


def load(name: str) -> dict:
    p = ROOT / "src" / name
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def electrical() -> dict:
    return load("electrical.yaml")


def mcu_pins() -> dict:
    return load("mcu_pins.yaml")


def addr_int(a) -> int:
    return int(str(a), 16)


def r_min(v_pull: float) -> float:
    """I2C 上拉并联后的最小阻值：(V − 0.4V) / 3mA。"""
    return (v_pull - 0.4) / (I2C_SINK_MA / 1000)


def parallel(ohms: list[float]) -> float | None:
    ohms = [o for o in ohms if o]
    return 1 / sum(1 / o for o in ohms) if ohms else None


def out_level(spec, vcc: float | None):
    """模块输出电平：'vcc' → 供电电压；数值 → 本身；None → 未核/开漏。"""
    if spec == "vcc":
        return vcc
    return spec


def direct_to_3v3(e: dict) -> tuple[str, str]:
    """模块输出接 3.3V 主控（不耐 5V）能否直连。返回（结论，说明）。"""
    outs = e.get("outputs") or {}
    if not outs:
        return "直连", "模块不向主控输出电平（只有输入或 I2C/开漏总线另看上拉）"
    vmin = e.get("vcc_min")
    worst, unknown = [], []
    for pin, spec in outs.items():
        if spec is None:
            unknown.append(pin)
        elif spec == "vcc":
            if vmin is not None and vmin > V_SAFE_3V3:
                worst.append(f"{pin} 输出随供电（最低 {vmin:g}V）")
        elif float(spec) > V_SAFE_3V3:
            worst.append(f"{pin} 输出 {float(spec):g}V")
    if worst:
        return "需分压或电平转换", "；".join(worst)
    if any(spec == "vcc" for spec in outs.values()):
        return "3.3V 供电时直连", "输出随供电：模块接 3.3V 供电即 3.3V 电平；接 5V 供电就要分压"
    if unknown:
        return "未核", "输出电平未核：" + "、".join(unknown)
    return "直连", "输出 ≤3.3V"


def direct_from_5v(e: dict) -> tuple[str, str]:
    """5V 主控（Arduino Nano、STC89）驱动模块输入能否直连。"""
    vmax = e.get("vcc_max")
    tol = str(e.get("io_5v_tolerant", "未核"))
    if tol.startswith("是"):
        return "直连", "模块输入耐 5V"
    if vmax is not None and vmax <= V_SAFE_3V3:
        return "需电平转换", f"模块最高 {vmax:g}V 供电，输入不耐 5V"
    if vmax is not None and vmax >= 4.5:
        return "5V 供电时直连", "模块可 5V 供电，5V 供电时输入按 5V 逻辑"
    return "未核", "模块输入耐压未核"


def i2c_fix(e: dict, addr: int, taken: set[int]) -> list[int]:
    """条目 e 的地址 addr 能改到哪些地址（不与 taken 冲突）。addr 在 i2c_addr_fixed 里就不能改。"""
    if addr in {addr_int(x) for x in e.get("i2c_addr_fixed", [])}:
        return []
    defaults = {addr_int(x) for x in e.get("i2c_addr", [])}
    opts = {addr_int(x) for x in e.get("i2c_addr_options", [])}
    # 多地址器件（如 ZS-042：DS3231 + AT24C32）只有可改的那颗芯片能换；没有分组信息时，候选里去掉其他默认地址
    return sorted(opts - defaults - taken)
