"""按功能选型速查：src/selection.yaml → 库根目录 选型速查.md。

参数只存一份：接口/供电/电平/电流读 src/electrical.yaml，坑读 parts.csv pitfalls，量程默认读 parts.csv key_params，
价格和热度读市场数据（market_lib）。selection.yaml 只写选型判断（难度、驱动库、场景、三档推荐、不推荐原因）。

检查（有错退出 1）：
  - 所有候选、推荐、不推荐里的编号都在 parts.csv；三档推荐必须是本功能的候选件；
  - 传感器、执行器、通信、电源类条目（前缀 SEN ACT COM PMD PWR REG BAT）每条至少出现在一个功能的候选里，没被引用的列出来；
  - "不推荐"每条都要有原因和出处；
  - 驱动库名必须在 LIB_REPO 里（已在 arduino/library-registry 核对存在的库），新加库要先核对再加进来。
用法：python tools/build_selection.py            # 检查并生成
      python tools/build_selection.py 某.yaml     # 用该文件代替 src/selection.yaml 只做检查（自测用）
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compat_lib as cl  # noqa: E402
import market_lib as ml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "选型速查.md"
COVER = ("SEN", "ACT", "COM", "PMD", "PWR", "REG", "BAT")
TIERS = ("省钱", "均衡", "精度")
# 驱动库 → Arduino 官方库注册表里的仓库（arduino/library-registry@df95082，2026-10-01 核对存在）
LIB_REPO = {
    "Adafruit ADXL345": "adafruit/Adafruit_ADXL345", "Adafruit AHTX0": "adafruit/Adafruit_AHTX0",
    "Adafruit BMP280 Library": "adafruit/Adafruit_BMP280_Library",
    "Adafruit Fingerprint Sensor Library": "adafruit/Adafruit-Fingerprint-Sensor-Library",
    "Adafruit ILI9341": "adafruit/Adafruit_ILI9341", "Adafruit INA219": "adafruit/Adafruit_INA219",
    "Adafruit MLX90614 Library": "adafruit/Adafruit-MLX90614-Library", "Adafruit MPU6050": "adafruit/Adafruit_MPU6050",
    "Adafruit SHT31 Library": "adafruit/Adafruit_SHT31", "Adafruit SSD1306": "adafruit/Adafruit_SSD1306",
    "Adafruit ST7735 and ST7789 Library": "adafruit/Adafruit-ST7735-Library",
    "ArduinoRS485": "arduino-libraries/ArduinoRS485", "BH1750": "claws/BH1750",
    "DFRobotDFPlayerMini": "DFRobot/DFRobotDFPlayerMini", "DHT sensor library": "adafruit/DHT-sensor-library",
    "DallasTemperature": "milesburton/Arduino-Temperature-Control-Library", "Ds1302": "Treboada/Ds1302",
    "ESP32Servo": "madhephaestus/ESP32Servo", "HCSR04": "d03n3rfr1tz3/HC-SR04", "HLK-LD6002": "phuongnamzz/HLK-LD6002",
    "HX711 Arduino Library": "bogde/HX711", "IRremote": "z3t0/Arduino-IRremote", "LedControl": "wayoda/LedControl",
    "LiquidCrystal I2C": "johnrickman/LiquidCrystal_I2C", "MD_MAX72XX": "MajicDesigns/MD_MAX72XX",
    "MFRC522": "miguelbalboa/rfid", "MPU6050": "ElectronicCats/mpu6050", "MQUnifiedsensor": "miguel5612/MQSensorsLib",
    "OneWire": "PaulStoffregen/OneWire", "PulseSensor Playground": "WorldFamousElectronics/PulseSensorPlayground",
    "RF24": "TMRh20/RF24", "RTClib": "adafruit/RTClib", "SD": "arduino-libraries/SD", "SdFat": "greiman/SdFat",
    "Servo": "arduino-libraries/Servo", "SparkFun MAX3010x Pulse and Proximity Sensor Library": "sparkfun/SparkFun_MAX3010x_Sensor_Library",
    "Stepper": "arduino-libraries/Stepper", "TFT_eSPI": "Bodmer/TFT_eSPI", "TM1637": "avishorp/TM1637",
    "TinyGPSPlus": "mikalhart/TinyGPSPlus", "U8g2": "olikraus/U8g2_Arduino", "VL53L0X": "pololu/vl53l0x-arduino",
    "ld2410": "ncmreynolds/ld2410",
}


def form(row: dict) -> str:
    m = row.get("mount", "")
    if m.startswith("不上板"):
        return "离板（导线/端子连接）"
    if "排针" in m or "排母" in m or "IC 座" in m:
        return "模块（插排母/杜邦线）"
    return "直插件"


def elec(e: dict) -> tuple[str, str, str]:
    if not e:
        return "—", "—", "—"
    iface = e.get("interface") or "—"
    if isinstance(iface, list):
        iface = "、".join(map(str, iface))
    vcc = str(e.get("vcc_range") or "未核")
    lv = e.get("logic_v")
    if lv:
        vcc += f"；电平 {lv}"
    cur = []
    for k, lab in (("i_typ_ma", "典型"), ("i_peak_ma", "峰值")):
        d = e.get(k) or {}
        if d.get("value") is not None:
            cur.append(f"{lab} {d['value']:g}mA")
    return str(iface), vcc, "，".join(cur) or "未核"


def check(sel: dict, ids: set[str]) -> tuple[list[str], list[str]]:
    errs, used = [], set()
    for grp, funcs in sel.items():
        for fn, f in (funcs or {}).items():
            where = f"{grp}/{fn}"
            cands = f.get("candidates") or {}
            for pid, c in cands.items():
                used.add(pid)
                if pid not in ids:
                    errs.append(f"{where}：候选 {pid} 不在 parts.csv")
                for lib in c.get("libs") or []:
                    if lib not in LIB_REPO:
                        errs.append(f"{where}：{pid} 的驱动库“{lib}”没核对过（先在 arduino/library-registry 查到再加进 LIB_REPO）")
                if not c.get("difficulty") or not c.get("diff_why"):
                    errs.append(f"{where}：{pid} 缺难度或难度理由")
            picks = f.get("picks") or {}
            if cands:
                for t in TIERS:
                    if t not in picks:
                        errs.append(f"{where}：缺“{t}”推荐")
            for t, (pid, why) in picks.items():
                if pid not in cands:
                    errs.append(f"{where}：{t}推荐 {pid} 不是本功能的候选件")
                if not why:
                    errs.append(f"{where}：{t}推荐没写理由")
            for a in f.get("avoid") or []:
                if a.get("id") and a["id"] not in ids:
                    errs.append(f"{where}：不推荐的 {a['id']} 不在 parts.csv")
                if not a.get("why") or not a.get("src"):
                    errs.append(f"{where}：不推荐的 {a.get('id') or a.get('name')} 缺原因或出处")
            for n in f.get("not_in_lib") or []:
                if not n.get("why"):
                    errs.append(f"{where}：未入库件 {n.get('name')} 没写原因")
            if not cands and not f.get("not_in_lib"):
                errs.append(f"{where}：既没有候选件也没有未入库说明")
    missing = sorted(i for i in ids if i.split("-")[0] in COVER and i not in used)
    for i in missing:
        errs.append(f"{i} 没出现在任何功能的候选里")
    return errs, missing


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = {r["id"]: r for r in ml.parts_rows()}
    alt = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sel = yaml.safe_load((alt or ROOT / "src" / "selection.yaml").read_text(encoding="utf-8"))
    errs, missing = check(sel, set(rows))
    if alt:
        for e in errs:
            print("✗", e)
        print(f"选型数据校验（{alt.name}）：错误 {len(errs)}")
        return 1 if errs else 0
    E, mk, hist = cl.electrical(), ml.market(), ml.history()
    esc = lambda s: str(s).replace("|", "/").replace("\n", " ")
    n_fn = sum(len(f) for f in sel.values())
    L = ["# 选型速查", "",
         "由 `tools/build_selection.py` 从 `src/selection.yaml` 生成，不要手改。接口/供电/电流来自 `src/electrical.yaml`，坑来自 `parts.csv`，",
         "价格和热度来自 `reports/价格与热度表.md` 同一份市场数据（淘宝价云端未核）。量程/精度没单独写出处的，取自 parts.csv key_params，括号里标了来源类型。", "",
         "难度：1 = 现成库几行代码、接线 ≤3 根；2 = I2C/SPI/串口或要注意电平；3 = 要调参、大电流或射频/协议多。", "",
         f"共 {len(sel)} 大类、{n_fn} 个功能。", ""]
    if errs:
        L += ["## 检查错误", ""] + [f"- {e}" for e in errs] + [""]
    L += ["## 目录", ""] + [f"- {g}：{'、'.join(f)}" for g, f in sel.items()] + [""]
    for grp, funcs in sel.items():
        L += [f"## {grp}", ""]
        for fn, f in funcs.items():
            L += [f"### {fn}", ""]
            cands = f.get("candidates") or {}
            if cands:
                L += ["| 编号 | 名称 | 量程/精度 | 接口 | 供电/电平 | 电流 | 形态 | 难度 | 驱动库 | 坑 | 适合 | 立创价 | 热度 |",
                      "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
                for pid, c in cands.items():
                    r = rows.get(pid, {})
                    spec = c.get("spec") or r.get("key_params", "")
                    if c.get("spec_src"):
                        spec += f"（出处：{c['spec_src']}）"
                    iface, vcc, cur = elec(E.get(pid) or {})
                    libs = "、".join(f"{x}（{LIB_REPO.get(x, '未核对')}）" for x in c.get("libs") or []) or "—"
                    m = ml.entry(r, mk, hist) if r else {}
                    L.append("| " + " | ".join(esc(x) for x in (
                        pid, r.get("name", "?"), spec, iface, vcc, cur, f"{form(r)}（{r.get('level', '')} 级）",
                        f"{c['difficulty']}：{c['diff_why']}", libs, r.get("pitfalls") or "—", c.get("fit", ""),
                        ml.price_brief(m) if m else "—", f"{m.get('sales_level', '未核')}" if m else "—")) + " |")
                L.append("")
                for t in TIERS:
                    if t in (f.get("picks") or {}):
                        pid, why = f["picks"][t]
                        L.append(f"- **{t}款**：{pid} {rows.get(pid, {}).get('name', '')} —— {why}")
                L.append("")
            for a in f.get("avoid") or []:
                who = f"{a['id']} {rows.get(a['id'], {}).get('name', '')}" if a.get("id") else a.get("name")
                L.append(f"- ⚠ **很多人用但不推荐：{who}**。{a['why']}（出处：{a['src']}）")
            for n in f.get("not_in_lib") or []:
                L.append(f"- 未入库：{n['name']}。{n['why']}")
            L.append("")
    if missing:
        L += ["## 没被任何功能引用的传感器/执行器/通信/电源条目", ""] + [f"- {i} {rows[i]['name']}" for i in missing] + [""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    for e in errs:
        print("✗", e)
    print(f"选型速查：{len(sel)} 大类 {n_fn} 个功能，未引用 {len(missing)} 条，错误 {len(errs)} → {OUT.name}")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
