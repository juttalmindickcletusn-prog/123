"""模块（核心板、显示屏等）的几何与引脚定义。gen_modules.py 用它生成封装和符号。

坐标约定（与 KiCad 封装一致）：单位 mm，1 脚在 (0, 0)，x 向右，y 向下，从模块正面（元件面朝上）看。
- board：模块 PCB 外框 (x0, y0, x1, y1)
- overhang：伸出外框的部分（如天线），只画在 Fab/courtyard
- holes：模块安装孔 (x, y, 直径)，只画在 Fab 层，不钻孔
- rows：每排引脚 {"start": (x, y), "dir": "down"/"up"/"right"/"left", "names": [...], "first": 起始脚号, "side": 名字印在哪侧}
  脚号按逆时针（DIP 习惯）：第一排 1..n，第二排接着编号
- sym_groups：符号左右两侧放哪几排（行索引）
每条都写了尺寸来源，证据图在 evidence/<编号>/。
"""
from __future__ import annotations

P = 2.54


def col(n, names, x=0.0, y=0.0, d="down", first=1, side="left"):
    return {"start": (x, y), "dir": d, "names": names, "first": first, "side": side, "n": n}


MODULES = {}


def add(name, **kw):
    kw["name"] = name
    MODULES[name] = kw


# ---------------- 主控板 ----------------
# 立创 ESP32-S3R8N8 核心板：厂家图 51.66×20.32，排距 17.78，两排 1×20（V1.1 实测排距 17.78）
_s3_left = ["GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "GND", "GPIO7", "GPIO8", "GPIO9", "GPIO10",
            "GPIO11", "GPIO12", "GPIO13", "GPIO14", "RST", "3V3", "3V3", "3V3", "GND"]
_s3_right_top_down = ["GPIO46", "GPIO45", "GPIO42", "GPIO41", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "GND", "GPIO21",
                      "GPIO40", "GPIO39", "GPIO38", "GPIO47", "GPIO48", "BOOT_GPIO0", "5V", "5V", "5V", "GND"]
add("Module_LCKFB_ESP32S3R8N8",
    descr="立创·ESP32S3R8N8 核心板 40P，两排 1×20 2.54，排距 17.78；天线在 1 脚一端，Type-C 在另一端",
    board=(-1.27, -1.70, 17.78 + 1.27, 48.26 + 1.70),
    rows=[col(20, _s3_left, 0, 0, "down", 1, "left"),
          col(20, list(reversed(_s3_right_top_down)), 17.78, 48.26, "up", 21, "right")],
    labels=[("ANT", 8.89, -3.2, 0), ("USB-C", 8.89, 51.4, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# 立创·地猛星 STM32F103C8T6 / 经典蓝色药丸：53.34×22.86，两排 1×20，排距 15.24（图上未标，按 2.54 网格量得）
_bp_bottom = ["PB12", "PB13", "PB14", "PB15", "PA8", "PA9", "PA10", "PA11", "PA12", "PA15", "PB3", "PB4", "PB5",
              "PB6", "PB7", "PB8", "PB9", "5V", "GND", "3V3"]
_bp_top_left_right = ["GND", "GND", "3V3", "RST", "PB11", "PB10", "PB1", "PB0", "PA7", "PA6", "PA5", "PA4", "PA3",
                      "PA2", "PA1", "PA0", "PC15", "PC14", "PC13", "VBAT"]
add("Module_STM32F103C8T6_BluePill",
    descr="STM32F103C8T6 核心板（蓝色药丸/立创地猛星），两排 1×20 2.54，排距 15.24；USB 在左端",
    board=(-2.54, -15.24 - 3.81, 48.26 + 2.54, 3.81),
    rows=[col(20, _bp_bottom, 0, 0, "right", 1, "bottom"),
          col(20, list(reversed(_bp_top_left_right)), 48.26, -15.24, "left", 21, "top")],
    labels=[("USB", -4.6, -7.62, 90)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# 乐鑫 ESP32-S3-DevKitC-1 v1.1：厂家尺寸图 25.40×62.74，排距 22.86，2×22；末脚离 USB 端 8.00；天线伸出板外约 6
_dkc1_j1 = ["3V3", "3V3", "RST", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "GPIO8",
            "GPIO3", "GPIO46", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14", "5V", "GND"]
_dkc1_j3 = ["GND", "TX_GPIO43", "RX_GPIO44", "GPIO1", "GPIO2", "GPIO42", "GPIO41", "GPIO40", "GPIO39", "GPIO38",
            "GPIO37", "GPIO36", "GPIO35", "GPIO0", "GPIO45", "GPIO48", "GPIO47", "GPIO21", "GPIO20", "GPIO19", "GND", "GND"]
add("Module_ESP32-S3-DevKitC-1",
    descr="乐鑫 ESP32-S3-DevKitC-1，2×22 2.54，排距 22.86；J1 在左（1 脚 3V3 靠天线），J3 在右；天线伸出板外",
    board=(-1.27, -1.40, 22.86 + 1.27, 53.34 + 8.00),
    overhang=(3.68, -1.40 - 6.2, 3.68 + 18.0, -1.40),
    rows=[col(22, _dkc1_j1, 0, 0, "down", 1, "left"),
          col(22, list(reversed(_dkc1_j3)), 22.86, 53.34, "up", 23, "right")],
    labels=[("ANT", 11.43, -9.0, 0), ("USB", 11.43, 63.2, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# 乐鑫 ESP32-DevKitC V4（38P）：厂家尺寸图 27.94×48.26，排距 25.40，2×19；天线伸出 6.04，宽 18
_dkc4_j2 = ["3V3", "EN", "VP_GPIO36", "VN_GPIO39", "GPIO34", "GPIO35", "GPIO32", "GPIO33", "GPIO25", "GPIO26",
            "GPIO27", "GPIO14", "GPIO12", "GND", "GPIO13", "SD2_GPIO9", "SD3_GPIO10", "CMD_GPIO11", "5V"]
_dkc4_j3 = ["GND", "GPIO23", "GPIO22", "TX_GPIO1", "RX_GPIO3", "GPIO21", "GND", "GPIO19", "GPIO18", "GPIO5", "GPIO17",
            "GPIO16", "GPIO4", "GPIO0", "GPIO2", "GPIO15", "SD1_GPIO8", "SD0_GPIO7", "CLK_GPIO6"]
add("Module_ESP32-DevKitC-V4_38P",
    descr="乐鑫 ESP32-DevKitC V4（38P），2×19 2.54，排距 25.40；J2 在左（1 脚 3V3 靠天线）；天线伸出板外 6.04",
    board=(-1.27, -1.30, 25.40 + 1.27, 45.72 + 1.29),
    overhang=(3.70, -1.30 - 6.04, 3.70 + 18.0, -1.30),
    rows=[col(19, _dkc4_j2, 0, 0, "down", 1, "left"),
          col(19, list(reversed(_dkc4_j3)), 25.40, 45.72, "up", 20, "right")],
    labels=[("ANT", 12.7, -8.7, 0), ("USB", 12.7, 48.0, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# ESP32 30P 开发板（DOIT DevKit V1 类，淘宝）：51.45×28.33，2×15，排距 25.40；EN 端余 5.9、USB 端余 10.0（按 espboards 图量）
_doit_l = ["EN", "VP_GPIO36", "VN_GPIO39", "GPIO34", "GPIO35", "GPIO32", "GPIO33", "GPIO25", "GPIO26", "GPIO27",
           "GPIO14", "GPIO12", "GPIO13", "GND", "VIN"]
_doit_r = ["GPIO23", "GPIO22", "TX_GPIO1", "RX_GPIO3", "GPIO21", "GPIO19", "GPIO18", "GPIO5", "GPIO17", "GPIO16",
           "GPIO4", "GPIO2", "GPIO15", "GND", "3V3"]
add("Module_ESP32_DevKit_30P_W25.4",
    descr="ESP32 30P 开发板（DOIT DevKit V1 类），2×15 2.54，排距 25.40；1 脚 EN 靠天线。淘宝另有排距 22.86 的窄版",
    board=(-1.47, -5.9, 25.40 + 1.47, 35.56 + 10.0),
    rows=[col(15, _doit_l, 0, 0, "down", 1, "left"),
          col(15, list(reversed(_doit_r)), 25.40, 35.56, "up", 16, "right")],
    labels=[("ANT", 12.7, -7.1, 0), ("USB", 12.7, 46.8, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# ESP32-C3 SuperMini（淘宝 nologo）：22.52×18，2×8，排距 15.24。正面看 USB-C 朝上时，左列 GPIO5…21，右列 5V…GPIO0
_c3_l = ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "RX_GPIO20", "TX_GPIO21"]
_c3_r = ["5V", "GND", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"]
add("Module_ESP32-C3_SuperMini",
    descr="ESP32-C3 SuperMini，2×8 2.54，排距 15.24；正面朝上、USB-C 朝上时左列 GPIO5-21，右列 5V/GND/3V3/GPIO4-0",
    board=(-1.38, -1.5, 15.24 + 1.38, 17.78 + 3.24),
    rows=[col(8, _c3_l, 0, 0, "down", 1, "left"),
          col(8, list(reversed(_c3_r)), 15.24, 17.78, "up", 9, "right")],
    labels=[("USB-C", 7.62, -2.7, 0), ("ANT", 7.62, 22.1, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# NodeMCU ESP8266：v3（CH340，宽版）排距 27.94；v2（CP2102，窄版）排距 22.86。2×15
_nm_l = ["A0", "RSV", "RSV", "SD3_GPIO10", "SD2_GPIO9", "SD1", "CMD", "SD0", "CLK", "GND", "3V3", "EN", "RST", "GND", "VIN"]
_nm_r = ["D0_GPIO16", "D1_GPIO5", "D2_GPIO4", "D3_GPIO0", "D4_GPIO2", "3V3", "GND", "D5_GPIO14", "D6_GPIO12",
         "D7_GPIO13", "D8_GPIO15", "RX_GPIO3", "TX_GPIO1", "GND", "3V3"]
add("Module_NodeMCU_ESP8266_CH340_W27.94",
    descr="NodeMCU ESP8266 v3（CH340 宽版），2×15 2.54，排距 27.94；1 脚 A0 靠天线",
    board=(-1.5, -12.0, 27.94 + 1.5, 35.56 + 10.3),
    rows=[col(15, _nm_l, 0, 0, "down", 1, "left"),
          col(15, list(reversed(_nm_r)), 27.94, 35.56, "up", 16, "right")],
    labels=[("ANT", 13.97, -13.2, 0), ("USB", 13.97, 47.0, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])
add("Module_NodeMCU_ESP8266_CP2102_W22.86",
    descr="NodeMCU ESP8266 v2（CP2102 窄版），2×15 2.54，排距 22.86；1 脚 A0 靠天线",
    board=(-1.57, -6.2, 22.86 + 1.57, 35.56 + 6.2),
    rows=[col(15, _nm_l, 0, 0, "down", 1, "left"),
          col(15, list(reversed(_nm_r)), 22.86, 35.56, "up", 16, "right")],
    labels=[("ANT", 11.43, -7.4, 0), ("USB", 11.43, 43.0, 0)],
    height="插在 8.5 mm 排母上，模块底面离底板约 8.5 mm",
    sym_groups=[[0], [1]])

# ---------------- 显示屏 ----------------
def _oled096(name, names, descr):
    # lcdwiki MC096：PCB 27.30×27.80；1 脚距左边 9.84，引脚行距上边 1.50；Φ2 安装孔距边 2.0
    add(name, descr=descr, board=(-9.84, -1.50, -9.84 + 27.30, -1.50 + 27.80),
        holes=[(-7.84, 0.50, 2.0), (15.46, 0.50, 2.0), (-7.84, 24.30, 2.0), (15.46, 24.30, 2.0)],
        rows=[col(4, names, 0, 0, "right", 1, "top")],
        height="插在 8.5 mm 排母上（屏朝上）；或用 1×4 排针加杜邦线", sym_groups=[[0]])


_oled096("Module_OLED_0.96_I2C_GND-VCC-SCL-SDA", ["GND", "VCC", "SCL", "SDA"], "0.96 寸 I2C OLED 4P，GND 在前（GND-VCC-SCL-SDA）")
_oled096("Module_OLED_0.96_I2C_VCC-GND-SCL-SDA", ["VCC", "GND", "SCL", "SDA"], "0.96 寸 I2C OLED 4P，VCC 在前（VCC-GND-SCL-SDA）")


def _oled130(name, names, descr):
    # lcdwiki MC130GX/VX：PCB 35.40×33.50；引脚居中，1 脚距左边 13.89，行距上边 2.00；Φ3.0 孔距边 2.50
    add(name, descr=descr, board=(-13.89, -2.00, -13.89 + 35.40, -2.00 + 33.50),
        holes=[(-11.39, 0.50, 3.0), (19.01, 0.50, 3.0), (-11.39, 29.00, 3.0), (19.01, 29.00, 3.0)],
        rows=[col(4, names, 0, 0, "right", 1, "top")],
        height="插在 8.5 mm 排母上（屏朝上）；或用 1×4 排针加杜邦线", sym_groups=[[0]])


_oled130("Module_OLED_1.3_I2C_GND-VCC-SCL-SDA", ["GND", "VCC", "SCL", "SDA"], "1.3 寸 I2C OLED（SH1106）4P，GND 在前")
_oled130("Module_OLED_1.3_I2C_VCC-GND-SCL-SDA", ["VCC", "GND", "SCL", "SDA"], "1.3 寸 I2C OLED（SH1106）4P，VCC 在前")

# lcdwiki MC091GX：PCB 38.00×12.00；引脚竖排在左端距左边 1.50，GND 在下（方焊盘）距下边 2.19
add("Module_OLED_0.91_I2C_128x32",
    descr="0.91 寸 I2C OLED 128×32，4P 竖排在左端，自下而上 GND-VCC-SCL-SDA",
    board=(-1.50, 2.19 - 12.00, -1.50 + 38.00, 2.19),
    rows=[col(4, ["GND", "VCC", "SCL", "SDA"], 0, 0, "up", 1, "left")],
    height="插在排母上或用杜邦线；屏很薄，需固定", sym_groups=[[0]])

# lcdwiki MSP096X：PCB 27.30×27.80；1 脚 GND 距左边 6.03，行距上边 1.50；Φ2 孔距边 2.0
add("Module_OLED_0.96_SPI_7P",
    descr="0.96 寸 SPI OLED 7P：GND-VCC-D0-D1-RES-DC-CS",
    board=(-6.03, -1.50, -6.03 + 27.30, -1.50 + 27.80),
    holes=[(-4.03, 0.50, 2.0), (19.27, 0.50, 2.0), (-4.03, 24.30, 2.0), (19.27, 24.30, 2.0)],
    rows=[col(7, ["GND", "VCC", "D0_SCK", "D1_MOSI", "RES", "DC", "CS"], 0, 0, "right", 1, "top")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])

# lcdwiki MSP1803：PCB 34.50×58.00；8P 在下边，行距下边 2.50，横向居中（图上未直接标，量图 8.4）；Φ3.2 孔距边 3.0
add("Module_TFT_1.8_ST7735_8P",
    descr="1.8 寸 SPI TFT ST7735S 8P：VCC-GND-CS-RESET-A0-SDA-SCK-LED，引脚在屏下边",
    board=(-8.36, 2.50 - 58.00, -8.36 + 34.50, 2.50),
    holes=[(-5.36, -52.50, 3.2), (23.14, -52.50, 3.2), (-5.36, -0.50, 3.2), (23.14, -0.50, 3.2)],
    rows=[col(8, ["VCC", "GND", "CS", "RESET", "A0_DC", "SDA", "SCK", "LED"], 0, 0, "right", 1, "bottom")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])

# lcdwiki MSP1541：PCB 32.00×43.72；1 脚 GND 距左边 7.11，行距上边 1.50；Φ2 孔距边 2.5
add("Module_IPS_1.54_ST7789_8P",
    descr="1.54 寸 IPS ST7789 240×240，8P：GND-VCC-SCL-SDA-RES-DC-CS-BLK，只能接 3.3V",
    board=(-7.11, -1.50, -7.11 + 32.00, -1.50 + 43.72),
    holes=[(-4.61, 1.00, 2.0), (22.39, 1.00, 2.0), (-4.61, 39.72, 2.0), (22.39, 39.72, 2.0)],
    rows=[col(8, ["GND", "VCC", "SCL", "SDA", "RES", "DC", "CS", "BLK"], 0, 0, "right", 1, "top")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])

# lcdwiki MSP2008：PCB 36.48×61.12；1 脚 GND 距左边 9.35，行距上边 1.50；Φ2 孔距边 2.5
add("Module_IPS_2.0_ST7789_8P",
    descr="2.0 寸 IPS ST7789 240×320，8P：GND-VCC-SCL-SDA-RES-DC-CS-BLK，只能接 3.3V",
    board=(-9.35, -1.50, -9.35 + 36.48, -1.50 + 61.12),
    holes=[(-6.85, 1.00, 2.0), (24.63, 1.00, 2.0), (-6.85, 57.12, 2.0), (24.63, 57.12, 2.0)],
    rows=[col(8, ["GND", "VCC", "SCL", "SDA", "RES", "DC", "CS", "BLK"], 0, 0, "right", 1, "top")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])

_ili_pins = ["VCC", "GND", "CS", "RESET", "DC", "SDI_MOSI", "SCK", "LED", "SDO_MISO", "T_CLK", "T_CS", "T_DIN", "T_DO", "T_IRQ"]
# lcdwiki MSP2402：PCB 42.72×77.18；14P 在下边距下边 2.00，1 脚距左边 4.85；Φ3.2 孔间距 36.72×67.26，距左右 3.00、距上 3.00
add("Module_TFT_2.4_ILI9341_14P",
    descr="2.4 寸 SPI TFT ILI9341 带触摸 14P，引脚在屏下边，1 脚 VCC",
    board=(-4.85, 2.00 - 77.18, -4.85 + 42.72, 2.00),
    holes=[(-1.85, -72.18, 3.2), (34.87, -72.18, 3.2), (-1.85, -4.92, 3.2), (34.87, -4.92, 3.2)],
    rows=[col(14, _ili_pins, 0, 0, "right", 1, "bottom")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])
# lcdwiki MSP2807：PCB 50.00×86.00；14P 距下边 2.00，1 脚距左边 8.49；Φ3.2 孔间距 44.00×76.08，距左右、上 3.00
add("Module_TFT_2.8_ILI9341_14P",
    descr="2.8 寸 SPI TFT ILI9341 带触摸 14P，引脚在屏下边，1 脚 VCC",
    board=(-8.49, 2.00 - 86.00, -8.49 + 50.00, 2.00),
    holes=[(-5.49, -81.00, 3.2), (38.51, -81.00, 3.2), (-5.49, -4.92, 3.2), (38.51, -4.92, 3.2)],
    rows=[col(14, _ili_pins, 0, 0, "right", 1, "bottom")],
    height="插在 8.5 mm 排母上（屏朝上）", sym_groups=[[0]])


# ---------------- 只生成符号（封装用官方或 gen_footprints 生成的） ----------------
SYMBOLS = {}


def sym(name, fp, descr, left, right=()):
    SYMBOLS[name] = {"name": name, "fp": fp, "descr": descr, "left": list(left), "right": list(right)}


sym("7Seg_1Digit_CA", "StudentHW:7Seg_0.56in_1Digit_10P", "1 位 7 段数码管，共阳（3、8 脚为公共阳极）",
    [("7", "A"), ("6", "B"), ("4", "C"), ("2", "D"), ("1", "E"), ("9", "F"), ("10", "G"), ("5", "DP")],
    [("3", "CA"), ("8", "CA")])
