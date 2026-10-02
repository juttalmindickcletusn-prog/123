"""一次性生成 src/market.yaml（热度依据、替代、推荐店铺）。数字全部来自：
  - evidence/<id>/jlc.json（嘉立创/立创接口记录：库存、起订价）
  - arduino/library-registry 仓库 repositories.txt（库数，commit df95082，2026-10-01）
  - 各 Arduino 内核 boards.txt（raw.githubusercontent.com，2026-10-02 取）
"""
import csv, json, re, sys
from pathlib import Path
import yaml

LIB = Path('/home/user/123/常用元器件库')
SP = Path(__file__).resolve().parent
REG = [l.strip() for l in open(SP / 'library-registry/repositories.txt') if l.strip().startswith('http')]
REG_TAG = 'arduino/library-registry@df95082（2026-10-01）'
TODAY = '2026-10-02'

rows = list(csv.DictReader(open(LIB / 'parts.csv', encoding='utf-8-sig')))

# 规则 2：带数字协议、需要驱动库的芯片 → 库数
CHIP = {
    'SEN-001': ('DHT11/DHT22', r'dht(?!20)'), 'SEN-003': ('DHT11/DHT22', r'dht(?!20)'),
    'SEN-004': ('AHT10/AHT20', r'aht[0-9x]'), 'SEN-005': ('BMP280', r'bmp280'), 'SEN-006': ('SHT3x', r'sht3'),
    'SEN-007': ('DS18B20', r'ds18b20|dallastemp'), 'SEN-008': ('DS18B20', r'ds18b20|dallastemp'),
    'SEN-009': ('DS18B20', r'ds18b20|dallastemp'),
    'SEN-010': ('MLX90614', r'mlx90614'), 'SEN-011': ('MAX3010x', r'max3010'),
    'SEN-014': ('MPU6050', r'mpu6050'), 'SEN-015': ('ADXL345', r'adxl345'),
    'SEN-018': ('HC-SR04', r'hc-?sr04|hcsr04'), 'SEN-019': ('HC-SR04', r'hc-?sr04|hcsr04'),
    'SEN-020': ('VL53L0X', r'vl53l0x'), 'SEN-022': ('LD2410', r'ld2410'),
    'SEN-023': ('LD6002', r'ld6002'), 'SEN-024': ('LD6002', r'ld6002'),
    'SEN-025': ('BH1750', r'bh1750'), 'SEN-038': ('HX711', r'hx711'), 'SEN-041': ('INA219', r'ina219'),
    'SEN-045': ('MFRC522/RC522', r'mfrc522|rc522'), 'SEN-047': ('DS3231/RTClib', r'ds3231|rtclib'),
    'SEN-048': ('DS1302', r'ds1302'), 'ACT-010': ('DFPlayer', r'dfplayer|dfmini|dfrobotdfplayer'),
    'COM-004': ('RF24', r'rf24'), 'DSP-015': ('TM1637', r'tm1637'), 'DSP-016': ('MAX7219/MAX72xx', r'max72'),
    'DSP-012': ('LiquidCrystal', r'liquidcrystal|lcd1602|lcd2004'), 'DSP-013': ('PCF8574', r'pcf8574'),
    'DSP-014': ('LiquidCrystal', r'liquidcrystal|lcd1602|lcd2004'),
    'DSP-001': ('SSD1306', r'ssd1306'), 'DSP-002': ('SSD1306', r'ssd1306'), 'DSP-005': ('SSD1306', r'ssd1306'),
    'DSP-006': ('SSD1306', r'ssd1306'), 'DSP-003': ('SH1106', r'sh1106'), 'DSP-004': ('SH1106', r'sh1106'),
    'DSP-007': ('ST7735', r'st7735'), 'DSP-008': ('ST7789', r'st7789'), 'DSP-009': ('ST7789', r'st7789'),
    'DSP-010': ('ILI9341', r'ili9341'), 'DSP-011': ('ILI9341', r'ili9341'),
}


def reg_hits(rx):
    out = []
    for l in REG:
        name = re.sub(r'^https?://(github|gitlab)\.com/', '', l).rstrip('/').removesuffix('.git')
        if re.search(rx, name, re.I):
            out.append(name)
    return out


# 规则 3：主控板在主流 Arduino 内核里有专属板型
CORE = {
    'MCU-003': ('stm32duino/Arduino_Core_STM32', 'BluePill F103C8'),
    'MCU-015': ('stm32duino/Arduino_Core_STM32', 'BlackPill F411CE'),
    'MCU-007': ('espressif/arduino-esp32', 'DOIT ESP32 DEVKIT V1'),
    'MCU-008': ('espressif/arduino-esp32', 'Nologo ESP32C3 Super Mini'),
    'MCU-016': ('espressif/arduino-esp32', 'AI Thinker ESP32-CAM'),
    'MCU-009': ('arduino/ArduinoCore-avr', 'Arduino Nano'),
    'MCU-010': ('esp8266/Arduino', 'NodeMCU 1.0 (ESP-12E Module)'),
    'MCU-011': ('esp8266/Arduino', 'NodeMCU 1.0 (ESP-12E Module)'),
    'MCU-012': ('earlephilhower/arduino-pico', 'Raspberry Pi Pico'),
    'MCU-013': ('earlephilhower/arduino-pico', 'Raspberry Pi Pico W'),
}
STD_PREFIX = ('PWR', 'HDR', 'SKT', 'JMP', 'TERM', 'XH', 'PH', 'SW', 'BZ', 'BAT', 'RES', 'POT', 'CAP', 'FUS',
              'DIO', 'LED', 'Q', 'OPT', 'REG', 'SEG')

ALT = {  # 模块/主控：库内同功能更优件及理由（无则写"无"并说明）
    'MCU-001': '乐鑫 ESP32-S3-DevKitC-1（MCU-004）：官方板，针序有官方图、教程最多；立创核心板的好处是立创商城可直接配单',
    'MCU-002': 'Blue Pill（MCU-003）脚位相同、教程多但芯片常为兼容片；要正品芯片就用地猛星本身',
    'MCU-003': '立创·地猛星（MCU-002）：脚位相同、立创自营可配单；要更强性能和 Type-C 选 BlackPill F411（MCU-015，WeAct 公开原理图）',
    'MCU-004': '无（乐鑫官方板）；要更小可用立创 ESP32-S3 核心板（MCU-001）',
    'MCU-005': '乐鑫官方 ESP32-S3-DevKitC-1（MCU-004）：针序有官方图，兼容板各家可能不同',
    'MCU-006': '新项目优先 ESP32-S3（MCU-004）：原生 USB、可用 GPIO 更多',
    'MCU-007': '乐鑫官方 ESP32-DevKitC V4（MCU-006）：针序有官方图；新项目优先 ESP32-S3（MCU-004）',
    'MCU-008': '要更多 IO 选 ESP32-S3（MCU-001/MCU-004）',
    'MCU-009': '要 WiFi/蓝牙或外设 3.3V 直连：ESP32-C3 SuperMini（MCU-008）；纯 5V 外设时 Nano 本身合适',
    'MCU-010': 'ESP32-C3 SuperMini（MCU-008）：芯片更新、带 BLE、体积小；NodeMCU v3 板宽，插面包板两侧不留空位',
    'MCU-011': 'ESP32-C3 SuperMini（MCU-008）：芯片更新、带 BLE、体积小',
    'MCU-012': '要 WiFi 选 Pico W（MCU-013），脚位相同',
    'MCU-013': '不需要无线用 Pico（MCU-012）：脚位相同，立创起订价 ¥43.71 比 Pico W ¥78.48 便宜（交接线索记录）',
    'MCU-014': '课程不要求 51 时优先 Arduino Nano（MCU-009）或 STM32（MCU-002/MCU-003）：USB 直接下载、资料多',
    'MCU-015': '无（库内性能最强的 STM32 板）',
    'MCU-016': '无（库内唯一带摄像头的主控）',
    'DSP-001': '要更大显示用 1.3 寸 SH1106（DSP-003），注意驱动芯片不同、库要换',
    'DSP-002': '项目里统一用 GND 在前版（DSP-001），避免两种针序混用接反',
    'DSP-003': '无；注意 SH1106 与 SSD1306 驱动不同',
    'DSP-004': '无；注意 SH1106 与 SSD1306 驱动不同',
    'DSP-005': '要多显示几行用 0.96 寸（DSP-001）',
    'DSP-006': '只要静态显示时 I2C 版（DSP-001）接线更少；SPI 版刷新更快',
    'DSP-007': 'ST7789 IPS（DSP-008/DSP-009）：IPS 视角更好',
    'DSP-008': '无', 'DSP-009': '无',
    'DSP-010': '要更小体积用 2.0 寸 ST7789（DSP-009）', 'DSP-011': '要更小体积用 2.0 寸 ST7789（DSP-009）',
    'DSP-012': '只显示几行字时用 I2C OLED（DSP-001）：3.3V 直连、4 根线；1602 并口要 5V 供电和对比度电位器，可加 PCF8574 转接板（DSP-013）减线',
    'DSP-013': '无', 'DSP-014': '无', 'DSP-015': '无', 'DSP-016': '无',
    'TOOL-001': '无（CP2102 版 TOOL-002 功能相同，二选一）', 'TOOL-002': '无（CH340 版 TOOL-001 功能相同，二选一）',
    'TOOL-003': '无',
    'SEN-001': 'AHT20（SEN-004）：I2C、3.3V 直连、精度更高（参数对比见 选型速查.md）',
    'SEN-003': 'SHT30（SEN-006）：I2C、精度更高（参数对比见 选型速查.md）',
    'SEN-004': '要同时测气压用 AHT20+BMP280（SEN-005）', 'SEN-005': '无', 'SEN-006': '无',
    'SEN-007': '测液体用防水探头（SEN-008）', 'SEN-008': '无',
    'SEN-009': 'DS18B20 探头（SEN-008）：驱动库和教程更多（见本表热度依据）',
    'SEN-010': '无', 'SEN-011': '无',
    'SEN-012': 'MAX30102（SEN-011）：I2C 数字输出，还能测血氧',
    'SEN-013': '无',
    'SEN-014': '无', 'SEN-015': '要角速度（姿态/跌倒）用 MPU6050（SEN-014）',
    'SEN-016': '要体积小用 AM312（SEN-017）', 'SEN-017': '要更远感应距离用 HC-SR501（SEN-016，可调）',
    'SEN-018': 'HC-SR04P（SEN-019）：3.3V 供电时输出 3.3V，可直连 ESP32/Pico', 'SEN-019': '无',
    'SEN-020': '无',
    'SEN-021': 'HLK-LD2410C（SEN-022）：能检测静止的人（呼吸微动），可串口读距离',
    'SEN-022': '无', 'SEN-023': '无', 'SEN-024': '无',
    'SEN-025': '无', 'SEN-026': '要光照数值（lux）用 BH1750（SEN-025）',
    'SEN-027': '无', 'SEN-028': '无', 'SEN-029': '无', 'SEN-030': '无', 'SEN-031': '无',
    'SEN-032': '无（MQ 系列只能定性，见 选型速查.md）', 'SEN-033': '无（MQ 系列只能定性；数字型 SGP30 未入库）',
    'SEN-034': '要测振动大小用 MPU6050（SEN-014）', 'SEN-035': '无', 'SEN-036': '无', 'SEN-037': '无',
    'SEN-038': '无',
    'SEN-039': 'INA219（SEN-041）：I2C 数字输出、同时测电压（量程较小，见 兼容性速查）',
    'SEN-040': '无', 'SEN-041': '无', 'SEN-042': 'INA219（SEN-041）：I2C 数字输出、同时测电流',
    'SEN-043': '无（北斗+GPS 双模）', 'SEN-044': 'ATGM336H（SEN-043）：北斗+GPS 双模',
    'SEN-045': '无', 'SEN-046': '无',
    'SEN-047': '无', 'SEN-048': 'DS3231（SEN-047）：温补晶振，走时更准，I2C 接口',
    'SEN-049': '无',
    'ACT-001': '无', 'ACT-002': '无',
    'ACT-003': '不想自己搭三极管驱动和续流二极管就用继电器模块（ACT-001/ACT-002）',
    'ACT-004': '要更大扭矩用 MG996R（ACT-005，金属齿）', 'ACT-005': '无', 'ACT-006': '无', 'ACT-007': '无',
    'ACT-008': 'TB6612FNG（ACT-007）：MOSFET 输出，压降和发热比 L298N 小，体积小', 'ACT-009': '无', 'ACT-010': '无',
    'COM-001': '主控用 ESP32（MCU-004/MCU-006）时自带蓝牙，可省掉模块',
    'COM-002': 'HC-05（COM-001）：可做主机', 'COM-003': 'ESP32-C3 SuperMini（MCU-008）：可直接当主控，省掉 AT 指令',
    'COM-004': '无', 'COM-005': '无',
    'PMD-001': '无', 'PMD-002': '带保护版（PMD-001）：有过充/过放/过流保护',
    'PMD-003': '无', 'PMD-004': '要体积小用 MP1584（PMD-003）', 'PMD-005': '无', 'PMD-006': '无',
}

SHOP = {
    'MCU-004': '乐鑫官方店（候选，店铺页未核实）', 'MCU-006': '乐鑫官方店（候选，店铺页未核实）',
    'MCU-015': 'WeAct 官方店（候选，店铺页未核实）', 'MCU-016': '安信可官方店（候选，店铺页未核实）',
    'COM-003': '安信可官方店（候选，店铺页未核实）',
    'SEN-022': '海凌科官方店（候选，店铺页未核实）', 'SEN-023': '海凌科官方店（候选，店铺页未核实）',
    'SEN-024': '海凌科官方店（候选，店铺页未核实）',
    'ACT-010': 'DFRobot 官方店（候选，店铺页未核实）',
    'MCU-009': 'Arduino 官方授权渠道（正品）或 CH340 兼容版综合店（候选，未核实）',
}
GENERIC_SHOP = '未核；可先在 优信电子、正点原子 等综合电子店搜关键词（候选，需登录核实）'


def jlc(pid, code):
    p = LIB / 'evidence' / pid / 'jlc.json'
    if not p.exists():
        return None, {}
    d = json.loads(p.read_text(encoding='utf-8'))
    return d, d.get('parts', {})


def unit(rec):
    return float(rec['cny_price']) if rec.get('cny_price') not in (None, '') else None


out = {}
for r in rows:
    pid, code = r['id'], r['lcsc_id']
    d, parts = jlc(pid, code)
    main = parts.get(code, {}) if parts else {}
    date = (d or {}).get('date', '')
    m = {}
    stock_txt = ''
    if main.get('jlc_stock') is not None:
        stock_txt = f"嘉立创库存 {main['jlc_stock']}、立创商城库存 {main.get('szlcsc_stock') or '未记录'}（{code}，{date} 接口记录）"
    # 热度
    if pid in CHIP:
        kw, rx = CHIP[pid]
        hits = reg_hits(rx)
        n = len(hits)
        lvl = '大众' if n >= 10 else ('常用' if n >= 4 else '冷门')
        ev = f"Arduino 官方库注册表仓库名含 {kw} 的库 {n} 个（{REG_TAG}；例：{'、'.join(h.split('/')[-1] for h in hits[:3]) or '无'}）"
        if stock_txt:
            ev += '；' + stock_txt
        m['sales_level'], m['sales_evidence'] = lvl, ev + '；淘宝销量未核（需登录）'
        m['sales_rule'] = '库数'
    elif pid in CORE:
        core, board = CORE[pid]
        ev = f"{core} 内核 boards.txt 内置专属板型“{board}”（{TODAY} 取自 raw.githubusercontent.com）"
        if stock_txt:
            ev += '；' + stock_txt
        m['sales_level'], m['sales_evidence'], m['sales_rule'] = '常用', ev + '；淘宝销量未核（需登录），未据此定为大众', '内核板型'
    elif pid.split('-')[0] in STD_PREFIX and main.get('jlc_stock') is not None:
        s = int(main['jlc_stock'])
        lvl = '大众' if s >= 50000 else ('常用' if s >= 5000 else '冷门')
        m['sales_level'], m['sales_evidence'], m['sales_rule'] = lvl, stock_txt + '；淘宝销量未核（需登录）', '嘉立创库存'
    else:
        why = '无专用驱动库（模拟/开关量或电源模块），库数不能代表热度' if pid.split('-')[0] in ('SEN', 'ACT', 'COM', 'PMD', 'TOOL', 'DSP', 'MCU') else '无嘉立创库存记录'
        m['sales_level'] = '未核'
        m['sales_evidence'] = f"未核：{why}；淘宝销量需登录" + (f"；{stock_txt}" if stock_txt else '')
        m['sales_rule'] = '无'
    # 替代
    if pid in ALT:
        m['better_alt'] = ALT[pid]
    else:
        alts = [(k, v) for k, v in parts.items() if k != code] if parts else []
        if not main or not alts:
            m['better_alt'] = '无（库内无同功能更优件；立创未记录替代编号）'
        else:
            k, v = alts[0]
            pu, au = unit(main), unit(v)
            bits = []
            if pu and au and au < pu * 0.95:
                bits.append(f"起订价 ¥{au:g}（{v.get('cny_step')} 起）比主选 ¥{pu:g}（{main.get('cny_step')} 起）便宜 {round((1 - au / pu) * 100)}%")
            ms, as_ = int(main.get('jlc_stock') or 0), int(v.get('jlc_stock') or 0)
            if as_ >= 2 * ms and as_ > 0:
                bits.append(f"嘉立创库存 {as_} 比主选 {ms} 多，更好买")
            name = f"{k}（{v.get('mpn', '')}，{v.get('brand', '')}）"
            if bits:
                m['better_alt'] = f"{name}：" + '；'.join(bits) + '（尺寸、参数差异见 parts.csv alternatives 列）'
            else:
                m['better_alt'] = f"无（替代 {name} 没有明显优势：起订价低不到 5%、嘉立创库存不到主选 2 倍；只作缺货备选）"
    # 店铺
    if pid in SHOP:
        m['recommend_shop'] = SHOP[pid]
    elif code.startswith('C'):
        m['recommend_shop'] = f'立创商城（按 {code} 下单）'
    else:
        m['recommend_shop'] = GENERIC_SHOP
    out[pid] = m

hdr = ("# 市场数据（人工/半自动核实部分）。由 build_market.py 与立创价格（price_history.csv / jlc.json）合并输出。\n"
       "# 热度规则（sales_rule）：\n"
       "#   嘉立创库存：标准件按嘉立创库存分档，≥50000 大众，5000–49999 常用，<5000 冷门（库存反映采购量级，不等于销量）\n"
       "#   库数：带数字协议的芯片/模块按 Arduino 官方库注册表中仓库名含芯片名的库数，≥10 大众，4–9 常用，≤3 冷门\n"
       "#   内核板型：主控板被主流 Arduino 内核收录专属板型 → 常用（没有销量数据，不定为大众）\n"
       "#   无：没有可靠依据 → 未核\n"
       "# 淘宝价格/销量：云端不能登录，全部未核；核到后按 price_taobao_ref: {shops: [{shop, url, price, spec, free_ship}], median} 填写，\n"
       "#   至少 3 家，build_market.py 会校验中位数。\n")
txt = yaml.safe_dump(out, allow_unicode=True, sort_keys=True, width=1000)
(LIB / 'src' / 'market.yaml').write_text(hdr + txt, encoding='utf-8')
from collections import Counter
print(Counter(v['sales_level'] for v in out.values()), Counter(v['sales_rule'] for v in out.values()))
for k in ('SEN-001', 'DSP-001', 'RES-001', 'CAP-002', 'MCU-012', 'SEN-030', 'BZ-002'):
    print(k, out[k])
