"""第三批模块的底板排针封装和符号（由第三批建库脚本一次生成，之后手工维护）。
每个封装 = 一排排针，丝印逐脚印出脚名、顶上印模块名；模块用杜邦线按脚名对接。"""

P = 2.54


HDRS = [
    # 第二批补充（杜邦线连接的显示模块）
    ('Module_Hdr_PCF8574_LCD_I2C_4P', ['GND', 'VCC', 'SDA', 'SCL'], 'LCD1602/2004 的 PCF8574 I2C 转接板接口：底板排针，丝印印脚名', 'LCD_I2C', 2.54),
    ('Module_Hdr_TM1637_4P', ['CLK', 'DIO', 'VCC', 'GND'], 'TM1637 4 位数码管模块接口：底板排针，丝印印脚名', 'TM1637', 2.54),
    ('Module_Hdr_MAX7219_5P', ['VCC', 'GND', 'DIN', 'CS', 'CLK'], 'MAX7219 8×8 点阵模块输入端接口：底板排针，丝印印脚名', 'MAX7219', 2.54),
    ('Module_Hdr_DHT11_3P', ['VCC', 'DATA', 'GND'], 'DHT11 温湿度模块（3P 板）：底板排针，丝印印脚名（VCC DATA GND）', 'DHT11', 2.54),
    ('Module_Hdr_DHT22_4P', ['VDD', 'DATA', 'NC', 'GND'], 'DHT22 / AM2302 温湿度传感器（4P）：底板排针，丝印印脚名（VDD DATA NC GND）', 'DHT22', 2.54),
    ('Module_Hdr_AHT20_4P', ['VIN', 'GND', 'SCL', 'SDA'], 'AHT20 温湿度模块（I2C 4P）：底板排针，丝印印脚名（VIN GND SCL SDA）', 'AHT20', 2.54),
    ('Module_Hdr_AHT20_BMP280_4P', ['VCC', 'GND', 'SCL', 'SDA'], 'AHT20 + BMP280 温湿度气压二合一模块（I2C 4P）：底板排针，丝印印脚名（VCC GND SCL SDA）', 'AHT20_BMP280', 2.54),
    ('Module_Hdr_SHT30_6P', ['VIN', 'GND', 'SCL', 'SDA', 'ADR', 'ALR'], 'SHT30 温湿度模块（GY-SHT30-D，I2C）：底板排针，丝印印脚名（VIN GND SCL SDA ADR ALR）', 'SHT30', 2.54),
    ('Module_Hdr_GY-906_4P', ['VIN', 'GND', 'SCL', 'SDA'], 'MLX90614 红外测温模块（GY-906，I2C）：底板排针，丝印印脚名（VIN GND SCL SDA）', 'GY-906', 2.54),
    ('Module_Hdr_MAX30102_7P', ['VIN', 'SCL', 'SDA', 'INT', 'IRD', 'RD', 'GND'], 'MAX30102 心率血氧模块（单排 7P 紫板）：底板排针，丝印印脚名（VIN SCL SDA INT IRD RD GND）', 'MAX30102', 2.54),
    ('Module_Hdr_PulseSensor_3P', ['SIG', 'VCC', 'GND'], 'PulseSensor 光电脉搏传感器（3 线）：底板排针，丝印印脚名（SIG VCC GND）', 'PulseSensor', 2.54),
    ('Module_Hdr_AD8232_6P', ['GND', '3.3V', 'OUTPUT', 'LO-', 'LO+', 'SDN'], 'AD8232 单导联心电模块（6P）：底板排针，丝印印脚名（GND 3.3V OUTPUT LO- LO+ SDN）', 'AD8232', 2.54),
    ('Module_Hdr_GY-521_8P', ['VCC', 'GND', 'SCL', 'SDA', 'XDA', 'XCL', 'AD0', 'INT'], 'MPU6050 六轴模块（GY-521，8P）：底板排针，丝印印脚名（VCC GND SCL SDA XDA XCL AD0 INT）', 'GY-521', 2.54),
    ('Module_Hdr_GY-291_8P', ['GND', 'VCC', 'CS', 'INT1', 'INT2', 'SDO', 'SDA', 'SCL'], 'ADXL345 三轴加速度模块（GY-291，8P）：底板排针，丝印印脚名（GND VCC CS INT1 INT2 SDO SDA SCL）', 'GY-291', 2.54),
    ('Module_Hdr_HC-SR501_3P', ['VCC', 'OUT', 'GND'], 'HC-SR501 人体红外模块（3P）：底板排针，丝印印脚名（VCC OUT GND）', 'HC-SR501', 2.54),
    ('Module_Hdr_AM312_3P', ['VCC', 'OUT', 'GND'], 'AM312 迷你人体红外模块（3P）：底板排针，丝印印脚名（VCC OUT GND）', 'AM312', 2.54),
    ('Module_Hdr_HC-SR04_4P', ['VCC', 'TRIG', 'ECHO', 'GND'], 'HC-SR04 超声波测距模块（5V，4P）：底板排针，丝印印脚名（VCC TRIG ECHO GND）', 'HC-SR04', 2.54),
    ('Module_Hdr_HC-SR04P_4P', ['VCC', 'TRIG', 'ECHO', 'GND'], 'HC-SR04P 超声波测距模块（3.3–5V，4P）：底板排针，丝印印脚名（VCC TRIG ECHO GND）', 'HC-SR04P', 2.54),
    ('Module_Hdr_GY-530_6P', ['VIN', 'GND', 'SCL', 'SDA', 'GPIO1', 'XSHUT'], 'VL53L0X 激光测距模块（GY-530，6P）：底板排针，丝印印脚名（VIN GND SCL SDA GPIO1 XSHUT）', 'GY-530', 2.54),
    ('Module_Hdr_RCWL-0516_5P', ['3V3', 'GND', 'OUT', 'VIN', 'CDS'], 'RCWL-0516 微波雷达感应模块（5P）：底板排针，丝印印脚名（3V3 GND OUT VIN CDS）', 'RCWL-0516', 2.54),
    ('Module_Hdr_LD2410C_5P', ['TX', 'RX', 'OUT', 'GND', 'VCC'], '海凌科 HLK-LD2410C 24GHz 人体存在雷达（2.54 5P）：底板排针，丝印印脚名（TX RX OUT GND VCC）', 'LD2410C', 2.54),
    ('Module_Hdr_GY-302_5P', ['VCC', 'GND', 'SCL', 'SDA', 'ADDR'], 'BH1750 光照模块（GY-302，5P）：底板排针，丝印印脚名（VCC GND SCL SDA ADDR）', 'GY-302', 2.54),
    ('Module_Hdr_LDR_LM393_4P', ['VCC', 'GND', 'DO', 'AO'], '光敏电阻模块（LM393，4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'LDR_LM393', 2.54),
    ('Module_Hdr_Sound_4P', ['VCC', 'GND', 'DO', 'AO'], '声音传感器模块（KY-038 类，4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'Sound', 2.54),
    ('Module_Hdr_Flame_4P', ['VCC', 'GND', 'DO', 'AO'], '火焰传感器模块（LM393，4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'Flame', 2.54),
    ('Module_Hdr_Rain_4P', ['VCC', 'GND', 'DO', 'AO'], '雨滴传感器模块（4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'Rain', 2.54),
    ('Module_Hdr_MQ-2_4P', ['VCC', 'GND', 'DO', 'AO'], 'MQ-2 烟雾/可燃气体模块（4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'MQ-2', 2.54),
    ('Module_Hdr_MQ-135_4P', ['VCC', 'GND', 'DO', 'AO'], 'MQ-135 空气质量模块（4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'MQ-135', 2.54),
    ('Module_Hdr_TCRT5000_4P', ['VCC', 'GND', 'DO', 'AO'], 'TCRT5000 红外反射/循迹模块（4P）：底板排针，丝印印脚名（VCC GND DO AO）', 'TCRT5000', 2.54),
    ('Module_Hdr_Soil_v1.2_3P', ['GND', 'VCC', 'AOUT'], '电容式土壤湿度传感器 v1.2（3P）：底板排针，丝印印脚名（GND VCC AOUT）', 'Soil_v1.2', 2.54),
    ('Module_Hdr_WaterLevel_3P', ['SIG', 'VCC', 'GND'], '水位传感器（3P，S + -）：底板排针，丝印印脚名（SIG VCC GND）', 'WaterLevel', 2.54),
    ('Module_Hdr_SW-420_3P', ['VCC', 'GND', 'DO'], 'SW-420 振动传感器模块（3P）：底板排针，丝印印脚名（VCC GND DO）', 'SW-420', 2.54),
    ('Module_Hdr_VS1838B_3P', ['OUT', 'GND', 'VCC'], 'VS1838B 红外接收头（38kHz，3P）：底板排针，丝印印脚名（OUT GND VCC）', 'VS1838B', 2.54),
    ('Module_Hdr_KY-003_3P', ['GND', 'VCC', 'SIG'], 'A3144 霍尔开关模块（KY-003，3P）：底板排针，丝印印脚名（GND VCC SIG）', 'KY-003', 2.54),
    ('Module_Hdr_HX711_4P', ['GND', 'DT', 'SCK', 'VCC'], 'HX711 称重模块（底板 4P 数字口）：底板排针，丝印印脚名（GND DT SCK VCC）', 'HX711', 2.54),
    ('Module_Hdr_ACS712_05B_3P', ['VCC', 'OUT', 'GND'], 'ACS712 电流模块 5A（3P）：底板排针，丝印印脚名（VCC OUT GND）', 'ACS712_05B', 2.54),
    ('Module_Hdr_ACS712_20A_3P', ['VCC', 'OUT', 'GND'], 'ACS712 电流模块 20A（3P）：底板排针，丝印印脚名（VCC OUT GND）', 'ACS712_20A', 2.54),
    ('Module_Hdr_INA219_4P', ['VCC', 'GND', 'SCL', 'SDA'], 'INA219 电流电压模块（I2C，0.1Ω）：底板排针，丝印印脚名（VCC GND SCL SDA）', 'INA219', 2.54),
    ('Module_Hdr_VSENSE25_2P', ['SIG', 'GND'], '0–25V 电压检测模块（分压 5:1）：底板排针，丝印印脚名（SIG GND）', 'VSENSE25', 2.54),
    ('Module_Hdr_ATGM336H_5P', ['VCC', 'GND', 'TX', 'RX', 'PPS'], 'ATGM336H 北斗/GPS 定位模块（5P）：底板排针，丝印印脚名（VCC GND TX RX PPS）', 'ATGM336H', 2.54),
    ('Module_Hdr_NEO-6M_4P', ['VCC', 'RX', 'TX', 'GND'], 'NEO-6M GPS 模块（GY-GPS6MV2，4P）：底板排针，丝印印脚名（VCC RX TX GND）', 'NEO-6M', 2.54),
    ('Module_Hdr_RC522_8P', ['SDA', 'SCK', 'MOSI', 'MISO', 'IRQ', 'GND', 'RST', '3V3'], 'RC522 RFID 读卡模块（13.56MHz，8P）：底板排针，丝印印脚名（SDA SCK MOSI MISO IRQ GND RST 3V3）', 'RC522', 2.54),
    ('Module_Hdr_AS608_6P', ['VCC', 'GND', 'TX', 'RX', 'TOUCH', '3V3'], 'AS608 光学指纹模块（6P）：底板排针，丝印印脚名（VCC GND TX RX TOUCH 3V3）', 'AS608', 2.54),
    ('Module_Hdr_DS3231_6P', ['32K', 'SQW', 'SCL', 'SDA', 'VCC', 'GND'], 'DS3231 高精度时钟模块（ZS-042，6P）：底板排针，丝印印脚名（32K SQW SCL SDA VCC GND）', 'DS3231', 2.54),
    ('Module_Hdr_DS1302_5P', ['VCC', 'GND', 'CLK', 'DAT', 'RST'], 'DS1302 时钟模块（5P）：底板排针，丝印印脚名（VCC GND CLK DAT RST）', 'DS1302', 2.54),
    ('Module_Hdr_MicroSD_6P', ['GND', 'VCC', 'MISO', 'MOSI', 'SCK', 'CS'], 'Micro SD 卡模块（SPI，6P）：底板排针，丝印印脚名（GND VCC MISO MOSI SCK CS）', 'MicroSD', 2.54),
    ('Module_Hdr_Relay_H_3P', ['VCC', 'GND', 'IN'], '1 路 5V 继电器模块（高电平触发）：底板排针，丝印印脚名（VCC GND IN）', 'Relay_H', 2.54),
    ('Module_Hdr_Relay_L_3P', ['VCC', 'GND', 'IN'], '1 路 5V 继电器模块（低电平触发）：底板排针，丝印印脚名（VCC GND IN）', 'Relay_L', 2.54),
    ('Module_Hdr_SG90_3P', ['GND', 'VCC', 'PWM'], 'SG90 9g 舵机（3 线）：底板排针，丝印印脚名（GND VCC PWM）', 'SG90', 2.54),
    ('Module_Hdr_MG996R_3P', ['GND', 'VCC', 'PWM'], 'MG996R 金属齿舵机（3 线）：底板排针，丝印印脚名（GND VCC PWM）', 'MG996R', 2.54),
    ('Module_Hdr_ULN2003_6P', ['IN1', 'IN2', 'IN3', 'IN4', 'VCC', 'GND'], '28BYJ-48 步进电机 + ULN2003 驱动板（控制口 6P）：底板排针，丝印印脚名（IN1 IN2 IN3 IN4 VCC GND）', 'ULN2003', 2.54),
    ('Module_Hdr_TB6612_8P', ['PWMA', 'AIN2', 'AIN1', 'STBY', 'BIN1', 'BIN2', 'PWMB', 'GND'], 'TB6612FNG 双路电机驱动模块（控制口 8P）：底板排针，丝印印脚名（PWMA AIN2 AIN1 STBY BIN1 BIN2 PWMB GND）', 'TB6612', 2.54),
    ('Module_Hdr_L298N_7P', ['ENA', 'IN1', 'IN2', 'IN3', 'IN4', 'ENB', 'GND'], 'L298N 双路电机驱动模块（控制口 7P）：底板排针，丝印印脚名（ENA IN1 IN2 IN3 IN4 ENB GND）', 'L298N', 2.54),
    ('Module_Hdr_DRV8833_6P', ['IN1', 'IN2', 'IN3', 'IN4', 'EEP', 'GND'], 'DRV8833 双路电机驱动模块（控制口 6P）：底板排针，丝印印脚名（IN1 IN2 IN3 IN4 EEP GND）', 'DRV8833', 2.54),
    ('Module_Hdr_DFPlayer_7P', ['VCC', 'RX', 'TX', 'GND', 'SPK1', 'SPK2', 'BUSY'], 'DFPlayer Mini MP3 模块（底板控制口 7P）：底板排针，丝印印脚名（VCC RX TX GND SPK1 SPK2 BUSY）', 'DFPlayer', 2.54),
    ('Module_Hdr_HC-05_6P', ['STATE', 'RXD', 'TXD', 'GND', 'VCC', 'EN'], 'HC-05 蓝牙串口模块（6P，主从一体）：底板排针，丝印印脚名（STATE RXD TXD GND VCC EN）', 'HC-05', 2.54),
    ('Module_Hdr_HC-06_4P', ['VCC', 'GND', 'TXD', 'RXD'], 'HC-06 蓝牙串口模块（4P，从机）：底板排针，丝印印脚名（VCC GND TXD RXD）', 'HC-06', 2.54),
    ('Module_Hdr_ESP-01S_8P', ['GND', 'IO2', 'IO0', 'RXD', 'TXD', 'EN', 'RST', '3V3'], 'ESP-01S Wi-Fi 模块（安信可，杜邦线 8P）：底板排针，丝印印脚名（GND IO2 IO0 RXD TXD EN RST 3V3）', 'ESP-01S', 2.54),
    ('Module_Hdr_MAX485_6P', ['VCC', 'GND', 'RO', 'RE', 'DE', 'DI'], 'MAX485 TTL 转 RS485 模块（控制口 6P）：底板排针，丝印印脚名（VCC GND RO RE DE DI）', 'MAX485', 2.54),
]


SYMS = [
    ('HLK-LD6002_8P', 'StudentHW:PinSocket_1x08_P2.00mm_Vertical', '海凌科 HLK-LD6002 呼吸心率雷达 8P（2.0 排母）',
     ['3V3', 'GND', 'P19', 'TX2', 'AIO1', 'SCL0', 'TX0', 'RX0']),
    ('HLK-LD6002C_8P', 'StudentHW:PinSocket_1x08_P2.00mm_Vertical', '海凌科 HLK-LD6002C 雷达 8P（2.0 排母，外观同 LD6002）',
     ['3V3', 'GND', 'P19', 'TX2', 'AIO1', 'SCL0', 'TX0', 'RX0']),
    ('NRF24L01_Module_2x4', 'Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical', 'NRF24L01 模块 2×4（单号一排、双号一排）',
     ['GND', 'VCC', 'CE', 'CSN', 'SCK', 'MOSI', 'MISO', 'IRQ']),
]


def register(add, sym):
    for fp, names, descr, label, pitch in HDRS:
        n = len(names)
        add(fp, descr=descr,
            board=(-pitch / 2, -pitch / 2, pitch / 2, (n - 1) * pitch + pitch / 2),
            rows=[{"start": (0, 0), "dir": "down", "names": names, "first": 1, "side": "right", "n": n, "pitch": pitch}],
            labels=[(label, 0, -pitch / 2 - 1.2, 0)],
            height="底板排针，模块用杜邦线连接（不插板）",
            sym_groups=[[0]])
    for name, fp, descr, names in SYMS:
        sym(name, fp, descr, [(str(i + 1), nm) for i, nm in enumerate(names)])
