# 检查脚本自测

每一行把一个真实条目故意改错一处，脚本必须报错。

| 结果 | 故意制造的错误 | 脚本 | 期望报出 | 实际输出（节选） |
|---|---|---|---|---|
| ✅ 抓到 | 脚距写错（XH 写成 2.54） | check_footprints.py | 脚距 | ✗ XH-005    Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical: 脚距 2.500 ≠ CSV 2.54（焊盘 1-2） |
| ✅ 抓到 | 脚数不符 | check_footprints.py | 焊盘编号数 | ✗ TERM-002  TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal: 焊盘编号数 3 ≠ pin_coun |
| ✅ 抓到 | 引脚太粗、孔太小 | check_footprints.py | 孔 | ✗ DIO-004   StudentHW:D_DO-41_SOD81_P10.16mm_Horizontal: 焊盘1 孔 1.10 < 引脚 0.95+0.2；焊盘2 孔 1.10 < 引脚 0.95+0.2 |
| ✅ 抓到 | 环宽不足且没写理由 | check_footprints.py | 环宽 | ✗ HDR-001   Connector_PinHeader_2.54mm:PinHeader_1x40_P2.54mm_Vertical: 焊盘1 环宽 0.35 < 0.5（孔 1.00）；焊盘2 环宽 0.35  |
| ✅ 抓到 | 放宽环宽但 notes 没写理由 | check_footprints.py | notes 没写理由 | ✗ XH-002    Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical: ring_min_mm 放宽了环宽，但 notes 没写理由；ring_min_mm 放宽 |
| ✅ 抓到 | 有极性但 1 脚不是方焊盘 | check_footprints.py | 方焊盘 | ✗ CAP-001   Capacitor_THT:C_Disc_D7.0mm_W2.5mm_P5.00mm: 有极性但 1 脚不是方焊盘 |
| ✅ 抓到 | 封装不存在 | check_footprints.py | 封装不存在 | ✗ RES-001   StudentHW:NoSuchFootprint: 封装不存在: StudentHW:NoSuchFootprint |
| ✅ 抓到 | 没有 3D 也没说明 | check_footprints.py | 3D | ✗ FUS-001   StudentHW:Fuse_PTC_Radial_P5.08mm: 没有 3D 模型且 notes 未说明 |
| ✅ 抓到 | 贴片封装（0805 电阻） | check_footprints.py | 禁止贴片 | ✗ RES-001   Resistor_SMD:R_0805_2012Metric: 禁止贴片：封装 Resistor_SMD:R_0805_2012Metric 是贴片封装；禁止贴片：封装里有贴片焊盘 ['1', ' |
| ✅ 抓到 | mount 写贴片 | check_footprints.py | 禁止贴片 | ✗ RES-002   Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal: 禁止贴片：mount 写的是“贴片” |
| ✅ 抓到 | 符号引脚与焊盘不符 | check_symbol_pins.py | ≠ 焊盘 | ✗ LED-001   符号引脚 ['1', '2', '3'] ≠ 焊盘 ['1', '2'] |
| ✅ 抓到 | 符号不存在 | check_symbol_pins.py | 符号不存在 | ✗ Q-001     符号不存在: Transistor_BJT:NoSuchPart |
| ✅ 抓到 | 两个条目用同一张尺寸图 | check_evidence.py | 内容完全相同 | ✗ CAP-002   dim_same.png 与 /home/user/123/常用元器件库/tools/selftest/fixtures/evidence/CAP-001/dim_same.png 内容完全相同 |
| ✅ 抓到 | 型号与 C 编号不符 | check_evidence.py | 型号不符 | ✗ RES-001   型号不符：嘉立创 MFR0W4F1001A50 ≠ CSV MFR0W4F1002A50 |
| ✅ 抓到 | 规格书是网页不是 PDF | check_evidence.py | 不是 PDF | ✗ RES-002   datasheet.pdf 不是 PDF |
| ✅ 抓到 | 图片型 PDF 未注明人工读图 | check_evidence.py | 人工读图 | ✗ SW-001    PDF 文本里找不到 K2-1102DP-C4SW-04，且 dim_source 未注明人工读图 |
| ✅ 抓到 | 规格书链接为空 | check_evidence.py | datasheet_url 为空 | ✗ DSP-002   datasheet_url 为空 |
| ✅ 抓到 | 缺尺寸图 | check_evidence.py | 缺尺寸图 | ✗ BZ-002    缺尺寸图 dim*.png |
| ✅ 抓到 | 原子符号封装属性写错 | check_atomic.py | Footprint 属性 | ✗ Q-001_S8050: Footprint 属性 'Package_TO_SOT_THT:TO-92_Inline' ≠ 应为 'StudentHW:TO-92_Inline_Wide' |
| ✅ 抓到 | 原子符号少一个引脚 | check_atomic.py | 引脚与基础符号 | ✗ REG-002_LD1117V33: 引脚与基础符号 Regulator_Linear:LM1117T-3.3 不一致：缺 [('3', 'VI')] 多 []；引脚号 ['1', '2'] ≠ 封装焊盘号 ['1' |
| ✅ 抓到 | 原子符号 C 编号写错 | check_atomic.py | LCSC 属性 | ✗ RES-001_10k: LCSC 属性 'C57435' ≠ 应为 'C57436' |
| ✅ 抓到 | I2C 地址冲突（MPU6050 与 DS3231 同为 0x68） | check_project.py | 冲突 | ✗ I2C 总线 0：0x68 冲突（SEN-014 与 SEN-047）→ 把 SEN-014 改到 0x69（AD0 接 VCC 改 0x69），并在 items 里写 i2c_addr；或分两路 I2C |
| ✅ 抓到 | 5V 输出接不耐 5V 的脚（HC-SR04 Echo → ESP32） | check_project.py | 不耐 5V | ✗ SEN-018.ECHO → GPIO26：模块输出 5V，GPIO26 不耐 5V（加分压/电平转换，或模块改 3.3V 供电） |
| ✅ 抓到 | 用 Flash 脚 | check_project.py | 别用 | ✗ SEN-019.TRIG → GPIO34：该脚只能输入，但 TRIG 需要主控输出 |
| ✅ 抓到 | 只能输入的脚接输出信号 | check_project.py | 只能输入 | ✗ SEN-019.TRIG → GPIO34：该脚只能输入，但 TRIG 需要主控输出 |
| ✅ 抓到 | 同一个脚分两次 | check_project.py | 同时分给了 | ✗ SEN-019.TRIG → GPIO34：该脚只能输入，但 TRIG 需要主控输出 |
| ✅ 抓到 | 电流超 70%（USB 带 MG996R） | check_project.py | 超过 70% | ✗ 电流：典型合计 2500mA，峰值合计 2500mA；USB 口 500mA 的 70% = 350mA → 超过 70%，换更大电源或分路供电 |
| ✅ 抓到 | I2C 上拉到 5V 接 ESP32 | check_project.py | 上拉到 5V | ✗ I2C 总线 0：SEN-006 上拉到 5V，主控 GPIO4 不耐 5V（模块改 3.3V 供电或加电平转换） |
| ✅ 抓到 | 热度定为大众但依据写未核 | build_market.py | 依据写的是未核 | ✗ SEN-030 定为大众，但依据写的是未核 |
| ✅ 抓到 | 淘宝参考价只取 2 家 | build_market.py | 至少 3 家 | ✗ SEN-014 淘宝参考价只有 2 家，至少 3 家 |
| ✅ 抓到 | 淘宝中位数算错 | build_market.py | 中位数 | ✗ SEN-014 淘宝参考价 median=2.5 与各家价格中位数 2 不符 |
| ✅ 抓到 | 淘宝价只写一个数字 | build_market.py | 店铺明细 | ✗ SEN-014 price_taobao_ref 只写了一个数字，必须写店铺明细（shops） |
| ✅ 抓到 | 替代料引用不存在的编号 | build_market.py | 不在 parts.csv | ✗ SEN-001 better_alt 引用的 SEN-999 不在 parts.csv |
| ✅ 抓到 | 热度等级写错字 | build_market.py | 不是 大众 | ✗ RES-001 sales_level=热门 不是 大众/常用/冷门/未核 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_footprints.py | 0 错误 | 检查 189 条，出错 0 条 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_symbol_pins.py | 0 错误 | 检查 189 条，出错 0 条 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_evidence.py | 0 错误 | 检查 189 条，出错 0 条；离线警告：缺 PDF 86 条，C 编号未接口核实 2 条 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_atomic.py | 0 错误 | 原子符号 192 个（应有 192），kicad-cli 导出 192 张 SVG，出错 0 处 |
| ✅ 通过 | 正向对照：样例项目 示例1-ESP32S3-OLED-温湿度 | check_project.py | 0 错误 | 示例1-ESP32S3-OLED-温湿度：错误 0，提醒 2 → projects/示例1-ESP32S3-OLED-温湿度/检查结果.md |
| ✅ 通过 | 正向对照：样例项目 示例2-STM32-继电器-按键 | check_project.py | 0 错误 | 示例2-STM32-继电器-按键：错误 0，提醒 1 → projects/示例2-STM32-继电器-按键/检查结果.md |
| ✅ 通过 | 正向对照：样例项目 示例3-Nano-超声波-舵机 | check_project.py | 0 错误 | 示例3-Nano-超声波-舵机：错误 0，提醒 1 → projects/示例3-Nano-超声波-舵机/检查结果.md |

合计 34 个故意错误 + 7 个正向对照，失败 0 项。

注意：本次在离线模式运行（STUDENTHW_OFFLINE=1），证据检查的正向对照把缺 PDF、缺 jlc.json 记为警告而非错误。
