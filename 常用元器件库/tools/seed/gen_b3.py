# 一次性生成：第三批条目 src/b3_modules.yaml + tools/module_defs_b3.py（生成后两个文件即为手工维护的源数据）
import re, textwrap
ROOT = '/home/user/123/常用元器件库'

HDR = []   # (fp_name, names, descr, label, pitch)
ENT = []

def q(s):
    s = str(s)
    if s == '' : return '""'
    if re.search(r'^[\s\-\[\]{}&*!|>\'"%@`#,?:]|: | #|^\d', s) or s in ('是', '否'):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s

def hdr_entry(id, cat, name, pn, url, key, supply, logic, pins, src, pit, kw, tag, label=None,
              alt='', pitch=2.54, extra_notes='', mount=None, level='C', pin1=None):
    n = len(pins)
    fp = f"Module_Hdr_{tag}_{n}P"
    HDR.append((fp, pins, f"{name}：底板排针，丝印印脚名（{' '.join(pins)}）", label or tag, pitch))
    pinout = '、'.join(f"{i+1}={p}" for i, p in enumerate(pins))
    ENT.append(dict(
        id=id, category=cat, name=name, lcsc='', datasheet_url=url, part_number=pn, manufacturer='淘宝通用',
        alternatives='[]', alternatives_text=alt or '无', key_params=key, supply=supply, logic_level=logic,
        pin_count=n, pinout=f"底板排针 {pinout}（{src}）",
        pitch_mm=f"{pitch:g}", row_spacing_mm='不适用', lead_size_mm='方针 0.64（排针）' if pitch == 2.54 else '方针 0.5（2.0 排针）',
        body_mm='未核（模块外形各家不同，底板只放排针）',
        mount=mount or f'底板焊 1×{n} 直排针，杜邦线按丝印脚名一一对接；要把模块直接插在排母上，先对照模块丝印确认顺序相同',
        seated_height_mm='8.2（排针）',
        pin1=pin1 or f'1={pins[0]}：PCB 方焊盘；按丝印脚名接线',
        kicad_symbol=f"StudentHW:{fp.replace('Module_', '')}", kicad_footprint=f"StudentHW:{fp}",
        dim_source='底板上只有排针，尺寸按 HDR-001 排针图纸（evidence/HDR-001/dim_PZ254_1xN.png）；模块本身没有厂家图' if pitch == 2.54
                   else '底板上只有 2.0 排针，尺寸按 HDR-004 图纸（evidence/HDR-004/dim_PZ200_1xN.png）',
        level=level, pitfalls=pit,
        notes=(f'规格书缺（淘宝模块，datasheet_url 给的是芯片规格书或厂家资料页）。脚序来源：{src}，二手资料，到货对照丝印。'
               f'{extra_notes}环宽：排针焊盘 1.7、孔 1.0，按 0.35 放宽（2.54 脚距）。模块无 3D 模型。') if pitch == 2.54 else
              (f'规格书缺（datasheet_url 为厂家资料页）。脚序来源：{src}。{extra_notes}环宽：焊盘 1.35、孔 0.8，2.0 脚距下按 0.275 放宽。模块无 3D 模型。'),
        taobao_keyword=kw, price='未查（淘宝需登录）', stock='淘宝（未核实）', polarized='是',
        lead_max_mm='0.64' if pitch == 2.54 else '0.5', ring_min_mm='0.35' if pitch == 2.54 else '0.275',
        evidence_extra=['evidence/HDR-001/dim_PZ254_1xN.png'] if pitch == 2.54 else ['evidence/HDR-004/dim_PZ200_1xN.png'],
    ))

def off_entry(id, cat, name, pn, url, key, supply, logic, pinout, src, pit, kw, mount, alt='', level='C', notes_extra=''):
    ENT.append(dict(
        id=id, category=cat, name=name, lcsc='', datasheet_url=url, part_number=pn, manufacturer='淘宝通用',
        alternatives='[]', alternatives_text=alt or '无', key_params=key, supply=supply, logic_level=logic,
        pin_count=0, pinout=f"{pinout}（{src}）", pitch_mm='不适用', row_spacing_mm='不适用', lead_size_mm='不适用',
        body_mm='不适用', mount=mount, seated_height_mm='不适用', pin1='不上板',
        kicad_symbol='不适用', kicad_footprint='不适用', dim_source='不上板，不需要尺寸图', level=level, pitfalls=pit,
        notes=f'不上板。规格书缺（淘宝模块/成品，datasheet_url 为芯片规格书或厂家资料）。{notes_extra}',
        taobao_keyword=kw, price='未查（淘宝需登录）', stock='淘宝（未核实）', polarized='否', lead_max_mm='',
    ))

S = '传感器'
# ---------- 温湿度与温度 ----------
hdr_entry('SEN-001', S, 'DHT11 温湿度模块（3P 板）', 'DHT11 module 3P', 'https://components101.com/sites/default/files/component_datasheet/DHT11-Temperature-Sensor.pdf',
  'DHT11（奥松），单总线；温湿度精度低（见选型速查）', 'DHT11 规格书：DC 3.3–5.5V', '随供电', ['VCC', 'DATA', 'GND'],
  '奥松 DHT11 规格书（components101 转存）；3P 板脚序各家不同，底板按功能名', 'DATA 要上拉（多数 3P 板已带）；两次读取间隔 ≥1 s；精度低，只适合演示', 'DHT11 模块 3P 温湿度', 'DHT11')
hdr_entry('SEN-003', S, 'DHT22 / AM2302 温湿度传感器（4P）', 'DHT22 (AM2302)', 'https://cdn.sparkfun.com/assets/f/7/d/9/c/DHT22.pdf',
  '单总线，温度 ±0.5℃、湿度 ±2%RH（max ±5%RH），0.5Hz 采样（规格书）', '3.3–5.5V（以规格书为准）', '随供电', ['VDD', 'DATA', 'NC', 'GND'],
  '奥松 DHT22 规格书（SparkFun 转存）引脚 1 VDD、2 DATA、3 NC、4 GND', '两次读取间隔 ≥2 s；AM2302 是带线版本，线色以商品说明为准', 'DHT22 AM2302 温湿度', 'DHT22')
hdr_entry('SEN-004', S, 'AHT20 温湿度模块（I2C 4P）', 'AHT20 module', 'https://www.aosong.com/userfiles/files/media/Data%20Sheet%20AHT20.pdf',
  'AHT20（奥松），I2C 地址 0x38（不可改），温度 ±0.3℃（规格书）', '模块 VIN（芯片 2.0–5.5V，模块以说明为准）', '随 VIN；板上 I2C 上拉阻值未核',
  ['VIN', 'GND', 'SCL', 'SDA'], 'Adafruit AHT20 引脚说明与教程站；淘宝蓝板顺序可能不同', '地址固定 0x38，与 PCF8574A 跳线全低（0x38）冲突', 'AHT20 温湿度模块 I2C', 'AHT20')
hdr_entry('SEN-005', S, 'AHT20 + BMP280 温湿度气压二合一模块（I2C 4P）', 'AHT20+BMP280 module', 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf',
  'AHT20（0x38）+ BMP280（0x76 或 0x77，看模块 SDO 接法）', '模块 VCC（以模块说明为准）', '随 VCC；板上上拉未核', ['VCC', 'GND', 'SCL', 'SDA'],
  'cirkitdesigner / ESPHome 社区资料', 'BMP280 地址 0x76/0x77 各家不同，先 I2C 扫描；有的板 BMP280 不响应要换地址', 'AHT20 BMP280 温湿度气压模块', 'AHT20_BMP280')
hdr_entry('SEN-006', S, 'SHT30 温湿度模块（GY-SHT30-D，I2C）', 'GY-SHT30-D', 'https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf',
  'SHT30（盛思锐），I2C 0x44，ADR 接 VIN 改 0x45（模块 ADR 下拉 10k）', 'VIN 2.5–5V（教程站，以模块为准）', '随 VIN；SCL/SDA 各 10k 上拉到 VIN（教程站资料）',
  ['VIN', 'GND', 'SCL', 'SDA', 'ADR', 'ALR'], '教程站 GY-SHT30-D 引脚说明（Adafruit SHT31-D 布局）；淘宝板脚数有 4P/6P 两种', '同一总线两只 SHT30 用 ADR 分地址', 'SHT30 温湿度模块 GY-SHT30-D', 'SHT30')
ENT.append(dict(id='SEN-007', category=S, name='DS18B20 数字温度传感器（TO-92）', lcsc='C18723599', datasheet_url='https://analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf',
  part_number='DS18B20(XBLW)', manufacturer='XBLW（芯伯乐，国产兼容）', alternatives='[]', alternatives_text='原装 Maxim DS18B20+（C 编号未核）',
  key_params='单总线，-55~+125℃，12 位；DQ 需 4.7k 上拉（Maxim 规格书）', supply='3.0–5.5V（Maxim 规格书）', logic_level='随供电（开漏单总线）',
  pin_count=3, pinout='1=GND、2=DQ、3=VDD（平面朝自己、引脚朝下，从左到右；Maxim 规格书）', pitch_mm='2.54', row_spacing_mm='不适用',
  lead_size_mm='未核（云端未取到 XBLW 规格书）', body_mm='TO-92', mount='立式直插，DQ 接 4.7k 上拉到 VDD', seated_height_mm='约 5（TO-92 本体，未核）',
  pin1='1=GND：平面朝自己、引脚朝下最左，PCB 方焊盘', kicad_symbol='Sensor_Temperature:DS18B20', kicad_footprint='StudentHW:TO-92_Inline_Wide',
  dim_source='Maxim DS18B20 规格书第 1 页 Pin Configurations（dim_DS18B20_pins.png，GitHub 公开转存的原版 PDF）：TO-92 1=GND 2=DQ 3=VDD；规格书正文没有 TO-92 外形尺寸（另见 Maxim 21-0248），脚径未核',
  level='C', pitfalls='国产兼容片有个别不支持寄生供电；VDD 和 GND 接反会烫手损坏', polarized='是', lead_max_mm='', ring_min_mm='0.35',
  notes='环宽：TO-92 加宽封装焊盘 1.5、孔 0.8，按 0.35 放宽（同 Q-001）。C 编号与型号由 jlcparts 镜像核实（XBLW 国产兼容）。datasheet.pdf 为 Maxim 原版（引脚兼容），XBLW 自家规格书未取到；定 C 级是因为没有 TO-92 外形和脚径图。', taobao_keyword='DS18B20 TO-92 温度传感器', pdf_keyword='DS18B20'))
off_entry('SEN-008', S, 'DS18B20 防水探头（3 线，不上板）', 'DS18B20 waterproof probe', 'https://analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf',
  '不锈钢封装 DS18B20，3 线', '3.0–5.5V（Maxim 规格书）', '随供电', '红=VDD、黑=GND、黄=DQ（多数商家，以商品说明为准）', '商品常见线色，未核',
  '线色以商品为准；DQ 4.7k 上拉放底板端子旁', 'DS18B20 防水探头 不锈钢', '不上板：接底板 TERM-004（KF301-5.08 3P）端子，底板放 4.7k 上拉',
  alt='M1820 探头（SEN-009）换算公式不同')
ENT.append(dict(id='SEN-009', category=S, name='M1820 数字温度探头（不上板，V1.1 已用）', lcsc='', datasheet_url='https://www.mysentech.com/',
  part_number='M1820 probe', manufacturer='敏源传感（Mysentech）', alternatives='[]', alternatives_text='DS18B20 防水探头（SEN-008），换算公式不同，在 config.h 选择',
  key_params='单总线数字温度探头（与 DS18B20 接法相同、数据换算不同）', supply='未核（以商品说明为准）', logic_level='随供电',
  pin_count=0, pinout='3 线接 KF301-5.08-3P，DQ 接 4.7kΩ 上拉（规范第 7 节 V1.1 实物验证）', pitch_mm='不适用', row_spacing_mm='不适用', lead_size_mm='不适用',
  body_mm='不适用', mount='不上板：接 TERM-004（KF301-5.08 3P）', seated_height_mm='不适用', pin1='不上板', kicad_symbol='不适用', kicad_footprint='不适用',
  dim_source='V1.1 实物验证（规范第 7 节 ✅：KF301-5.08-3P 端子 + 4.7kΩ 上拉）', level='A', pitfalls='与 DS18B20 换算公式不同，固件里必须选对型号',
  polarized='否', lead_max_mm='', notes='不上板。V1.1 实物验证。规格书缺（云端未取到敏源规格书，datasheet_url 为厂家主页）。线色以商品说明为准。',
  taobao_keyword='M1820 温度探头 敏源', price='未查（淘宝需登录）', stock='淘宝（未核实）'))
hdr_entry('SEN-010', S, 'MLX90614 红外测温模块（GY-906，I2C）', 'GY-906 MLX90614', 'https://www.melexis.com/-/media/files/documents/datasheets/mlx90614-datasheet-melexis.pdf',
  'MLX90614，I2C(SMBus) 地址 0x5A；物体 -70~+380℃（教程站）', '模块 VIN（有 3.3V 版和 5V 版，买前看后缀）', '模块带稳压和上拉（教程站资料，阻值未核）',
  ['VIN', 'GND', 'SCL', 'SDA'], '教程站 GY-906 引脚说明', 'BAA/BCC/DCI 后缀视场角不同；3V 版接 5V 会坏', 'GY-906 MLX90614 红外测温', 'GY-906')
# ---------- 生理 ----------
hdr_entry('SEN-011', S, 'MAX30102 心率血氧模块（单排 7P 紫板）', 'MAX30102 module 7P', 'https://datasheets.maximintegrated.com/en/ds/MAX30102.pdf',
  'MAX30102，I2C 地址 0x57（规格书）', 'VIN（模块常标 3.3–5V，以模块为准）；芯片本身 1.8V + LED 3.3V', '模块上拉电压各版不同（有的上拉到 1.8V），见兼容性速查',
  ['VIN', 'SCL', 'SDA', 'INT', 'IRD', 'RD', 'GND'], '教程站 MAX30102 模块引脚说明（VIN SCL SDA INT IRD RD GND）',
  '地址 0x57 与 DS3231 模块上的 AT24C32（0x57）冲突；规范第 7 节：V1.1 买到的是两侧各 4 针版，插不上单排座——两侧版另见 待确认.md', 'MAX30102 心率血氧 模块', 'MAX30102')
hdr_entry('SEN-012', S, 'PulseSensor 光电脉搏传感器（3 线）', 'PulseSensor', 'https://media.digikey.com/pdf/Data%20Sheets/Pulse%20Sensor%20PDFs/Pulse_Sensor.pdf',
  '模拟输出心率波形，约 4mA（教程站）', '3.3–5V（教程站）', '模拟输出 0.3V~VCC，接 3.3V 主控用 3.3V 供电', ['SIG', 'VCC', 'GND'],
  'pulsesensor.com 资料（紫=信号、红=VCC、黑=GND）', '只能测心率不能测血氧；运动干扰大', 'Pulse Sensor 心率传感器', 'PulseSensor')
hdr_entry('SEN-013', S, 'AD8232 单导联心电模块（6P）', 'AD8232 ECG module', 'https://www.analog.com/media/en/technical-documentation/data-sheets/ad8232.pdf',
  'AD8232 心电前端，模拟输出 + 导联脱落检测 LO+/LO-', '3.3V（模块标注）', '3.3V', ['GND', '3.3V', 'OUTPUT', 'LO-', 'LO+', 'SDN'],
  'SparkFun AD8232 Hookup Guide 引脚顺序', '电极接触不良时 OUTPUT 乱跳，用 LO+/LO- 判断；不是医疗器械', 'AD8232 心电 模块', 'AD8232')
# ---------- 运动 ----------
hdr_entry('SEN-014', S, 'MPU6050 六轴模块（GY-521，8P）', 'GY-521 MPU6050', 'https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/mpu-6000-datasheet1.pdf',
  'MPU6050，I2C 地址 0x68（AD0 接高 0x69）', 'VCC 3.3–5V（模块带稳压，教程站）', '模块上拉阻值和电压未核（见兼容性速查）', ['VCC', 'GND', 'SCL', 'SDA', 'XDA', 'XCL', 'AD0', 'INT'],
  '教程站 GY-521 引脚说明（VCC GND SCL SDA XDA XCL AD0 INT）', '0x68 与 DS3231（0x68）冲突，AD0 接 VCC 改 0x69；XDA/XCL 悬空', 'GY-521 MPU6050 模块', 'GY-521')
hdr_entry('SEN-015', S, 'ADXL345 三轴加速度模块（GY-291，8P）', 'GY-291 ADXL345', 'https://www.analog.com/media/en/technical-documentation/data-sheets/adxl345.pdf',
  'ADXL345，I2C 0x53（SDO 接地），SDO 接高 0x1D；也可 SPI', '3–5V（模块标注，教程站）', '模块称 SDA/SCL 兼容 5V（未核）', ['GND', 'VCC', 'CS', 'INT1', 'INT2', 'SDO', 'SDA', 'SCL'],
  '教程站 GY-291 引脚说明', 'I2C 模式 CS 要接高；SDO 决定地址', 'GY-291 ADXL345 模块', 'GY-291')
# ---------- 人体与距离 ----------
hdr_entry('SEN-016', S, 'HC-SR501 人体红外模块（3P）', 'HC-SR501', 'https://components101.com/sensors/hc-sr501-pir-sensor',
  '热释电人体感应，输出高 3.3V / 低 0V，感应 3–7m（教程站）', 'DC 4.5–20V（教程站）', '输出 3.3V，可直连 3.3V 主控', ['VCC', 'OUT', 'GND'],
  '教程站 HC-SR501 引脚说明；有的板丝印在透镜罩下', '上电后约 1 分钟内会误触发；两个电位器调灵敏度和延时，跳线选可重复触发', 'HC-SR501 人体红外感应模块', 'HC-SR501')
hdr_entry('SEN-017', S, 'AM312 迷你人体红外模块（3P）', 'AM312', 'https://pinouthub.com/am312-pir-sensor/',
  '小型热释电，输出高 3.3V，静态 <0.1mA（教程站）', '2.7–12V（教程站）', '输出 3.3V', ['VCC', 'OUT', 'GND'], '教程站 AM312 引脚说明',
  '距离和角度比 HC-SR501 小，延时不可调', 'AM312 迷你人体感应', 'AM312')
hdr_entry('SEN-018', S, 'HC-SR04 超声波测距模块（5V，4P）', 'HC-SR04', 'https://www.handsontec.com/dataspecs/HC-SR04-Ultrasonic.pdf',
  '2–400cm，40kHz，Trig 10µs 触发（教程站）', '5V，工作电流约 15mA（教程站）', 'Echo 输出 5V，接 3.3V 主控要分压', ['VCC', 'TRIG', 'ECHO', 'GND'],
  'Handson Technology HC-SR04 用户指南与教程站', '老版只能 5V 供电；Echo 是 5V，ESP32/STM32 必须分压或换 HC-SR04P', 'HC-SR04 超声波模块', 'HC-SR04')
hdr_entry('SEN-019', S, 'HC-SR04P 超声波测距模块（3.3–5V，4P）', 'HC-SR04P', 'https://x2robotics.ca/hc-sr04p-ultrasonic-ranging-sensor-3-3v-5v',
  '与 HC-SR04 尺寸软件兼容，宽电压（商家资料）', '3.3–5V（商家资料）', 'Echo 电平随供电：3.3V 供电即 3.3V 输出', ['VCC', 'TRIG', 'ECHO', 'GND'],
  '商家资料（与 HC-SR04 相同）', '要 3.3V 电平就用 3.3V 供电；外观与 HC-SR04 几乎一样，看丝印 P', 'HC-SR04P 超声波 3.3V', 'HC-SR04P')
hdr_entry('SEN-020', S, 'VL53L0X 激光测距模块（GY-530，6P）', 'GY-530 VL53L0X', 'https://www.st.com/resource/en/datasheet/vl53l0x.pdf',
  'VL53L0X，I2C 0x29（可软件改），最远约 2m（教程站）', 'VIN 2.6–5.5V，板载稳压到 2.8V（教程站）', '板载电平转换和上拉（教程站，阻值未核）', ['VIN', 'GND', 'SCL', 'SDA', 'GPIO1', 'XSHUT'],
  '教程站 GY-530 引脚说明', '多只同用要靠 XSHUT 逐个上电改地址；强光下量程变短', 'GY-530 VL53L0X 激光测距', 'GY-530')
hdr_entry('SEN-021', S, 'RCWL-0516 微波雷达感应模块（5P）', 'RCWL-0516', 'https://www.datasheethub.com/rcwl-0516-microwave-radar-sensor-module/',
  '多普勒微波（约 3.2GHz），OUT 高 3.3V 约 2s（教程站）', 'VIN 4–28V（教程站）；3V3 脚为输出（≤100mA）', 'OUT 3.3V', ['3V3', 'GND', 'OUT', 'VIN', 'CDS'],
  '教程站 RCWL-0516 引脚说明', '能穿透塑料外壳，背面也会触发；3V3 脚是输出不是输入', 'RCWL-0516 微波雷达', 'RCWL-0516')
hdr_entry('SEN-022', S, '海凌科 HLK-LD2410C 24GHz 人体存在雷达（2.54 5P）', 'HLK-LD2410C', 'https://naylampmechatronics.com/img/cms/001080/HLK-LD2410C_datasheet.pdf',
  '24GHz 毫米波，人体存在/运动，UART 256000 + OUT 脚（海凌科手册）', 'VCC 5–12V，建议 5V（海凌科手册）', 'UART/OUT 3.3V（以手册为准）', ['TX', 'RX', 'OUT', 'GND', 'VCC'],
  '海凌科 HLK-LD2410C 手册引脚表（孔径 0.9、脚距 2.54）', 'LD2410/LD2410B 是 1.27 脚距 7×35 小板，不是这个封装（见 待确认.md）；UART 默认 256000 波特率', 'HLK-LD2410C 人体存在雷达', 'LD2410C',
  mount='底板焊 1×5 直排针，杜邦线按脚名对接；模块孔 0.9，排针可直接焊在模块上')
# LD6002：用 V1.1 已实焊的 2.0 排母封装（SKT-003，A 级）
for sid, nm, pn, fn in (('SEN-023', '海凌科 HLK-LD6002 60GHz 呼吸心率雷达（2.0 8P）', 'HLK-LD6002', '呼吸心率'),
                         ('SEN-024', '海凌科 HLK-LD6002C 60GHz 雷达（2.0 8P，外观同 LD6002）', 'HLK-LD6002C', 'LD6002C')):
    ENT.append(dict(id=sid, category=S, name=nm, lcsc='', datasheet_url='https://www.hlktech.net/index.php?id=1180', part_number=pn, manufacturer='Hi-Link（海凌科）',
      alternatives='[]', alternatives_text='LD6002 与 LD6002C 外观相同、功能不同，插座上印功能名',
      key_params='60GHz FMCW 雷达，UART', supply='3.3V（手册：3.1–3.5V，纹波 ≤50mV，电源能力 ≥1A；二手资料）', logic_level='3.3V',
      pin_count=8, pinout='1=3V3、2=GND、3=P19（上电须拉低）、4=TX2、5=AIO1、6=SCL0、7=TX0、8=RX0（海凌科手册引脚表，manuals.plus/教程站转述）',
      pitch_mm='2.0', row_spacing_mm='不适用', lead_size_mm='2.0 排针', body_mm='约 25×31.5（手册，二手资料）', mount='底板焊 1×8 2.0mm 排母（V1.1 同款），模块插上',
      seated_height_mm='未核', pin1='1=3V3：PCB 方焊盘；插座旁印功能名区分 LD6002/LD6002C',
      kicad_symbol=f"StudentHW:{'HLK-LD6002' if sid == 'SEN-023' else 'HLK-LD6002C'}_8P", kicad_footprint='StudentHW:PinSocket_1x08_P2.00mm_Vertical',
      dim_source='封装 = SKT-003（V1.1 实焊的 2.0 排母，A 级）；引脚名按海凌科手册二手资料，云端未取到原版手册',
      level='C', pitfalls='要求低纹波 3.3V，建议单独 LDO；P19 上电必须为低，否则进下载模式；两款外观相同，插错功能不对',
      polarized='是', lead_max_mm='0.5', ring_min_mm='0.275',
      notes='封装与规范第 7 节 ✅ 的 V1.1 排母相同，但引脚名是二手资料，本地对照 V1.1 原理图和海凌科原版手册后可定 A。环宽：焊盘 1.35、孔 0.8，按 0.275 放宽（V1.1 原封装）。规格书缺（hlktech 被云端拦截）。模块无 3D 模型（排母有）。',
      taobao_keyword=f'海凌科 {pn} 雷达', price='未查（淘宝需登录）', stock='淘宝（未核实）',
      evidence_extra=['evidence/SKT-003/dim_HX_PM20.png']))
# ---------- 环境 ----------
hdr_entry('SEN-025', S, 'BH1750 光照模块（GY-302，5P）', 'GY-302 BH1750', 'https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf',
  'BH1750FVI，1–65535 lx，I2C 0x23（ADDR 接高 0x5C）', '模块 VCC（芯片 2.4–3.6V，模块带稳压，以模块为准）', '上拉电压阻值未核', ['VCC', 'GND', 'SCL', 'SDA', 'ADDR'],
  '教程站 GY-302 引脚说明', 'ADDR 悬空/接地 0x23；同总线两只要一只 ADDR 接高', 'GY-302 BH1750 光照模块', 'GY-302')
for sid, nm, pn, url, key, kw, tag, src in (
  ('SEN-026', '光敏电阻模块（LM393，4P）', 'LDR LM393 module 4P', 'https://notenoughtech.com/raspberry-pi/light-sensor-lm393-ky018/', '光敏电阻 + LM393 比较器，DO 阈值可调、AO 模拟', '光敏电阻模块 4针 LM393', 'LDR_LM393', '教程站（VCC GND DO AO）'),
  ('SEN-027', '声音传感器模块（KY-038 类，4P）', 'Sound sensor KY-038', 'https://eclass.uth.gr/modules/document/file.php/E-CE_U_269/Sensors/Sensors_%20Datasheets/KY-038-Joy-IT.pdf', '驻极体话筒 + LM393，DO 声音阈值、AO 模拟', '声音传感器模块 4针', 'Sound', 'Joy-IT KY-038 资料（丝印顺序 AO G + DO，底板按功能名）'),
  ('SEN-028', '火焰传感器模块（LM393，4P）', 'Flame sensor LM393', 'https://www.rajguruelectronics.com/Product/13200/A132002_Flame%20sensor%20Module%20LM393_Datasheet.pdf', '红外接收管 760–1100nm + LM393', '火焰传感器模块 4针', 'Flame', '商家资料（VCC GND DO AO）'),
  ('SEN-029', '雨滴传感器模块（4P）', 'Raindrop sensor module', 'https://www.openhacks.com/uploadsproductos/rain_sensor_module.pdf', '雨滴板 + LM393，DO 阈值、AO 模拟', '雨滴传感器模块', 'Rain', '商家资料（VCC GND DO AO）'),
  ('SEN-032', 'MQ-2 烟雾/可燃气体模块（4P）', 'MQ-2 module', 'https://www.winsen-sensor.com/d/files/PDF/Semiconductor%20Gas%20Sensor/MQ-2%20(Ver1.4)%20-%20Manual.pdf', '炜盛 MQ-2，加热式，只能定性', 'MQ-2 烟雾传感器模块', 'MQ-2', '教程站（VCC GND DO AO）'),
  ('SEN-033', 'MQ-135 空气质量模块（4P）', 'MQ-135 module', 'https://www.winsen-sensor.com/d/files/PDF/Semiconductor%20Gas%20Sensor/MQ135%20(Ver1.4)%20-%20Manual.pdf', '炜盛 MQ-135，加热式，只能定性', 'MQ-135 空气质量模块', 'MQ-135', '教程站（VCC GND DO AO）'),
  ('SEN-035', 'TCRT5000 红外反射/循迹模块（4P）', 'TCRT5000 module', 'https://www.vishay.com/en/product/83760/', 'TCRT5000 反射式光电 + 比较器，检测距离约 15mm（Vishay）', 'TCRT5000 循迹模块', 'TCRT5000', '教程站（VCC GND D0 A0）')):
    gas = sid in ('SEN-032', 'SEN-033')
    hdr_entry(sid, S, nm, pn, url, key, '5V（加热丝 5V，功耗规格书 ≤800mW 量级，见兼容性速查）' if gas else '3.3–5V（教程站）',
      'DO/AO 电平随供电；5V 供电时 AO 最高 5V，接 3.3V 主控 ADC 要分压' if gas else 'DO/AO 随供电',
      ['VCC', 'GND', 'DO', 'AO'], src,
      ('要预热（规格书标准条件预热 24h 以上），电流大，只能定性判断有无' if gas else 'DO 阈值靠板上电位器；AO 是模拟量'), kw, tag)
hdr_entry('SEN-030', S, '电容式土壤湿度传感器 v1.2（3P）', 'Capacitive soil moisture v1.2', 'https://lastminuteengineers.com/capacitive-soil-moisture-sensor-arduino/',
  'TLC555 振荡 + 电容测湿，AOUT 模拟（教程站：约 1.2–3V）', '3.3–5.5V（教程站）', 'AOUT 模拟，最高约 3V', ['GND', 'VCC', 'AOUT'], '教程站（GND VCC AOUT）',
  '板边要做防水；部分批次缺稳压芯片导致 3.3V 下不准', '电容式土壤湿度传感器 v1.2', 'Soil_v1.2')
hdr_entry('SEN-031', S, '水位传感器（3P，S + -）', 'Water level sensor', 'https://cdn-reichelt.de/documents/datenblatt/A300/SE045.pdf',
  '裸露梳状电极，模拟输出', '3.3–5V（教程站）', 'S 模拟输出随供电', ['SIG', 'VCC', 'GND'], 'Iduino SE045 资料（S + -）',
  '电极长期通电会电解腐蚀，只在测量时供电', '水位传感器 模块 S+-', 'WaterLevel')
hdr_entry('SEN-034', S, 'SW-420 振动传感器模块（3P）', 'SW-420 module', 'https://microcontrollerslab.com/sw-420-vibration-sensor-module-pinout-interfacing-arduino-features/',
  '振动开关 + 比较器，DO 输出', '3.3–5V（教程站）', 'DO 随供电', ['VCC', 'GND', 'DO'], '教程站（VCC GND D0）', '只能判断有无振动，不能测加速度', 'SW-420 振动传感器模块', 'SW-420')
hdr_entry('SEN-036', S, 'VS1838B 红外接收头（38kHz，3P）', 'VS1838B', 'https://www.electronicoscaldas.com/datasheet/VS1838B-M-WCON_Manual.pdf',
  '38kHz 红外遥控接收，OUT 低有效', '2.7–5.5V（商家资料）', 'OUT 随供电', ['OUT', 'GND', 'VCC'], '商家 VS1838B 资料（1 OUT、2 GND、3 VCC，球面朝自己）',
  '同外形的接收头脚序可能不同（如 VCC/GND 对调），买到后按资料核对；VCC 加 RC 滤波更稳', 'VS1838B 红外接收头', 'VS1838B',
  mount='直接插在底板 3P 排母上或焊在 3 个孔上（孔 1.0，引脚细，可直接焊）')
hdr_entry('SEN-037', S, 'A3144 霍尔开关模块（KY-003，3P）', 'KY-003 A3144', 'https://www.gotronic.fr/pj2-sen-ky003-manual-1932.pdf',
  'A3144 单极霍尔开关，开漏 NPN 低有效（Joy-IT 资料）', 'A3144 4.5–24V（资料）', '开漏输出，上拉到主控电压即可', ['GND', 'VCC', 'SIG'], 'Joy-IT KY-003 资料（丝印 - + S）',
  'A3144 最低 4.5V，3.3V 供电不可靠；输出开漏要上拉', 'KY-003 霍尔传感器 A3144', 'KY-003')
# ---------- 称重与电参量 ----------
hdr_entry('SEN-038', S, 'HX711 称重模块（底板 4P 数字口）', 'HX711 module', 'https://github.com/sparkfun/HX711-Load-Cell-Amplifier/blob/master/datasheets/hx711F_EN.pdf',
  '24 位 ADC，两线 DT/SCK（非 I2C），称重传感器接 E+ E- A- A+', 'VCC 2.6–5.5V（教程站）', 'DT/SCK 随供电', ['GND', 'DT', 'SCK', 'VCC'],
  '教程站（GND DT SCK VCC）；称重传感器 4 线直接焊在模块另一侧', '红板/绿板两种，部分绿板 E- 没接地需改；接线颜色按传感器说明', 'HX711 称重模块', 'HX711')
for sid, nm, pn, kw, rng in (('SEN-039', 'ACS712 电流模块 5A（3P）', 'ACS712-05B module', 'ACS712 5A 电流模块', '±5A，185mV/A'),
                             ('SEN-040', 'ACS712 电流模块 20A（3P）', 'ACS712-20A module', 'ACS712 20A 电流模块', '±20A，100mV/A')):
    hdr_entry(sid, S, nm, pn, 'https://www.allegromicro.com/en/products/sense/current-sensor-ics/zero-to-fifty-amp-integrated-conductor-sensor-ics/acs712',
      f'霍尔电流，{rng}，0A 时输出 VCC/2（教程站）', '4.5–5.5V（教程站）', 'OUT 0–5V 模拟，接 3.3V 主控 ADC 要分压', ['VCC', 'OUT', 'GND'],
      '教程站（VCC OUT GND，被测电流走模块螺钉端子）', '5V 供电零点 2.5V，3.3V ADC 测不到上半量程；小电流分辨率差，测 mA 级用 INA219', kw, 'ACS712_' + pn.split('-')[1][:3])
hdr_entry('SEN-041', S, 'INA219 电流电压模块（I2C，0.1Ω）', 'INA219 module', 'https://cdn-shop.adafruit.com/datasheets/ina219.pdf',
  'INA219，0–26V、约 ±3.2A（0.1Ω 分流），I2C 0x40（A0/A1 焊盘可改 0x41/0x44/0x45）', 'VCC 3–5.5V（教程站）', '随 VCC；板上上拉未核', ['VCC', 'GND', 'SCL', 'SDA'],
  '教程站（VCC GND SCL SDA，VIN+/VIN- 在模块端子上）', '被测电路和模块要共地；高边测量，VIN+ 接电源、VIN- 接负载', 'INA219 电流模块', 'INA219')
hdr_entry('SEN-042', S, '0–25V 电压检测模块（分压 5:1）', 'Voltage sensor 0-25V', 'https://components101.com/sensors/voltage-sensor-module',
  '30k/7.5k 分压，输出 = 输入/5（教程站）', '无需供电（纯电阻分压）', 'S 输出 = Vin/5；3.3V 主控只能测到约 16.5V', ['SIG', 'GND'],
  '教程站（S 接 ADC，- 接 GND，+ 未接）', '3.3V 主控满量程只有约 16.5V，测 25V 会超 ADC 量程', '0-25V 电压检测模块', 'VSENSE25', extra_notes='模块的 + 脚内部不接，底板只出 SIG、GND。')
# ---------- 定位与识别 ----------
hdr_entry('SEN-043', S, 'ATGM336H 北斗/GPS 定位模块（5P）', 'ATGM336H module', 'https://www.tinytronics.nl/product_files/002176_ATGM336H.pdf',
  '中科微 ATGM336H-5N，UART 9600，GPS+北斗', '3.3–5V（教程站）', 'TX/RX 电平以模块为准（多为 3.3V）', ['VCC', 'GND', 'TX', 'RX', 'PPS'],
  '教程站与商家资料；淘宝板脚数和顺序不一', '必须接天线，室内搜不到星；冷启动 30s 以上', 'ATGM336H GPS 北斗模块', 'ATGM336H')
hdr_entry('SEN-044', S, 'NEO-6M GPS 模块（GY-GPS6MV2，4P）', 'GY-GPS6MV2', 'https://content.u-blox.com/sites/default/files/products/documents/NEO-6_DataSheet_(GPS.G6-HW-09005).pdf',
  'u-blox NEO-6M，UART 9600（u-blox 规格书默认）', '3.3–5V（模块带 3.3V 稳压，教程站）', '教程站称逻辑脚耐 5V（未核）', ['VCC', 'RX', 'TX', 'GND'],
  '教程站（多数资料 VCC RX TX GND，也有资料写 VCC GND TX RX，对照丝印）', '市面不少是翻新/仿 NEO-6M；室内搜不到星', 'GY-GPS6MV2 NEO-6M', 'NEO-6M')
hdr_entry('SEN-045', S, 'RC522 RFID 读卡模块（13.56MHz，8P）', 'RC522 RFID module', 'https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf',
  'NXP MFRC522，SPI（模块默认）', '3.3V（VCC 不能接 5V）', '3.3V；教程站称 SPI 脚可承受 5V（未核）', ['SDA', 'SCK', 'MOSI', 'MISO', 'IRQ', 'GND', 'RST', '3V3'],
  '教程站（SDA SCK MOSI MISO IRQ GND RST 3.3V）', 'VCC 接 5V 会烧；SDA 脚其实是 SPI 的 CS', 'RC522 RFID 读卡模块', 'RC522')
hdr_entry('SEN-046', S, 'AS608 光学指纹模块（6P）', 'AS608 fingerprint', 'https://robu.in/wp-content/uploads/2020/08/AS608-Optical-Fingerprint-Sensor-Fingerprint-Module.pdf',
  'UART 57600（教程站）', '3.3–6V（教程站，各资料不一）', 'UART 3.3V/5V TTL（教程站）', ['VCC', 'GND', 'TX', 'RX', 'TOUCH', '3V3'],
  '教程站（资料之间线色和顺序有冲突，到货对照模块说明）', '线色各家不同，务必看商品说明；TOUCH 为手指感应输出', 'AS608 指纹模块', 'AS608')
# ---------- 时钟与存储 ----------
hdr_entry('SEN-047', S, 'DS3231 高精度时钟模块（ZS-042，6P）', 'ZS-042 DS3231', 'https://www.analog.com/media/en/technical-documentation/data-sheets/ds3231.pdf',
  'DS3231 I2C 0x68（固定）；板载 AT24C32 EEPROM 0x57（A0–A2 焊盘可改）', '2.3–5.5V（教程站）', '模块带上拉（阻值和上拉电压未核，见兼容性速查）', ['32K', 'SQW', 'SCL', 'SDA', 'VCC', 'GND'],
  '教程站（32K SQW SCL SDA VCC GND）', '0x68 与 MPU6050 冲突、0x57 与 MAX30102 冲突；ZS-042 的充电电路给 CR2032 充电，装不可充电纽扣电池要断开充电通路', 'DS3231 时钟模块 ZS-042', 'DS3231')
hdr_entry('SEN-048', S, 'DS1302 时钟模块（5P）', 'DS1302 module', 'https://www.mouser.com/datasheet/2/256/ds1302-1177771.pdf',
  'DS1302，三线（CLK DAT RST，非 I2C）', '2.0–5.5V（教程站）', '随供电', ['VCC', 'GND', 'CLK', 'DAT', 'RST'], '教程站（VCC GND CLK DAT RST）',
  '晶振精度差，走时误差比 DS3231 大；不是 I2C 不能挂总线', 'DS1302 时钟模块', 'DS1302')
hdr_entry('SEN-049', S, 'Micro SD 卡模块（SPI，6P）', 'Micro SD module', 'https://lastminuteengineers.com/arduino-micro-sd-card-module-tutorial/',
  'SPI 读写 TF 卡，板载稳压和电平转换（教程站）', '模块 VCC 3.3–5V（有的版本只接 5V，看稳压）', '板载电平转换（74LVC125 类）时 MISO 输出电平未核', ['GND', 'VCC', 'MISO', 'MOSI', 'SCK', 'CS'],
  '教程站（GND VCC MISO MOSI SCK CS）', '带电平转换的版本 MISO 不释放总线，与其他 SPI 设备共线可能冲突；卡要 FAT32', 'Micro SD 卡模块 SPI', 'MicroSD')

A = '执行器'
for sid, nm, trig in (('ACT-001', '1 路 5V 继电器模块（高电平触发）', '高电平触发'), ('ACT-002', '1 路 5V 继电器模块（低电平触发）', '低电平触发')):
    hdr_entry(sid, A, nm, f'1CH 5V relay module ({trig})', 'https://www.lcsc.com/product-detail/C35449.html',
      f'松乐 SRD-05VDC-SL-C 继电器 + 三极管驱动，{trig}；触点 10A 250VAC/30VDC（商家资料）', '5V，线圈约 70mA（SRD 线圈 70Ω，教程站）',
      '模块输入一般 3.3V 可驱动（未核，看驱动管和光耦）', ['VCC', 'GND', 'IN'], '教程站（VCC GND IN，负载接模块螺钉端子 COM NO NC）',
      '高/低电平触发两种外观很像，看丝印和商品选项；有的模块带跳线可切换；负载端是强电时注意绝缘', f'5V 继电器模块 1路 {trig}', f"Relay_{'H' if '高' in trig else 'L'}")
ENT.append(dict(id='ACT-003', category=A, name='松乐 SRD-05VDC-SL-C 5V 继电器（裸件，直插）', lcsc='C35449', datasheet_url='https://www.lcsc.com/product-detail/C35449.html',
  part_number='SRD-05VDC-SL-C', manufacturer='Songle（松乐）', alternatives='[]', alternatives_text='自己搭驱动嫌麻烦就用继电器模块（ACT-001/002）',
  key_params='SPDT，线圈 5V 约 70Ω/71mA，触点 10A 250VAC / 10A 30VDC（教程站转述规格书）', supply='线圈 5V', logic_level='不适用（需三极管驱动 + 续流二极管）',
  pin_count=5, pinout='按 KiCad 官方 SANYOU_SRD_Form_C 符号与封装：1=COM、2/5=线圈、3=NC、4=NO（以封装焊盘号为准，焊前对照实物底面标记）',
  pitch_mm='12.0（两线圈脚）', row_spacing_mm='12.2（线圈脚到触点脚）', lead_size_mm='图中标 2-1×0.4 扁脚和 2-Φ0.6 圆脚，哪几只为扁脚图上看不清；官方封装孔 1.0（线圈）/1.3（COM、触点）',
  body_mm='19.1 × 15.5 × 15.3 max（松乐规格书）', mount='卧装直插', seated_height_mm='15.3 max', pin1='1=COM：PCB 焊盘号 1，焊前对照继电器底面引脚图', kicad_symbol='Relay:SANYOU_SRD_Form_C',
  kicad_footprint='Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C',
  dim_source='松乐 SRD 规格书第 1 页 5. DIMENSION/DRILLING（dim_SRD_drilling.png，GitHub 公开转存）：线圈两脚距 12±0.05、COM 到线圈 2±0.05、线圈到触点 12.2±0.05；KiCad 官方 SANYOU SRD 封装各脚位与之相差 ≤0.05',
  level='C', pitfalls='线圈必须并联续流二极管（1N4148/1N4007，K 接 +）；单片机 IO 不能直接驱动线圈', polarized='否', lead_max_mm='',
  ring_min_mm='', notes='C 编号由搜索引擎收录的嘉立创/立创商品页（C35449，SRD-05VDC-SL-C）对应，云端未能接口核实，jlc.json 待本地补。定 C 级原因：引脚截面（扁脚/圆脚对应哪几只）图上看不清，NO/NC 对应 3/4 号焊盘按 KiCad 官方符号，焊前对照继电器底面接线图。',
  taobao_keyword='SRD-05VDC-SL-C 继电器', check_pads='2,5', pdf_keyword='SRD'))
for sid, nm, pn, url, key, cur, kw, tag in (
  ('ACT-004', 'SG90 9g 舵机（3 线）', 'SG90', 'https://handsontec.com/dataspecs/motor_fan/SG90-Servo.pdf', '180°，PWM 50Hz 1–2ms（资料）', '4.8–6V，负载 200–250mA，堵转 500–750mA（教程站）', 'SG90 舵机 9g', 'SG90'),
  ('ACT-005', 'MG996R 金属齿舵机（3 线）', 'MG996R', 'https://www.electronicoscaldas.com/datasheet/MG996R_Tower-Pro.pdf', '大扭矩金属齿，PWM 50Hz', '4.8–7.2V，堵转约 2.5A（教程站）', 'MG996R 舵机 金属齿', 'MG996R')):
    hdr_entry(sid, A, nm, pn, url, key, cur, 'PWM 信号 3.3V 一般可驱动（未核）', ['GND', 'VCC', 'PWM'],
      '舵机线色：棕/深灰=GND、红=VCC、橙=信号（教程站）', '舵机电源不能取自主控板 3.3V/5V 脚，单独供电并共地；多个舵机同时动作电流叠加', kw, tag,
      mount='底板焊 1×3 直排针，舵机 3P 杜邦头直接插（顺序 GND VCC PWM，与舵机线棕红橙一致）')
hdr_entry('ACT-006', A, '28BYJ-48 步进电机 + ULN2003 驱动板（控制口 6P）', '28BYJ-48 + ULN2003', 'https://www.ti.com/lit/ds/symlink/uln2003a.pdf',
  'ULN2003 达林顿阵列驱动 5 线 4 相步进电机', '电机电源 5V（教程站；12V 电机版另购）', 'IN1–IN4 3.3V 可驱动（ULN2003 输入，未核模块）', ['IN1', 'IN2', 'IN3', 'IN4', 'VCC', 'GND'],
  '教程站（IN1–IN4 + 电源两脚）', '电机长时间通电发热，空闲时把 IN 全拉低；步进顺序 IN1-IN3-IN2-IN4（教程站）', '28BYJ-48 步进电机 ULN2003 驱动板', 'ULN2003')
hdr_entry('ACT-007', A, 'TB6612FNG 双路电机驱动模块（控制口 8P）', 'TB6612FNG module', 'https://toshiba.semicon-storage.com/info/TB6612FNG_datasheet_en_20141001.pdf?did=10660&prodName=TB6612FNG',
  '双 H 桥，每路 1.2A 连续、3.2A 峰值；VM 4.5–13.5V，VCC 2.7–5.5V（教程站转述规格书）', 'VM 电机电源 + VCC 逻辑电源分开', '逻辑随 VCC（3.3V 主控就给 3.3V）', ['PWMA', 'AIN2', 'AIN1', 'STBY', 'BIN1', 'BIN2', 'PWMB', 'GND'],
  'SparkFun TB6612FNG 模块一侧排针顺序', 'STBY 必须拉高才工作；VM、VCC、电机输出另接，不在这排针上', 'TB6612FNG 电机驱动模块', 'TB6612',
  extra_notes='底板只出控制信号 8P，电源和电机线走模块另一排或端子。')
hdr_entry('ACT-008', A, 'L298N 双路电机驱动模块（控制口 7P）', 'L298N module', 'https://www.st.com/resource/en/datasheet/l298.pdf',
  'L298N 双 H 桥（ST 规格书：供电最高 46V、总电流 4A）；模块常标 5–35V', '电机电源 5–35V（模块资料），板载 5V 稳压可跳线', '输入 TTL，3.3V 一般可识别（未核）', ['ENA', 'IN1', 'IN2', 'IN3', 'IN4', 'ENB', 'GND'],
  '教程站（ENA IN1 IN2 IN3 IN4 ENB，电源和电机走螺钉端子）', 'L298N 压降大（约 2V），低压电机推不动，小车优先 TB6612；ENA/ENB 跳线帽拔掉才能 PWM 调速', 'L298N 电机驱动模块', 'L298N')
hdr_entry('ACT-009', A, 'DRV8833 双路电机驱动模块（控制口 6P）', 'DRV8833 module', 'https://www.ti.com/product/DRV8833',
  '双 H 桥，2.7–10.8V，1.5A RMS（TI 产品页）', 'VCC 2.7–10.8V（电机电源）', '输入 3.3V 可驱动（TI 规格书逻辑电平，未核模块）', ['IN1', 'IN2', 'IN3', 'IN4', 'EEP', 'GND'],
  '教程站（模块 12P：EEP OUT1-4 ULT IN1-4 VCC GND）', 'EEP（nSLEEP）要拉高才工作；电机电压最高 10.8V', 'DRV8833 电机驱动模块', 'DRV8833')
hdr_entry('ACT-010', A, 'DFPlayer Mini MP3 模块（底板控制口 7P）', 'DFPlayer Mini (DFR0299)', 'https://wiki.dfrobot.com/DFPlayer_Mini_SKU_DFR0299',
  'UART 9600 控制，TF 卡放 MP3；内置单声道功放直推 SPK1/SPK2', 'VCC 3.2–5V（DFRobot 官方）', 'UART 3.3V；RX 串 1k 电阻减少杂音（DFRobot wiki）', ['VCC', 'RX', 'TX', 'GND', 'SPK1', 'SPK2', 'BUSY'],
  'DFRobot DFR0299 wiki 引脚定义（底板只取常用 7 脚）', '直接插板要按实物量两排间距（未核，见 待确认.md）；喇叭接 SPK1/SPK2 不要接地；仿品多，TF 卡格式和文件名有要求', 'DFPlayer Mini MP3 模块', 'DFPlayer',
  extra_notes='这里是杜邦线方案；模块 16P 双排直插的排距云端未核。')

C = '通信'
hdr_entry('COM-001', C, 'HC-05 蓝牙串口模块（6P，主从一体）', 'HC-05 module', 'https://components101.com/wireless/hc-05-bluetooth-module',
  '蓝牙 2.0 SPP，主从可设，AT 指令（EN/KEY 进 AT 模式）', 'VCC 3.6–6V（教程站）', 'TXD/RXD 3.3V 电平（教程站）', ['STATE', 'RXD', 'TXD', 'GND', 'VCC', 'EN'],
  '教程站 HC-05 引脚（底板顺序与常见底板一致）', '5V 主控 TX 接模块 RXD 要分压；手机 iOS 不支持经典蓝牙 SPP', 'HC-05 蓝牙模块', 'HC-05')
hdr_entry('COM-002', C, 'HC-06 蓝牙串口模块（4P，从机）', 'HC-06 module', 'https://www.etechnophiles.com/hc06-pinout-specifications-datasheet/',
  '蓝牙 2.0 SPP，仅从机，默认 9600', '模块 VCC（底板版常标 3.6–6V，以商品为准）', 'TXD/RXD 3.3V', ['VCC', 'GND', 'TXD', 'RXD'], '教程站（VCC GND TXD RXD）',
  '只能当从机；5V 主控 TX 要分压', 'HC-06 蓝牙模块', 'HC-06')
hdr_entry('COM-003', C, 'ESP-01S Wi-Fi 模块（安信可，杜邦线 8P）', 'ESP-01S', 'https://www.taydaelectronics.com/datasheets/files/ESP-01S.pdf',
  'ESP8266，AT 固件串口透传或自编程；只有 GPIO0、GPIO2 可用', '3.0–3.6V，峰值约 300mA（安信可资料转述）', '3.3V，不耐 5V', ['GND', 'IO2', 'IO0', 'RXD', 'TXD', 'EN', 'RST', '3V3'],
  '安信可 ESP-01S 规格书引脚编号 1–8（Tayda 转存）', 'ESP-01S 是 2×4 排针，不能插这排 1×8：用杜邦线或买 ESP-01 转接座；3.3V 电源要能给 500mA 以上；IO0 上电拉低进下载', 'ESP-01S 安信可 WiFi 模块', 'ESP-01S')
ENT.append(dict(id='COM-004', category=C, name='NRF24L01 2.4G 无线模块（2×4 直插）', lcsc='', datasheet_url='https://cdn.sparkfun.com/assets/3/d/8/5/1/nRF24L01P_Product_Specification_1_0.pdf',
  part_number='NRF24L01 module', manufacturer='淘宝通用', alternatives='[]', alternatives_text='带 PA+LNA 天线版距离远、耗电大',
  key_params='nRF24L01+，SPI，2.4GHz', supply='1.9–3.6V，不能接 5V（教程站）', logic_level='3.3V（芯片输入脚耐 5V 与否以规格书为准，未核）',
  pin_count=8, pinout='1=GND、2=VCC、3=CE、4=CSN、5=SCK、6=MOSI、7=MISO、8=IRQ；单号一排、双号一排（Odd_Even，教程站常见图）',
  pitch_mm='2.54', row_spacing_mm='2.54', lead_size_mm='方针 0.64', body_mm='未核', mount='底板焊 2×4 排母，模块插上，天线朝板外',
  seated_height_mm='排母 8.5 + 模块', pin1='1=GND：PCB 方焊盘；模块上 1 脚一般是方焊盘', kicad_symbol='StudentHW:NRF24L01_Module_2x4',
  kicad_footprint='Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical',
  dim_source='底板为 2×4 排母，尺寸按 SKT-001 排母图纸（evidence/SKT-001/dim_PM254_1xN.png）；模块无厂家图',
  level='C', pitfalls='VCC 接 5V 直接烧；电源旁加 10µF+100nF，否则发射时复位；2×4 排序按模块背面丝印核对', polarized='是',
  lead_max_mm='0.64', ring_min_mm='0.35', check_pads='1,3',
  notes='规格书缺（淘宝模块，datasheet_url 为 Nordic nRF24L01+ 规格书）。脚序为教程站常见图，二手资料，到货对照丝印。环宽：排母焊盘 1.7、孔 1.0，按 0.35 放宽。',
  taobao_keyword='NRF24L01 无线模块 2.4G', price='未查（淘宝需登录）', stock='淘宝（未核实）', evidence_extra=['evidence/SKT-001/dim_PM254_1xN.png']))
hdr_entry('COM-005', C, 'MAX485 TTL 转 RS485 模块（控制口 6P）', 'MAX485 module', 'https://www.analog.com/media/en/technical-documentation/data-sheets/MAX1487-MAX491.pdf',
  'MAX485 半双工，最高 2.5Mbps（ADI 规格书）；A/B 走模块螺钉端子', '5V（ADI 规格书单 5V 供电）', '5V 器件；RO 输出 5V，3.3V 主控要分压或换 MAX3485', ['VCC', 'GND', 'RO', 'RE', 'DE', 'DI'],
  '教程站（RO RE DE DI / VCC B A GND 两排）', '3.3V 系统优先 MAX3485 版本；RE、DE 可并在一起由一个 IO 控制收发', 'MAX485 模块 TTL转485', 'MAX485')

P = '电源模块'
off_entry('PMD-001', P, 'TP4056 Type-C 锂电充电模块（带保护，不上板）', 'TP4056 + DW01A module', 'https://datasheet.lcsc.com/lcsc/1809261820_TOPPOWER-Nanjing-Extension-Microelectronics-TP4056-42-ESOP8_C16581.pdf',
  'TP4056 线性充电 4.2V，R_PROG 1.2k 对应 1A；DW01A + 8205A 保护（商家资料）', 'Type-C 5V 输入', '不适用',
  '焊盘 IN+ IN-（或 Type-C）、B+ B-（接电池）、OUT+ OUT-（经保护后的输出）', '商家资料（TP4056 Type-C 带保护板）',
  '负载要接 OUT+/OUT-（带保护），不要接 B+/B-；1A 充电模块很烫，小电池要把 R_PROG 改大', 'TP4056 Type-C 充电模块 带保护',
  '不上板：模块用导线或 2P 端子（TERM-001/XH）连底板，电池接 BAT-001 电池座', alt='不带保护版（PMD-002）')
off_entry('PMD-002', P, 'TP4056 Type-C 锂电充电模块（不带保护，不上板）', 'TP4056 module (no protection)', 'https://datasheet.lcsc.com/lcsc/1809261820_TOPPOWER-Nanjing-Extension-Microelectronics-TP4056-42-ESOP8_C16581.pdf',
  'TP4056 线性充电 4.2V，只有 B+ B-', 'Type-C 5V 输入', '不适用', '焊盘 IN+ IN-（或 Type-C）、B+ B-', '商家资料',
  '规范 3.3 节：锂电必须带保护，用这个版本时电池本身要带保护板（PMD-006）', 'TP4056 Type-C 充电模块 不带保护',
  '不上板：导线或端子连接', alt='带保护版（PMD-001）')
off_entry('PMD-003', P, 'MP1584 小体积降压模块（3A，不上板）', 'MP1584EN buck module', 'https://www.mouser.com/datasheet/2/277/MP1584_r1.0-779241.pdf',
  'MP1584EN，输入 4.5–28V，输出 0.8–20V 可调，最大 3A，22×17×4.3mm（商家资料）', '输入 4.5–28V', '不适用', 'IN+ IN- OUT+ OUT- 四个焊盘', '商家资料',
  '出厂电压随机，接负载前先用万用表调好；3A 是峰值，长期 1.5A 以下', 'MP1584 降压模块 3A 可调', '不上板：四根导线或排针焊在底板 4 个孔上（孔距按实物量）')
off_entry('PMD-004', P, 'LM2596 降压模块（3A，不上板）', 'LM2596 buck module', 'https://www.ti.com/product/LM2596',
  'LM2596-ADJ，输入 4–40V，输出 1.25–37V，3A（商家资料，不同版本尺寸差别大）', '输入 4–40V', '不适用', 'IN+ IN- OUT+ OUT-（有的带数显）', '商家资料',
  '150kHz 开关频率，纹波比 MP1584 大；版本多（43×21 小板、66×36 数显板），开孔按实物', 'LM2596 降压模块', '不上板：导线连接')
off_entry('PMD-005', P, 'MT3608 升压模块（2A，不上板）', 'MT3608 boost module', 'https://components101.com/sites/default/files/component_datasheet/MT3608-Step-Up-Power-Module-Datasheet.pdf',
  'MT3608，输入 2–24V，输出可调最高 28V，最大 2A，37.2×17.2×14mm（商家资料）', '输入 2–24V', '不适用', 'VIN+ VIN- VOUT+ VOUT-', '商家资料',
  '升压后输入电流是输出电流的数倍，锂电升 5V 时电池电流大；空载先调电压', 'MT3608 升压模块', '不上板：导线连接')
off_entry('PMD-006', P, '18650 锂电池（带保护板，不上板）', '18650 Li-ion with protection', 'https://www.lcsc.com/product-detail/C5290176.html',
  '单节 3.7V（满电 4.2V），带保护板版本', '不适用', '不适用', '正负极装入 BAT-001 电池座', '规范 3.3 节',
  '带保护板的电池比裸电芯长约 2–3mm，先确认电池座放得下；不买"大容量"虚标电池', '18650 锂电池 带保护板 尖头',
  '不上板：装在 BAT-001（18650 电池座）里', notes_extra='datasheet_url 为 BAT-001 电池座的立创页（电池本身是淘宝商品，无规格书）。')

SW = '开关'
# ---------- 输出 ----------
ORDER = ['id', 'category', 'name', 'lcsc', 'datasheet_url', 'part_number', 'manufacturer', 'alternatives', 'alternatives_text', 'key_params',
         'supply', 'logic_level', 'pin_count', 'pinout', 'pitch_mm', 'row_spacing_mm', 'lead_size_mm', 'body_mm', 'mount', 'seated_height_mm',
         'pin1', 'kicad_symbol', 'kicad_footprint', 'dim_source', 'level', 'pitfalls', 'notes', 'taobao_keyword', 'price', 'stock',
         'polarized', 'lead_max_mm', 'ring_min_mm', 'check_pads', 'pdf_keyword', 'evidence_extra']
out = ['# 第三批（云端 2026-10-02）：传感器、执行器、通信、电源模块、12×12 轻触开关。',
       '# 云端拿不到淘宝商品页和厂家尺寸图，模块一律 C 级：底板只放带脚名丝印的排针，杜邦线按名字对接，',
       '# 脚序、电压等写明来源（多为教程站等二手资料），到货对照模块丝印。做不到的写在 待确认.md。', '']
for e in ENT:
    out.append(f"- id: {e['id']}")
    for k in ORDER[1:]:
        if k not in e: continue
        v = e[k]
        if k == 'evidence_extra':
            out.append(f"  {k}: [{', '.join(v)}]"); continue
        if k == 'alternatives':
            out.append(f"  {k}: []"); continue
        if k == 'pin_count':
            out.append(f"  {k}: {v}"); continue
        out.append(f"  {k}: {q(v)}")
    out.append('')
open(ROOT + '/src/b3_modules.yaml', 'w', encoding='utf-8').write('\n'.join(out))

md = ['"""第三批模块的底板排针封装和符号（由第三批建库脚本一次生成，之后手工维护）。',
      '每个封装 = 一排排针，丝印逐脚印出脚名、顶上印模块名；模块用杜邦线按脚名对接。"""', '', 'P = 2.54', '', '',
      'HDRS = [']
for fp, names, descr, label, pitch in HDR:
    md.append(f'    ({fp!r}, {names!r}, {descr!r}, {label!r}, {pitch}),')
md += [']', '', '',
       'SYMS = [',
       "    ('HLK-LD6002_8P', 'StudentHW:PinSocket_1x08_P2.00mm_Vertical', '海凌科 HLK-LD6002 呼吸心率雷达 8P（2.0 排母）',",
       "     ['3V3', 'GND', 'P19', 'TX2', 'AIO1', 'SCL0', 'TX0', 'RX0']),",
       "    ('HLK-LD6002C_8P', 'StudentHW:PinSocket_1x08_P2.00mm_Vertical', '海凌科 HLK-LD6002C 雷达 8P（2.0 排母，外观同 LD6002）',",
       "     ['3V3', 'GND', 'P19', 'TX2', 'AIO1', 'SCL0', 'TX0', 'RX0']),",
       "    ('NRF24L01_Module_2x4', 'Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical', 'NRF24L01 模块 2×4（单号一排、双号一排）',",
       "     ['GND', 'VCC', 'CE', 'CSN', 'SCK', 'MOSI', 'MISO', 'IRQ']),",
       ']', '', '',
       'def register(add, sym):',
       '    for fp, names, descr, label, pitch in HDRS:',
       '        n = len(names)',
       '        add(fp, descr=descr,',
       '            board=(-pitch / 2, -pitch / 2, pitch / 2, (n - 1) * pitch + pitch / 2),',
       '            rows=[{"start": (0, 0), "dir": "down", "names": names, "first": 1, "side": "right", "n": n, "pitch": pitch}],',
       '            labels=[(label, 0, -pitch / 2 - 1.2, 0)],',
       '            height="底板排针，模块用杜邦线连接（不插板）",',
       '            sym_groups=[[0]])',
       '    for name, fp, descr, names in SYMS:',
       '        sym(name, fp, descr, [(str(i + 1), nm) for i, nm in enumerate(names)])',
       '']
open(ROOT + '/tools/module_defs_b3.py', 'w', encoding='utf-8').write('\n'.join(md))
print(len(ENT), 'entries', len(HDR), 'header footprints')
