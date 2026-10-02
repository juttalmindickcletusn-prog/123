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
| ✅ 抓到 | 符号引脚与焊盘不符 | check_symbol_pins.py | ≠ 焊盘 | ✗ LED-001   符号引脚 ['1', '2', '3'] ≠ 焊盘 ['1', '2'] |
| ✅ 抓到 | 符号不存在 | check_symbol_pins.py | 符号不存在 | ✗ Q-001     符号不存在: Transistor_BJT:NoSuchPart |
| ✅ 抓到 | 两个条目用同一张尺寸图 | check_evidence.py | 内容完全相同 | ✗ CAP-002   dim_same.png 与 /home/user/123/常用元器件库/tools/selftest/fixtures/evidence/CAP-001/dim_same.png 内容完全相同 |
| ✅ 抓到 | 型号与 C 编号不符 | check_evidence.py | 型号不符 | ✗ RES-001   型号不符：嘉立创 MFR0W4F1001A50 ≠ CSV MFR0W4F1002A50 |
| ✅ 抓到 | 规格书是网页不是 PDF | check_evidence.py | 不是 PDF | ✗ RES-002   datasheet.pdf 不是 PDF |
| ✅ 抓到 | 图片型 PDF 未注明人工读图 | check_evidence.py | 人工读图 | ✗ SW-001    PDF 文本里找不到 K2-1102DP-C4SW-04，且 dim_source 未注明人工读图 |
| ✅ 抓到 | 规格书链接为空 | check_evidence.py | datasheet_url 为空 | ✗ DSP-002   datasheet_url 为空 |
| ✅ 抓到 | 缺尺寸图 | check_evidence.py | 缺尺寸图 | ✗ BZ-002    缺尺寸图 dim*.png |
| ✅ 通过 | 正向对照：真实 parts.csv | check_footprints.py | 0 错误 | 检查 113 条，出错 0 条 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_symbol_pins.py | 0 错误 | 检查 113 条，出错 0 条 |
| ✅ 通过 | 正向对照：真实 parts.csv | check_evidence.py | 0 错误 | 检查 113 条，出错 0 条；精简包缺 PDF（未核 PDF 文本）90 条 |

合计 16 个故意错误 + 3 个正向对照，失败 0 项。

注意：本次在精简包上运行（STUDENTHW_PDF_MISSING_OK=1），证据检查的正向对照把缺 PDF 记为警告而非错误。
