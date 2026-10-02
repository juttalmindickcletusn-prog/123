# 一次性生成 src/electrical.yaml（之后手工维护）。没有出处的值一律 null + "未核"，不估。
import yaml
ROOT = '/home/user/123/常用元器件库'
E = {}

def e(id, vcc, vmin, vmax, logic, out=None, io5v='未核', iface=(), addr=None, addr_alt=None, addr_opts=None,
      pull=None, fixed=None, ityp=None, ipeak=None, cap=None, outs=None, ins=None, src='', note=''):
    d = {'vcc_range': vcc, 'vcc_min': vmin, 'vcc_max': vmax, 'logic_v': logic, 'io_5v_tolerant': io5v, 'interface': list(iface)}
    if addr: d['i2c_addr'] = addr
    if addr_alt: d['i2c_addr_alt'] = addr_alt
    if addr_opts: d['i2c_addr_options'] = addr_opts
    if fixed: d['i2c_addr_fixed'] = fixed   # 不能改的地址
    if pull is not None: d['i2c_pullup'] = pull
    d['i_typ_ma'] = ityp or {'value': None, 'cond': '未核'}
    d['i_peak_ma'] = ipeak or {'value': None, 'cond': '未核'}
    if cap is not None: d['supply_capacity_ma'] = cap
    if outs: d['outputs'] = outs      # 模块输出给主控的脚：电平 'vcc'（随模块供电）或数值（V）或 null（未核/开漏）
    if ins: d['inputs'] = ins          # 主控驱动模块的脚：可写 vih_min（V）或备注
    d['src_ref'] = src
    if note: d['note'] = note
    E[id] = d

def I(v, c): return {'value': v, 'cond': c}
UNK = {'ohm': None, 'to': None, 'note': '未核（看模块板上电阻丝印或原理图）'}

# ---------------- 主控板 ----------------
esp_cap = {'value': None, 'note': '板载 3.3V LDO 型号和余量未核，模块 3.3V 用电多时单独加 LDO'}
for mid, name in (('MCU-001', 'LCKFB ESP32-S3R8N8'), ('MCU-004', 'ESP32-S3-DevKitC-1'), ('MCU-005', 'N16R8 兼容板'),
                  ('MCU-006', 'ESP32-DevKitC V4'), ('MCU-007', 'DOIT 30P'), ('MCU-008', 'ESP32-C3 SuperMini')):
    e(mid, '5V（USB 或 5V 脚），板载 LDO 出 3.3V', 4.75, 5.25, 'GPIO 3.3V', io5v='否', iface=['UART', 'I2C', 'SPI', 'ADC', 'PWM', 'Wi-Fi'],
      ipeak=I(500, '按用户规范 3.3 节：ESP32 负载预算按 ≥500mA 计'), cap=esp_cap,
      src='用户规范 3.3 节（ESP32 按 ≥500mA）；GPIO 不耐 5V 沿用第二批条目 logic_level（乐鑫规格书绝对最大额定值，云端未下载）')
e('MCU-016', '5V（安信可规格书只给 5V）', 5.0, 5.0, 'GPIO 3.3V', io5v='否', iface=['UART', 'Wi-Fi', 'Camera'],
  ityp=I(180, '关闪光灯 @5V（安信可规格书）'), ipeak=I(310, '闪光灯最亮 @5V（安信可规格书）'), cap=esp_cap,
  src='安信可 ESP32-CAM 规格书第 2 页 Power Dissipation', note='规格书 Notes：电源至少 5V 2A，否则图像有水波纹')
for mid in ('MCU-010', 'MCU-011'):
    e(mid, '5V（USB 或 VIN）', 4.75, 5.25, 'GPIO 3.3V', io5v='否', iface=['UART', 'I2C', 'SPI', 'ADC', 'Wi-Fi'],
      ityp=I(80, '按 ESP-01S 资料（同为 ESP8266）平均工作电流'), ipeak=I(300, '按 ESP-01S 资料 Wi-Fi 发射峰值'), cap=esp_cap,
      src='安信可 ESP-01S 资料（Tayda 转存，平均 80mA、峰值 300mA，同为 ESP8266 芯片）；A0 量程见 mcu_pins.yaml')
for mid in ('MCU-002', 'MCU-003'):
    e(mid, '5V（USB 或 5V 脚），板载 LDO 出 3.3V', 4.75, 5.25, '3.3V；FT 脚耐 5V（逐脚见 mcu_pins.yaml）', io5v='按脚', iface=['UART', 'I2C', 'SPI', 'ADC', 'USB', 'CAN'],
      cap={'value': None, 'note': '板载 LDO 型号未核'}, src='ST STM32F103x8 规格书 DS5319 表 5（FT 列）')
e('MCU-015', '5V（USB-C 或 5V 脚），板载 LDO 出 3.3V', 4.75, 5.25, '3.3V；FT 脚耐 5V（PA0、PB5 为 TC 不耐）', io5v='按脚', iface=['UART', 'I2C', 'SPI', 'ADC', 'USB'],
  cap={'value': None, 'note': 'V3.1 原理图 U2 只标 "SOT23-3 LDO"，型号和电流未核'}, src='ST STM32F411 规格书表 8；WeAct V3.1 原理图')
e('MCU-009', '5V（USB）或 VIN', 4.75, 5.25, '5V 逻辑', io5v='是', iface=['UART', 'I2C', 'SPI', 'ADC', 'PWM'],
  cap={'value': None, 'note': '板载 5V 稳压（VIN 供电时）和 3.3V 输出能力未核'}, src='本库 MCU-009 条目（5V 逻辑）；Arduino A000005 规格书（云端未下载）')
for mid in ('MCU-012', 'MCU-013'):
    e(mid, 'VBUS 5V 或 VSYS 1.8–5.5V（板载 DC-DC 出 3.3V）', 1.8, 5.5, 'GPIO 3.3V', io5v='否', iface=['UART', 'I2C', 'SPI', 'ADC', 'PWM', 'PIO'] + (['Wi-Fi'] if mid == 'MCU-013' else []),
      cap={'value': None, 'note': '3V3(OUT) 对外供电能力以 Pico 规格书为准（云端未下载）'}, src='本库 MCU-012/013 条目（Pico 规格书第 2 章，交接线索截图）')
e('MCU-014', '5V', 5.0, 5.0, '5V TTL；P0 开漏', io5v='是', iface=['UART'], src='本库 MCU-014 条目（STC89 手册，云端未取到正文）')

# ---------------- 显示 ----------------
oled = dict(iface=['I2C'], addr=['0x3C'], addr_alt='0x3D（模块背面电阻改焊；lcdwiki 写 8 位地址 0x78/0x7A）', addr_opts=['0x3C', '0x3D'], pull=UNK,
            ityp=I(18, 'lcdwiki 标正常显示 0.06W，按 3.3V 换算'), outs=None)
for mid in ('DSP-001', 'DSP-002', 'DSP-003', 'DSP-004', 'DSP-005'):
    e(mid, '3.3–5V（lcdwiki）', 3.3, 5.0, '3.3V/5V 兼容（lcdwiki：不需要电平转换）', io5v='是', src='lcdwiki MC096/MC130/MC091 页面与手册（地址、功耗）', **oled)
e('DSP-006', '3.3–5V（lcdwiki）', 3.3, 5.0, '3.3V/5V 兼容', io5v='是', iface=['SPI'], ityp=I(18, 'lcdwiki 标 0.06W，按 3.3V 换算'), src='lcdwiki 0.96 SPI OLED（MSP096X）')
e('DSP-007', 'VCC 3.3–5V，逻辑 3.3V（lcdwiki）', 3.3, 5.0, '3.3V', io5v='否', iface=['SPI'], ityp=I(61, 'lcdwiki 标功耗 0.2W 按 3.3V 换算，其中背光 38.2mA'),
  src='lcdwiki MSP1803 页面')
for mid in ('DSP-008', 'DSP-009'):
    e(mid, '3.3V（lcdwiki）', 3.3, 3.3, '3.3V', io5v='否', iface=['SPI'], src='lcdwiki MSP1541/MSP2008 手册（工作电压 3.3V）')
for mid in ('DSP-010', 'DSP-011'):
    e(mid, '3.3V/5V（lcdwiki）', 3.3, 5.0, '3.3V', io5v='否', iface=['SPI'], outs={'SDO_MISO': 3.3, 'T_DO': 3.3, 'T_IRQ': 3.3}, src='lcdwiki MSP2402/MSP2807 手册')
e('DSP-012', '5V', 5.0, 5.0, '5V（HD44780 兼容）', io5v='是', iface=['并口'], outs={'D0': 'vcc', 'D7': 'vcc'},
  src='本库 DSP-012 条目', note='RW 接地只写不读时屏不会往主控输出电平；要读忙标志则 D0–D7 输出 5V')
e('DSP-013', '5V（屏要 5V）', 5.0, 5.0, '随供电', io5v='未核', iface=['I2C'], addr=['0x27'], addr_alt='PCF8574AT 版为 0x3F；A0–A2 跳线可改：PCF8574 0x20–0x27、PCF8574A 0x38–0x3F（全部跳线短接为最低地址）',
  addr_opts=['0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27', '0x38', '0x39', '0x3A', '0x3B', '0x3C', '0x3D', '0x3E', '0x3F'],
  pull={'ohm': None, 'to': None, 'note': '未核：转接板是否带 I2C 上拉、上拉到哪，到货看板上电阻'},
  src='TI PCF8574/PCF8574A 规格书地址表（交接文档 1.2 节：PCF8574T=0x27、PCF8574AT=0x3F）')
e('DSP-015', '未核', None, None, '随供电（CLK/DIO 开漏，模块上拉到 VCC）', io5v='未核', iface=['两线（非 I2C）'], outs={'DIO': 'vcc'}, src='本库 DSP-015 条目')
e('DSP-016', '5V', 5.0, 5.0, '5V 器件', io5v='是', iface=['SPI 类'], ins={'DIN': '输入高电平门限以 MAX7219 规格书为准（未核），3.3V 驱动可能不稳'},
  src='本库 DSP-016 条目')

# ---------------- 通用芯片与分立件（电流预算用） ----------------
e('REG-002', '输入 4.5–12V', 4.5, 12, '不适用', iface=['电源'], cap={'value': 800, 'note': 'LD1117V33 额定 800mA（条目名称），按 70% 用'}, src='本库 REG-002 条目')
e('REG-003', '输入 4.8–12V', 4.8, 12, '不适用', iface=['电源'], cap={'value': 3000, 'note': 'LM1085 额定 3A，大电流按发热算'}, src='本库 REG-003 条目')
e('REG-004', '输入 7–25V', 7, 25, '不适用', iface=['电源'], cap={'value': 1500, 'note': 'L7805 额定 1.5A'}, src='本库 REG-004 条目')
e('BZ-001', '5V', 5.0, 5.0, '不适用（S8050 驱动）', iface=['数字'], ityp=I(30, '条目 supply/logic 字段'), src='本库 BZ-001 条目')
e('BZ-003', '5V', 5.0, 5.0, '不适用（S8050 驱动）', iface=['数字'], src='本库 BZ-003 条目')
e('Q-001', '不适用', None, None, '基极串 1k 由 3.3V GPIO 驱动', iface=['数字'], note='可开关约 100mA 负载（条目）', src='本库 Q-001 条目')
e('OPT-001', '不适用', None, None, '输入 3.3V GPIO 串 330Ω 约 6mA', iface=['数字'], ityp=I(6, '输入 LED 电流（条目）'), src='本库 OPT-001 条目')

# ---------------- 传感器 ----------------
e('SEN-001', 'DC 3.3–5.5V（奥松规格书）', 3.3, 5.5, '随供电', iface=['单总线'], outs={'DATA': 'vcc'}, ityp=I(0.3, '测量时（奥松规格书）'), src='奥松 DHT11 规格书（components101 转存）')
e('SEN-003', '3.3–5.5V', 3.3, 5.5, '随供电', iface=['单总线'], outs={'DATA': 'vcc'}, src='奥松 DHT22 规格书（SparkFun 转存）')
e('SEN-004', '芯片 2.0–5.5V；模块以说明为准', 2.0, 5.5, '随 VIN', iface=['I2C'], addr=['0x38'], addr_alt='不可改', addr_opts=['0x38'],
  pull={'ohm': 10000, 'to': 'vcc', 'note': 'Adafruit AHT20 板为 10k 上拉到 VIN；淘宝板未核'}, fixed=['0x38'], src='奥松 AHT20 规格书；Adafruit AHT20 引脚说明')
e('SEN-005', '以模块说明为准', None, None, '随 VCC', iface=['I2C'], addr=['0x38', '0x77'], addr_alt='BMP280 为 0x76 或 0x77（看 SDO），先 I2C 扫描',
  addr_opts=['0x38', '0x76', '0x77'], pull=UNK, fixed=['0x38'], src='AHT20/BMP280 规格书；cirkitdesigner 资料')
e('SEN-006', '2.5–5V（教程站）', 2.5, 5.0, '随 VIN', iface=['I2C'], addr=['0x44'], addr_alt='ADR 接 VIN 改 0x45', addr_opts=['0x44', '0x45'],
  pull={'ohm': 10000, 'to': 'vcc', 'note': '教程站：SCL/SDA 各 10k 上拉到 VIN'}, src='盛思锐 SHT3x 规格书；教程站 GY-SHT30-D 说明')
e('SEN-007', '3.0–5.5V（Maxim）', 3.0, 5.5, '开漏单总线，DQ 上拉到 VDD', iface=['单总线'], outs={'DQ': 'vcc'}, src='Maxim DS18B20 规格书')
e('SEN-008', '3.0–5.5V（Maxim）', 3.0, 5.5, '开漏单总线', iface=['单总线'], outs={'DQ': 'vcc'}, src='Maxim DS18B20 规格书')
e('SEN-009', '未核', None, None, '单总线，DQ 上拉', iface=['单总线'], outs={'DQ': 'vcc'}, src='规范第 7 节（V1.1 4.7k 上拉）')
e('SEN-010', '3V 版 / 5V 版（看后缀）', None, None, 'I2C 3.3V（教程站：模块带稳压和上拉）', iface=['I2C'], addr=['0x5A'], addr_alt='软件可改（EEPROM）', addr_opts=['0x5A'],
  pull={'ohm': None, 'to': '3.3', 'note': '教程站：带上拉，SCL/SDA 为 3.3V 电平；阻值未核'}, src='Melexis MLX90614 规格书；教程站 GY-906')
e('SEN-011', 'VIN（模块常标 3.3–5V）', 3.3, 5.0, '模块上拉电压各版不同', iface=['I2C'], addr=['0x57'], addr_alt='不可改', addr_opts=['0x57'],
  pull={'ohm': 4700, 'to': None, 'note': '教程站：多数模块板载 4.7k；上拉到哪（VIN/3.3V/1.8V）各版不同，未核'},
  ityp=I(0.6, '典型（教程站转述规格书，不含 LED 脉冲）'), fixed=['0x57'], src='Maxim MAX30102 规格书；教程站')
e('SEN-012', '3.3–5V', 3.3, 5.0, '模拟输出 0.3V~VCC', iface=['模拟'], outs={'SIG': 'vcc'}, ityp=I(4, '约 4mA（教程站）'), src='pulsesensor.com 资料（digikey 转存）')
e('SEN-013', '3.3V', 3.3, 3.3, '3.3V', iface=['模拟', '数字'], outs={'OUTPUT': 3.3, 'LO-': 3.3, 'LO+': 3.3}, src='SparkFun AD8232 Hookup Guide；ADI AD8232 规格书')
e('SEN-014', 'VCC 3.3–5V（模块带稳压）', 3.3, 5.0, '未核（模块上拉阻值和电压未核）', iface=['I2C'], addr=['0x68'], addr_alt='AD0 接 VCC 改 0x69', addr_opts=['0x68', '0x69'],
  pull=UNK, outs={'INT': None}, src='TDK MPU-6000/6050 规格书；教程站 GY-521')
e('SEN-015', '3–5V（教程站）', 3.0, 5.0, '教程站称 SDA/SCL 兼容 5V（未核）', iface=['I2C', 'SPI'], addr=['0x53'], addr_alt='SDO 接高改 0x1D', addr_opts=['0x53', '0x1D'],
  pull=UNK, src='ADI ADXL345 规格书；教程站 GY-291')
e('SEN-016', 'DC 4.5–20V（教程站）', 4.5, 20, '输出 3.3V', iface=['数字'], outs={'OUT': 3.3}, src='教程站 HC-SR501 资料')
e('SEN-017', '2.7–12V（教程站）', 2.7, 12, '输出 3.3V', iface=['数字'], outs={'OUT': 3.3}, ityp=I(0.1, '静态 <0.1mA（教程站）'), src='教程站 AM312 资料')
e('SEN-018', '5V（老版只能 5V）', 4.8, 5.0, 'Echo 输出 5V', io5v='是', iface=['数字'], outs={'ECHO': 'vcc'}, ityp=I(15, '工作电流（教程站）'), src='Handson HC-SR04 指南；教程站')
e('SEN-019', '3.3–5V（商家）', 3.3, 5.0, 'Echo 随供电', iface=['数字'], outs={'ECHO': 'vcc'}, src='商家 HC-SR04P 资料')
e('SEN-020', 'VIN 2.6–5.5V（教程站）', 2.6, 5.5, '板载电平转换到 VIN', iface=['I2C'], addr=['0x29'], addr_alt='软件可改（多只时用 XSHUT 逐个改）', addr_opts=['0x29'],
  pull={'ohm': None, 'to': 'vcc', 'note': '教程站：板载上拉并电平转换到 VIN；阻值未核'}, outs={'GPIO1': 'vcc'}, src='ST VL53L0X 规格书；教程站 GY-530')
e('SEN-021', 'VIN 4–28V（教程站）', 4.0, 28, '输出 3.3V', iface=['数字'], outs={'OUT': 3.3}, src='教程站 RCWL-0516；3V3 脚为输出（≤100mA）')
e('SEN-022', 'VCC 5–12V，建议 5V（海凌科手册）', 5.0, 12, '未核（以海凌科手册为准）', iface=['UART', '数字'], outs={'TX': None, 'OUT': None},
  src='海凌科 HLK-LD2410C 手册（naylamp 转存，摘要）')
for sid in ('SEN-023', 'SEN-024'):
    e(sid, '3.3V（手册：3.1–3.5V，纹波 ≤50mV，电源 ≥1A）', 3.1, 3.5, '3.3V', iface=['UART'], outs={'TX0': 3.3, 'TX2': 3.3},
      ipeak=I(600, '工作电流（海凌科手册，二手资料）'), src='海凌科 LD6002 手册（manuals.plus/商家转述）', note='要求低纹波，单独 LDO 供电')
e('SEN-025', '模块 VCC（芯片 2.4–3.6V，模块带稳压）', None, None, '未核', iface=['I2C'], addr=['0x23'], addr_alt='ADDR 接高改 0x5C', addr_opts=['0x23', '0x5C'], pull=UNK,
  src='ROHM BH1750FVI 规格书；教程站 GY-302')
for sid in ('SEN-026', 'SEN-027', 'SEN-028', 'SEN-029', 'SEN-035'):
    e(sid, '3.3–5V（教程站/商家）', 3.3, 5.0, 'DO/AO 随供电', iface=['数字', '模拟'], outs={'DO': 'vcc', 'AO': 'vcc'}, src='教程站/商家资料（LM393 比较器模块）')
for sid in ('SEN-032', 'SEN-033'):
    e(sid, '5V（加热丝 5V±0.1，炜盛手册）', 4.9, 5.1, 'DO/AO 随供电（5V）', iface=['数字', '模拟'], outs={'DO': 'vcc', 'AO': 'vcc'},
      ityp=I(160, '加热功耗 ≤800mW（炜盛 MQ 手册）按 5V 换算的上限'), src='炜盛 MQ-2 / MQ-135 手册 V1.4')
e('SEN-030', '3.3–5.5V（教程站）', 3.3, 5.5, 'AOUT 约 1.2–3V（教程站）', iface=['模拟'], outs={'AOUT': 3.0}, src='教程站 v1.2 资料')
e('SEN-031', '3.3–5V（教程站）', 3.3, 5.0, 'S 随供电', iface=['模拟'], outs={'SIG': 'vcc'}, src='Iduino SE045 资料')
e('SEN-034', '3.3–5V（教程站）', 3.3, 5.0, 'DO 随供电', iface=['数字'], outs={'DO': 'vcc'}, src='教程站 SW-420')
e('SEN-036', '2.7–5.5V（商家）', 2.7, 5.5, 'OUT 随供电', iface=['数字'], outs={'OUT': 'vcc'}, src='商家 VS1838B 资料')
e('SEN-037', 'A3144 4.5–24V（资料）', 4.5, 24, '开漏输出，上拉到主控电压', iface=['数字'], outs={'SIG': None}, src='Joy-IT KY-003 资料')
e('SEN-038', 'VCC 2.6–5.5V（教程站）', 2.6, 5.5, 'DT/SCK 随供电', iface=['两线（非 I2C）'], outs={'DT': 'vcc'}, ityp=I(1.5, '工作电流（教程站）'), src='Avia HX711 规格书（SparkFun GitHub）；教程站')
for sid in ('SEN-039', 'SEN-040'):
    e(sid, '4.5–5.5V（教程站）', 4.5, 5.5, 'OUT 0–5V 模拟（0A 时 VCC/2）', iface=['模拟'], outs={'OUT': 'vcc'}, src='Allegro ACS712 产品页；教程站')
e('SEN-041', 'VCC 3–5.5V（教程站）', 3.0, 5.5, '随 VCC', iface=['I2C'], addr=['0x40'], addr_alt='A0/A1 焊盘改 0x41、0x44、0x45', addr_opts=['0x40', '0x41', '0x44', '0x45'],
  pull=UNK, src='TI INA219 规格书（Adafruit 转存）；教程站')
e('SEN-042', '无需供电（电阻分压）', None, None, 'SIG = Vin/5', iface=['模拟'], outs={'SIG': 5.0}, src='教程站（30k/7.5k 分压）', note='输入 25V 时 SIG=5V，3.3V 主控最多测约 16.5V')
e('SEN-043', '3.3–5V（教程站）', 3.3, 5.0, '未核', iface=['UART'], outs={'TX': None, 'PPS': None}, src='教程站/商家 ATGM336H 资料')
e('SEN-044', '3.3–5V（模块带 3.3V 稳压）', 3.3, 5.0, 'TX 3.3V（NEO-6M 为 3.3V 芯片）；教程站称输入耐 5V（未核）', iface=['UART'], outs={'TX': 3.3},
  ityp=I(45, '典型（教程站）'), src='u-blox NEO-6 规格书；教程站 GY-NEO6MV2')
e('SEN-045', '3.3V（不能接 5V）', 3.3, 3.3, '3.3V', iface=['SPI'], outs={'MISO': 3.3, 'IRQ': 3.3}, src='NXP MFRC522 规格书；教程站')
e('SEN-046', '3.3–6V（教程站，资料不一）', 3.3, 6.0, '未核', iface=['UART'], outs={'TX': None, 'TOUCH': None}, ipeak=I(120, '<120mA（教程站）'), src='教程站/商家 AS608 资料')
e('SEN-047', '2.3–5.5V（教程站）', 2.3, 5.5, '未核', iface=['I2C'], addr=['0x68', '0x57'], addr_alt='DS3231 0x68 固定；AT24C32 0x57（A0–A2 焊盘可改 0x50–0x57）',
  addr_opts=['0x68', '0x50', '0x51', '0x52', '0x53', '0x54', '0x55', '0x56', '0x57'], pull=UNK, outs={'SQW': None, '32K': None},
  fixed=['0x68'], src='ADI DS3231 规格书；教程站 ZS-042')
e('SEN-048', '2.0–5.5V（教程站）', 2.0, 5.5, '随供电', iface=['三线（非 I2C）'], outs={'DAT': 'vcc'}, src='DS1302 规格书；教程站')
e('SEN-049', '模块 VCC 3.3–5V（看稳压）', 3.3, 5.0, 'MISO 电平未核（板载缓冲器）', iface=['SPI'], outs={'MISO': None}, src='教程站 Micro SD 模块')

# ---------------- 执行器 ----------------
for aid in ('ACT-001', 'ACT-002'):
    e(aid, '5V', 5.0, 5.0, 'IN 由主控驱动（3.3V 能否触发未核）', iface=['数字'], ityp=I(71.4, 'SRD-05VDC 线圈电流（松乐规格书 5V 高灵敏度型）'),
      src='松乐 SRD 规格书线圈参数表；教程站继电器模块')
e('ACT-003', '线圈 5V', 5.0, 5.0, '需三极管驱动', iface=['线圈'], ityp=I(71.4, '5V 线圈（SRD 高灵敏度型 70Ω）'), src='松乐 SRD 规格书 6. COIL DATA CHART')
e('ACT-004', '4.8–6V（教程站）', 4.8, 6.0, 'PWM 信号', iface=['PWM'], ityp=I(250, '带载 200–250mA（教程站）'), ipeak=I(750, '堵转 500–750mA（教程站）'), src='教程站 SG90 资料')
e('ACT-005', '4.8–7.2V（教程站）', 4.8, 7.2, 'PWM 信号', iface=['PWM'], ipeak=I(2500, '堵转约 2.5A（教程站）'), src='教程站 MG996R 资料')
e('ACT-006', '5V（教程站）', 5.0, 5.0, 'IN1–IN4 由主控驱动', iface=['数字'], src='TI ULN2003A 规格书；教程站', note='电机电流未核，按电机规格书算')
e('ACT-007', 'VM 4.5–13.5V，VCC 2.7–5.5V（教程站转述）', 2.7, 5.5, '逻辑随 VCC', iface=['PWM', '数字'], src='东芝 TB6612FNG 规格书；教程站', note='每路 1.2A 连续、3.2A 峰值；电机电流另算')
e('ACT-008', '电机电源 5–35V（模块资料）', 5.0, 35, '输入 TTL（门限未核）', iface=['PWM', '数字'], src='ST L298 规格书；教程站')
e('ACT-009', '2.7–10.8V（TI）', 2.7, 10.8, '输入 3.3V 可驱动（未核模块）', iface=['PWM', '数字'], src='TI DRV8833 产品页')
e('ACT-010', '3.2–5V（DFRobot）', 3.2, 5.0, 'UART，RX 串 1k', iface=['UART'], outs={'TX': None, 'BUSY': None}, src='DFRobot DFR0299 wiki')

# ---------------- 通信 ----------------
e('COM-001', 'VCC 3.6–6V（教程站）', 3.6, 6.0, 'TXD/RXD 3.3V', io5v='否', iface=['UART'], outs={'TXD': 3.3, 'STATE': 3.3}, src='教程站 HC-05')
e('COM-002', '以商品为准', None, None, 'TXD/RXD 3.3V', io5v='否', iface=['UART'], outs={'TXD': 3.3}, src='教程站 HC-06')
e('COM-003', '3.0–3.6V（安信可）', 3.0, 3.6, '3.3V', io5v='否', iface=['UART', 'Wi-Fi'], outs={'TXD': 3.3},
  ityp=I(80, '平均（安信可 ESP-01S 资料）'), ipeak=I(300, 'Wi-Fi 发射峰值（安信可）'), src='安信可 ESP-01S 资料（Tayda 转存）', note='电源建议 ≥500mA')
e('COM-004', '1.9–3.6V（教程站）', 1.9, 3.6, '3.3V', io5v='未核', iface=['SPI'], outs={'MISO': 3.3, 'IRQ': 3.3}, src='Nordic nRF24L01+ 规格书；教程站', note='加 10µF 去耦')
e('COM-005', '5V（ADI 规格书）', 5.0, 5.0, '5V（RO 输出 5V）', io5v='是', iface=['UART', 'RS485'], outs={'RO': 'vcc'}, src='ADI MAX481/485 规格书；教程站')

e('DSP-014', '5V', 5.0, 5.0, '经 DSP-013 转接板为 I2C', iface=['I2C'], src='本库 DSP-014 条目', note='I2C 地址和上拉见 DSP-013')
e('TOOL-001', 'USB 5V', 5.0, 5.0, '跳线选 3.3V 或 5V 电平', iface=['UART'], outs={'TXD': None}, src='本库 TOOL-001 条目', note='接 3.3V 主控前把跳线拨到 3.3V')
e('TOOL-002', 'USB 5V', 5.0, 5.0, '多数板 3.3V 电平（以模块为准）', iface=['UART'], outs={'TXD': None}, src='本库 TOOL-002 条目')
e('TOOL-003', 'USB 5V', 5.0, 5.0, '3.3V', iface=['SWD'], src='ST UM1075')
# ---------------- 电源模块 ----------------
e('PMD-001', 'Type-C 5V 输入', 5.0, 5.0, '不适用', iface=['电源'], cap={'value': 1000, 'note': '充电电流 1A（R_PROG 1.2k，商家资料）；OUT 带 DW01A 保护'}, src='TP4056 规格书；商家资料')
e('PMD-002', 'Type-C 5V 输入', 5.0, 5.0, '不适用', iface=['电源'], cap={'value': 1000, 'note': '充电电流 1A（R_PROG 1.2k）'}, src='TP4056 规格书')
e('PMD-003', '输入 4.5–28V', 4.5, 28, '不适用', iface=['电源'], cap={'value': 3000, 'note': '最大 3A（商家），长期按 1.5A 以下用'}, src='MPS MP1584 规格书；商家资料')
e('PMD-004', '输入 4–40V', 4.0, 40, '不适用', iface=['电源'], cap={'value': 3000, 'note': '最大 3A（商家）'}, src='TI LM2596 产品页；商家资料')
e('PMD-005', '输入 2–24V', 2.0, 24, '不适用', iface=['电源'], cap={'value': 2000, 'note': '最大 2A（商家），升压后输入电流更大'}, src='MT3608 模块资料（components101 转存）')
e('PMD-006', '单节 3.7V（满电 4.2V）', 3.0, 4.2, '不适用', iface=['电源'], cap={'value': None, 'note': '放电能力看电池规格，未核'}, src='规范 3.3 节')

lines = ['# 电气参数（第 5 节）。由云端一次生成，之后手工维护。每条写 src_ref；查不到的值为 null 并写"未核"，不估。',
         '# outputs：模块输出给主控的脚 → 电平（"vcc" 表示随模块供电电压；数值为固定电平；null 为未核或开漏）。',
         '# i2c_pullup.to："vcc"（随模块供电）、"3.3"（板载 3.3V）、null（未核）。', '']
class D(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True
D.add_representer(str, lambda d, s: d.represent_scalar('tag:yaml.org,2002:str', s))
open(ROOT + '/src/electrical.yaml', 'w', encoding='utf-8').write('\n'.join(lines) + yaml.dump(E, Dumper=D, allow_unicode=True, sort_keys=False, width=200, default_flow_style=None))
print(len(E))
