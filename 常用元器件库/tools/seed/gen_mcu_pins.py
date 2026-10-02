# 一次性生成 src/mcu_pins.yaml（之后作为手工维护的数据）。规则全部来自下列出处，每条约束写 src。
import json, re, sys
ROOT = '/home/user/123/常用元器件库'
sys.path.insert(0, ROOT + '/tools')
from module_defs import MODULES
REF = '/tmp/claude-0/-home-user-123/57dc0b4d-8ed4-59af-9bef-fb8add56e077/scratchpad/refs/'

SRC = {
 'idf_esp32': 'ESP-IDF 文档 api-reference/peripherals/gpio/esp32.inc（GitHub espressif/esp-idf master，GPIO 汇总表）',
 'idf_s3': 'ESP-IDF 文档 api-reference/peripherals/gpio/esp32s3.inc（GitHub espressif/esp-idf master）',
 'idf_c3': 'ESP-IDF 文档 api-reference/peripherals/gpio/esp32c3.inc（GitHub espressif/esp-idf master）',
 'hdg': '乐鑫《硬件设计指南》schematic-checklist.rst Strapping Pins 与 ADC 节（GitHub espressif/esp-hardware-design-guidelines）',
 'esptool': 'esptool 文档 boot-mode-selection.rst（GitHub espressif/esptool）',
 'spec': '用户《本科毕业设计硬件项目通用设计规范》3.2 节 GPIO 规则',
 'ard_doit': 'arduino-esp32 variants/doitESP32devkitV1/pins_arduino.h（LED_BUILTIN=2，TX=1，RX=3）',
 'ard_s3': 'arduino-esp32 variants/esp32s3/pins_arduino.h（TX=43，RX=44；RGB_LED=48 是 v1.0 板）',
 'ard_c3': 'arduino-esp32 variants/nologo_esp32c3_super_mini/pins_arduino.h（LED_BUILTIN=8，TX=21，RX=20）',
 'esp8266_ref': 'ESP8266 Arduino 核心 doc/reference.rst（GPIO6–11 接 Flash；A0 裸片 0–1.0V）',
 'nodemcu_h': 'ESP8266 Arduino 核心 variants/nodemcu/pins_arduino.h（LED_BUILTIN=2，LED_BUILTIN_AUX=16，D0–D8 对应）',
 'f103_ds': 'ST STM32F103x8 规格书 DS5319 Rev17 表 5 引脚定义（I/O Level 列 FT；WeAct BluePill-Plus 仓库转存）',
 'f411_ds': 'ST STM32F411xC/xE 规格书 Rev7 表 8 引脚定义（FT=耐 5V，TC=标准 3.3V；evidence/MCU-015）',
 'stm32duino_f103': 'stm32duino variants/STM32F1xx/F103C8T_F103CB(T-U)/variant_PILL_F103Cx.h（Bluepill LED=PC13）',
 'stm32duino_f411': 'stm32duino variant_BLACKPILL_F411CE.h（LED_BUILTIN=PC13，USER_BTN=PA0）',
 'weact_sch': 'WeAct MiniF4x1Cx V3.1 原理图（evidence/MCU-015/datasheet.pdf：KEY→PA0，蓝灯 PC13 经 1.5k 接 3.3V，Y1 32.768k 接 PC14/PC15）',
 'pico_h': 'pico-sdk src/boards/include/boards/pico.h（LED=GP25，默认 UART0 TX=GP0 RX=GP1，I2C0 GP4/GP5）',
 'pico_w_h': 'pico-sdk boards/pico_w.h（板载 LED 在无线芯片上，CYW43_WL_GPIO_LED_PIN=0）',
 'ai_cam': '安信可 ESP32-CAM 规格书第 3 页 Internal Pin Connect（evidence/MCU-016/datasheet.pdf）',
 'lib_yaml': '本库条目 pinout/pitfalls 字段（第一、二批本地核实）',
}

def norm(n):
    m = re.search(r'GPIO(\d+)', n)
    if m: return f'GPIO{m.group(1)}'
    m = re.fullmatch(r'IO(\d+)', n)
    if m: return f'GPIO{m.group(1)}'
    if n in ('U0T',): return 'GPIO1'
    if n in ('U0R',): return 'GPIO3'
    return n

POWER = {'GND', '3V3', '5V', 'VIN', 'VBAT', 'VCC', 'RST', 'NRST', 'EN', 'RSV', 'SD1', 'CMD', 'SD0', 'CLK', 'AGND', 'VSYS', 'VBUS', '3V3_EN', 'ADC_VREF', 'RUN', 'V_{cc}', 'AREF', '+5V', '~{RESET}'}

def board_pins(modname):
    out = []
    for r in MODULES[modname]['rows']:
        for n in r['names']:
            out.append((n, norm(n)))
    return out

def esp32_rules(g):
    n = int(g[4:])
    f, notes, use = [], [], '能用'
    if n in (0, 2, 5, 12, 15):
        f.append('strap'); notes.append('启动脚（GPIO0/2/5/MTDI/MTDO），上电时外部电路不能把它拉偏' + ('；MTDI 拉高会把 Flash 电压设成 1.8V 导致不启动' if n == 12 else '')); use = '慎用'
    if 6 <= n <= 11:
        f.append('flash'); notes.append('接模组内 SPI Flash'); use = '别用'
    if n in (16, 17):
        f.append('psram'); notes.append('WROVER（带 PSRAM）模组接 PSRAM，WROOM 模组可用'); use = '慎用'
    if 34 <= n <= 39:
        f.append('input_only'); notes.append('只能输入，无内部上下拉'); use = '慎用' if use == '能用' else use
    if n in (12, 13, 14, 15): f.append('jtag')
    if n in (1, 3):
        f.append('uart_log'); notes.append('默认串口 ' + ('TX' if n == 1 else 'RX') + '（下载和日志）'); use = '慎用'
    adc2 = {0: 1, 2: 2, 4: 0, 12: 5, 13: 4, 14: 6, 15: 3, 25: 8, 26: 9, 27: 7}
    adc1 = {32: 4, 33: 5, 34: 6, 35: 7, 36: 0, 37: 1, 38: 2, 39: 3}
    adc = f'ADC1_CH{adc1[n]}' if n in adc1 else (f'ADC2_CH{adc2[n]}（开 Wi-Fi 时不能用）' if n in adc2 else '')
    if n in adc2: f.append('adc2')
    if n in (36, 39): notes.append('开 ADC 或 Wi-Fi/蓝牙睡眠时不要用 GPIO36/39 中断（勘误 GPIO-3.11）')
    return f, notes, use, adc

def s3_rules(g, octal):
    n = int(g[4:])
    f, notes, use = [], [], '能用'
    if n in (0, 3, 45, 46):
        f.append('strap'); notes.append('启动脚（GPIO0/3/45/46）；用户规范要求避开'); use = '别用'
    if 26 <= n <= 32:
        f.append('flash'); notes.append('SPI Flash/PSRAM 占用'); use = '别用'
    if 33 <= n <= 37:
        if octal: f.append('psram'); notes.append('八线 PSRAM（R8）占用'); use = '别用'
        else: notes.append('八线 Flash/PSRAM 版本占用，四线版可用')
    if n in (19, 20):
        f.append('usb'); notes.append('USB D-/D+（板上 USB 口），改作 GPIO 后不能用 USB 下载/调试'); use = '别用'
    if n in (43, 44):
        f.append('uart_log'); notes.append('默认串口 ' + ('TX' if n == 43 else 'RX')); use = '慎用'
    adc = f'ADC1_CH{n-1}' if 1 <= n <= 10 else (f'ADC2_CH{n-11}（开 Wi-Fi 时受限）' if 11 <= n <= 20 else '')
    if 11 <= n <= 20: f.append('adc2')
    return f, notes, use, adc

def c3_rules(g):
    n = int(g[4:])
    f, notes, use = [], [], '能用'
    if n in (2, 8, 9):
        f.append('strap'); notes.append('启动脚（GPIO2/8/9）'); use = '慎用'
    if 12 <= n <= 17: f.append('flash'); notes.append('SPI Flash'); use = '别用'
    if n in (18, 19): f.append('usb'); notes.append('USB-JTAG'); use = '别用'
    if n in (20, 21): f.append('uart_log'); notes.append('默认串口 ' + ('RX' if n == 20 else 'TX')); use = '慎用'
    adc = f'ADC1_CH{n}' if 0 <= n <= 4 else ('ADC2_CH0（开 Wi-Fi 时受限）' if n == 5 else '')
    if n == 5: f.append('adc2')
    return f, notes, use, adc

def esp8266_rules(g):
    if g == 'A0':
        return ['adc'], ['唯一模拟输入：裸片 0–1.0V，NodeMCU 板一般带分压（以板为准）'], '慎用', 'ADC0'
    n = int(g[4:])
    f, notes, use = [], [], '能用'
    if n in (0, 2, 15):
        f.append('strap'); use = '慎用'
        notes.append({0: '启动脚：上电为低进下载（FLASH 键）', 2: '启动脚：上电须为高，下载模式会输出 TX', 15: '启动脚：上电须为低'}[n])
    if 6 <= n <= 11: f.append('flash'); notes.append('接 Flash（SD/CMD/CLK 引脚）'); use = '别用'
    if n in (1, 3): f.append('uart_log'); notes.append('默认串口 ' + ('TX' if n == 1 else 'RX')); use = '慎用'
    return f, notes, use, ''

def stm32_rules(p, chip):
    ft = json.load(open(REF + ('f103_ft.json' if chip == 'F103' else 'f411_ft.json')))
    f, notes, use = [], [], '能用'
    tol = ft.get(p)
    if p in ('PC13', 'PC14', 'PC15') and chip == 'F103':
        tol = '-'  # 规格书表中 PC13–15 的 I/O Level 为 "-"
        notes.append('PC13–15 驱动能力弱（只宜作低速输入/灌小电流），规格书有注')
    if tol == 'FT': f.append('ft')
    if p in ('PA11', 'PA12'): f.append('usb'); notes.append('USB D-/D+（板上 USB 口）'); use = '慎用'
    if p in ('PA13', 'PA14'): f.append('swd'); notes.append('SWD 下载调试口'); use = '别用'
    if p in ('PA15', 'PB3', 'PB4'): f.append('jtag'); notes.append('复位后为 JTAG，作 GPIO 要先关 JTAG（保留 SWD）'); use = '慎用'
    if chip == 'F103' and p == 'PB2': f.append('strap'); notes.append('BOOT1'); use = '慎用'
    if p in ('PA9', 'PA10'): f.append('uart_log'); notes.append('USART1，串口下载用'); use = '慎用'
    if chip == 'F411' and p in ('PC14', 'PC15'): f.append('occupied'); notes.append('板载 32.768kHz 晶振'); use = '别用'
    adc_map = {'PA0': 0, 'PA1': 1, 'PA2': 2, 'PA3': 3, 'PA4': 4, 'PA5': 5, 'PA6': 6, 'PA7': 7, 'PB0': 8, 'PB1': 9}
    adc = f"ADC{'12' if chip == 'F103' else '1'}_IN{adc_map[p]}" if p in adc_map else ''
    if adc and 'ft' in f: notes.append('作模拟输入时不耐 5V')
    return f, notes, use, adc

BOARDS = {}

def add_board(id, name, chip, five_v, pins_rules, srcs, extra=None, adc_range='', log=''):
    pins = {}
    for raw, g in pins_rules['header']:
        if g in POWER or raw in POWER or g in pins: continue
        f, notes, use, adc = pins_rules['fn'](g)
        e = (extra or {}).get(g)
        if e:
            f = f + e.get('flags', []); notes = notes + [e['note']]
            if e.get('use'): use = e['use']
        d = {'header': raw, 'use': use}
        if f: d['flags'] = f
        if adc: d['adc'] = adc
        d['five_v_tolerant'] = ('ft' in f) if five_v == 'by_pin' else five_v
        if notes: d['note'] = '；'.join(notes)
        pins[g] = d
    BOARDS[id] = {'board': name, 'chip': chip, 'five_v_tolerant': {True: '是', False: '否（所有 GPIO 不耐 5V）', 'by_pin': '按脚：FT 脚耐 5V（作模拟输入时除外），其余不耐'}[five_v],
                  'adc_range': adc_range, 'uart_log': log, 'sources': [SRC[s] for s in srcs], 'pins': pins,
                  'safe': [g for g, d in pins.items() if d['use'] == '能用']}

esp_extra_led2 = {'GPIO2': {'flags': ['led'], 'note': '板载 LED（DOIT 板）'}}
add_board('MCU-006', '乐鑫 ESP32-DevKitC V4（38P）', 'ESP32', False, {'header': board_pins('Module_ESP32-DevKitC-V4_38P'), 'fn': esp32_rules},
          ['idf_esp32', 'hdg', 'esptool'], {'GPIO0': {'flags': ['button'], 'note': 'BOOT 键'}},
          'ATTEN3 校准范围 150–2450 mV（硬件设计指南）', 'UART0 TX=GPIO1 RX=GPIO3')
add_board('MCU-007', 'ESP32 30P 开发板（DOIT 类）', 'ESP32', False, {'header': board_pins('Module_ESP32_DevKit_30P_W25.4'), 'fn': esp32_rules},
          ['idf_esp32', 'hdg', 'ard_doit'], dict(esp_extra_led2, GPIO0={'flags': ['button'], 'note': 'BOOT 键（不在排针上）'}),
          'ATTEN3 校准范围 150–2450 mV', 'UART0 TX=GPIO1 RX=GPIO3')
cam_extra = {'GPIO4': {'flags': ['occupied'], 'note': '板载闪光灯（TF 卡 DATA1 也用它）', 'use': '慎用'},
             'GPIO2': {'flags': ['occupied'], 'note': 'TF 卡 DATA0', 'use': '慎用'},
             'GPIO12': {'flags': ['occupied'], 'note': 'TF 卡 DATA2', 'use': '慎用'},
             'GPIO13': {'flags': ['occupied'], 'note': 'TF 卡 DATA3', 'use': '慎用'},
             'GPIO14': {'flags': ['occupied'], 'note': 'TF 卡 CLK', 'use': '慎用'},
             'GPIO15': {'flags': ['occupied'], 'note': 'TF 卡 CMD', 'use': '慎用'},
             'GPIO0': {'flags': ['occupied'], 'note': '摄像头 XCLK；拉低进下载', 'use': '别用'},
             'GPIO16': {'flags': [], 'note': '模组 PSRAM 占用（IDF：GPIO16–17 常接 PSRAM）', 'use': '别用'}}
add_board('MCU-016', '安信可 ESP32-CAM', 'ESP32', False, {'header': board_pins('Module_ESP32-CAM_AiThinker'), 'fn': esp32_rules},
          ['idf_esp32', 'hdg', 'ai_cam'], cam_extra, 'ATTEN3 校准范围 150–2450 mV', 'UART0 U0T=GPIO1 U0R=GPIO3')
s3_lckfb = lambda g: s3_rules(g, True)
add_board('MCU-001', '立创 LCKFB-ESP32S3R8N8（40P）', 'ESP32-S3（R8 八线 PSRAM）', False, {'header': board_pins('Module_LCKFB_ESP32S3R8N8'), 'fn': s3_lckfb},
          ['idf_s3', 'hdg', 'spec', 'lib_yaml'], {'GPIO0': {'flags': ['button'], 'note': 'BOOT 键'}},
          'ATTEN3 校准范围 0–2900 mV', 'UART0 TX=GPIO43 RX=GPIO44（不在排针上）')
add_board('MCU-004', '乐鑫 ESP32-S3-DevKitC-1 v1.1（44P）', 'ESP32-S3（N8R8 等八线 PSRAM 版占 33–37）', False, {'header': board_pins('Module_ESP32-S3-DevKitC-1'), 'fn': lambda g: s3_rules(g, True)},
          ['idf_s3', 'hdg', 'spec', 'ard_s3', 'lib_yaml'],
          {'GPIO0': {'flags': ['button'], 'note': 'BOOT 键'}, 'GPIO38': {'flags': ['led'], 'note': 'v1.1 板载 RGB LED（v1.0 板在 GPIO48）'}},
          'ATTEN3 校准范围 0–2900 mV', 'UART0 TX=GPIO43 RX=GPIO44')
add_board('MCU-005', 'ESP32-S3 N16R8 兼容板（DevKitC-1 脚位）', 'ESP32-S3（N16R8）', False, {'header': board_pins('Module_ESP32-S3-DevKitC-1'), 'fn': lambda g: s3_rules(g, True)},
          ['idf_s3', 'hdg', 'spec'], {'GPIO0': {'flags': ['button'], 'note': 'BOOT 键'}, 'GPIO48': {'flags': ['led'], 'note': '多数兼容板 RGB 在 GPIO48（未核，看商品）'}},
          'ATTEN3 校准范围 0–2900 mV', 'UART0 TX=GPIO43 RX=GPIO44')
add_board('MCU-008', 'ESP32-C3 SuperMini', 'ESP32-C3', False, {'header': board_pins('Module_ESP32-C3_SuperMini'), 'fn': c3_rules},
          ['idf_c3', 'hdg', 'ard_c3'], {'GPIO8': {'flags': ['led'], 'note': '板载蓝色 LED（arduino 变体 LED_BUILTIN=8）'}, 'GPIO9': {'flags': ['button'], 'note': 'BOOT 键'}},
          'ATTEN3 校准范围 0–2500 mV', 'UART0 TX=GPIO21 RX=GPIO20')
for mid, mod in (('MCU-010', 'Module_NodeMCU_ESP8266_CH340_W27.94'), ('MCU-011', 'Module_NodeMCU_ESP8266_CP2102_W22.86')):
    add_board(mid, 'NodeMCU ESP8266（' + ('CH340 宽版' if mid == 'MCU-010' else 'CP2102 窄版') + '）', 'ESP8266', False,
              {'header': board_pins(mod), 'fn': esp8266_rules}, ['esp8266_ref', 'esptool', 'nodemcu_h'],
              {'GPIO2': {'flags': ['led'], 'note': '模组蓝灯（LED_BUILTIN）'}, 'GPIO16': {'flags': ['led'], 'note': '板载 LED（LED_BUILTIN_AUX）'},
               'GPIO0': {'flags': ['button'], 'note': 'FLASH 键'}},
              'A0：裸片 0–1.0V，开发板一般带分压（以板为准）', 'UART0 TX=GPIO1 RX=GPIO3（接 USB 转串口）')
f103 = lambda p: stm32_rules(p, 'F103')
for mid in ('MCU-002', 'MCU-003'):
    add_board(mid, ('立创·地猛星' if mid == 'MCU-002' else '蓝色药丸') + ' STM32F103C8T6', 'STM32F103C8T6', 'by_pin',
              {'header': board_pins('Module_STM32F103C8T6_BluePill'), 'fn': f103}, ['f103_ds', 'stm32duino_f103'],
              {'PC13': {'flags': ['led'], 'note': '板载 LED（蓝色药丸，stm32duino）'}}, '0–3.3V（VREF+ = 3.3V）', 'USART1 TX=PA9 RX=PA10')
add_board('MCU-015', 'WeAct BlackPill STM32F411CEU6 V3.1', 'STM32F411CEU6', 'by_pin',
          {'header': board_pins('Module_WeAct_BlackPill_STM32F411'), 'fn': lambda p: stm32_rules(p, 'F411')}, ['f411_ds', 'weact_sch', 'stm32duino_f411'],
          {'PC13': {'flags': ['led'], 'note': '板载蓝灯（低电平亮）'}, 'PA0': {'flags': ['button'], 'note': '板载 KEY 按键（按下接地）'}},
          '0–3.3V', 'USART1 TX=PA9 RX=PA10')

# Pico / Pico W：符号引脚名 GPIOn
pico_hdr = [(f'GPIO{i}', f'GPIO{i}') for i in list(range(0, 23)) + [26, 27, 28]]
def pico_rules(g):
    n = int(g[4:]); f, notes, use = [], [], '能用'
    if n in (0, 1): f.append('uart_log'); notes.append('默认 UART0 ' + ('TX' if n == 0 else 'RX')); use = '慎用'
    adc = {26: 'ADC0', 27: 'ADC1', 28: 'ADC2'}.get(n, '')
    return f, notes, use, adc
for mid, src in (('MCU-012', 'pico_h'), ('MCU-013', 'pico_w_h')):
    add_board(mid, '树莓派 Pico' + (' W' if mid == 'MCU-013' else ''), 'RP2040', False, {'header': pico_hdr, 'fn': pico_rules}, [src, 'lib_yaml'],
              None, '0–3.3V（ADC 只有 GP26–28）', 'UART0 TX=GP0 RX=GP1')
BOARDS['MCU-012']['note'] = '板载 LED 在 GP25（不在排针上）'
BOARDS['MCU-013']['note'] = '板载 LED 接在无线芯片 CYW43 的 WL_GPIO0，不能当普通 GPIO 用'

# Arduino Nano（ATmega328P，5V）
nano_hdr = [(f'D{i}', f'D{i}') for i in range(0, 14)] + [(f'A{i}', f'A{i}') for i in range(0, 8)]
def nano_rules(g):
    f, notes, use = [], [], '能用'
    if g in ('D0', 'D1'): f.append('uart_log'); notes.append('接板载 USB 转串口（下载和串口监视器）'); use = '别用'
    if g == 'D13': f.append('led'); notes.append('板载 LED（L）')
    if g in ('A6', 'A7'): f.append('input_only'); notes.append('只能模拟输入，不能当数字 IO'); use = '慎用'
    if g in ('A4', 'A5'): notes.append('硬件 I2C（A4=SDA，A5=SCL）')
    return f, notes, use, (g if g.startswith('A') else '')
add_board('MCU-009', 'Arduino Nano（ATmega328P）', 'ATmega328P（5V）', True, {'header': nano_hdr, 'fn': nano_rules}, ['lib_yaml'],
          None, '0–5V（AREF 默认 5V）', 'Serial TX=D1 RX=D0')
BOARDS['MCU-009']['sources'].append('Arduino Nano 官方规格书 A000005（https://docs.arduino.cc/resources/datasheets/A000005-datasheet.pdf，云端未下载）')

# STC89C52RC
stc_hdr = [(f'P{a}.{b}', f'P{a}.{b}') for a in range(0, 4) for b in range(0, 8)]
def stc_rules(g):
    f, notes, use = [], [], '能用'
    if g.startswith('P0.'): f.append('open_drain'); notes.append('P0 口开漏，作输出要外接上拉（排阻 10k）'); use = '慎用'
    if g in ('P3.0', 'P3.1'): f.append('uart_log'); notes.append('串口（ISP 下载用）'); use = '慎用'
    return f, notes, use, ''
add_board('MCU-014', 'STC89C52RC（DIP-40）', 'STC89C52RC（5V）', True, {'header': stc_hdr, 'fn': stc_rules}, ['lib_yaml'], None, '无 ADC', 'UART TXD=P3.1 RXD=P3.0')

# 输出
lines = ['# 主控板逐脚约束表（第 5 节）。由云端一次生成，之后手工维护。',
         '# use：能用 / 慎用 / 别用。flags：strap 启动脚、flash/psram 占用、input_only 只能输入、usb、uart_log 默认串口、',
         '#   jtag/swd 调试口、led/button 板载、occupied 板上已占用、adc2（ESP 开 Wi-Fi 时 ADC2 不能用）、ft 耐 5V、open_drain。',
         '# five_v_tolerant：本脚能否直接接 5V 信号。每块板的出处写在 sources。', '']
import yaml
class D(yaml.SafeDumper): pass
def str_rep(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
D.add_representer(str, str_rep)
out = yaml.dump(BOARDS, Dumper=D, allow_unicode=True, sort_keys=False, width=200, default_flow_style=None)
open(ROOT + '/src/mcu_pins.yaml', 'w', encoding='utf-8').write('\n'.join(lines) + out)
print({k: (len(v['pins']), len(v['safe'])) for k, v in BOARDS.items()})
