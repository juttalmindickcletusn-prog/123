# 第二批（主控与显示）完成报告

日期：2026-10-02。前 26 条（`src/b2_mcu_display.yaml`）是本地 Claude 做的；本次云端补完剩下 13 条（`src/b2_rest.yaml`），并给第二批全部条目补了电气字段和主控逐脚表。

## 结果

第二批共 39 条：A 级 2、B 级 20、C 级 17。本次新增 13 条：B 级 3、C 级 10。

| 编号 | 条目 | 级别 | 尺寸依据 | 说明 |
|---|---|---|---|---|
| MCU-012 | 树莓派 Pico | B | 树莓派 Pico 规格书机械图（交接资料线索里的 PDF 页截图） | 官方封装 `Module:RaspberryPi_Pico_Common_THT`，立创 C7203002 |
| MCU-013 | 树莓派 Pico W | C | 云端没取到 Pico W 规格书，暂用 Pico 机械图 | 外形和脚位与 Pico 相同（交接文档 1.2 节），但没拿到 Pico W 自己的图，所以定 C |
| MCU-014 | STC89C52RC（PDIP-40，插座） | C | STC89 系列手册 PDIP40 尺寸图（交接资料线索） | C14022 没能用接口核实（离线警告）；40P 锁紧座单独条目没做，见待确认 |
| MCU-015 | WeAct BlackPill F411 V3.1 | B | WeAct 官方 GitHub 仓库 Board Shape PDF | 自建封装，脚序按官方原理图 |
| MCU-016 | 安信可 ESP32-CAM | B | 安信可规格书尺寸图（GitHub 公开 PDF） | 自建封装，2×8 排母 |
| DSP-012 | LCD1602（汉昇 HS1602A-B） | C | 汉昇规格书外形图（交接资料线索） | 官方封装 `Display:WC1602A`；规格书是截图，没核对到焊盘公差，定 C |
| DSP-013 | PCF8574 I2C 转接板 | C | 底板只焊 1×4 排针，按 HDR-001 排针图 | 转接板本身无厂家图 |
| DSP-014 | LCD2004 | C | 不上板（铜柱固定，杜邦线接 4P） | 无可下载的主流款尺寸图 |
| DSP-015 | TM1637 4 位数码管模块 | C | 底板 1×4 排针 | 模块无厂家图 |
| DSP-016 | MAX7219 8×8 点阵模块 | C | 底板 1×5 排针 | 模块无厂家图 |
| TOOL-001/002/003 | CH340、CP2102 USB-TTL；ST-Link V2 | C | 不上板 | 只做接线说明和电气字段 |

C 级模块的做法：底板上只放带脚名丝印的排针（`StudentHW:Module_Hdr_*`），模块用杜邦线按脚名对接。底板封装只依赖排针图纸（HDR-001，B 级），不依赖模块外形，所以模块各家版型不同也不会焊错；直接插排母前要对照模块丝印确认顺序。

## 检查结果（`STUDENTHW_OFFLINE=1 python3 tools/run_all.py`，KiCad 10.0.6，全部通过）

| 检查 | 结果 |
|---|---|
| 封装检查（含新加的禁止贴片规则） | 189 条，0 错误 |
| 符号引脚检查 | 189 条，0 错误 |
| 证据检查 | 189 条，0 错误；离线警告：缺 PDF 86 条，C 编号未接口核实 2 条（ACT-003、MCU-014） |
| 原子符号检查 | 192 个，0 错误 |
| 检查脚本自测 | 39 个故意错误全部抓到，7 个正向对照、15 个成本/价格测试全部通过（`reports/selftest.md`） |
| 测试板 DRC | 149 个封装，0 违规、0 未连接 |

"离线警告"不算通过：精简交接包没带 PDF，云端也连不上立创/嘉立创接口。拿回本地后跑 `python tools/fetch_evidence.py 编号…`，再不带 `STUDENTHW_OFFLINE` 重跑一次。

## 资料来源

云端网络只能访问 GitHub、PyPI 和 Ubuntu 源，立创、嘉立创、淘宝、大多数厂家官网都被拦。新条目的资料来自：

- 交接资料 `交接资料/线索/` 里本地 Claude 留下的 Pico、LCD1602、STC89 规格书页面截图和立创 C 编号；
- GitHub 公开仓库：WeAct `WeActStudio.MiniSTM32F4x1`（BlackPill 原理图和外形）、ESP32-CAM 规格书（`raphaelbs/esp32-cam-ai-thinker`）；
- `yaqwsx/jlcparts` 的嘉立创元件库镜像（`tools/import_jlcparts.py` 导入），用来核对 MCU-012/013/016、DSP-012 的 C 编号、型号和库存。

## 与任务书的差异

- STC89C52RC 的 40P 锁紧座没有单独建条目：MCU-014 用 KiCad 官方 `DIP-40_W15.24mm_Socket` 封装，圆孔座、锁紧座都按 600mil 插，但锁紧座的具体型号和 C 编号没核到。
- 交接文档 1.2 节要求 Pico 环宽写 `ring_min_mm`，已按官方封装焊盘 1.6/孔 1.0 写了 0.3，并在 notes 里注明。

## 遇到的问题

- 原子符号库生成时，子单元改名用了母符号的名字长度，KiCad 打不开；改成正则匹配 `_单元_样式` 后正常。
- Value/Reference 复制时丢了对齐属性，改成复制原属性节点。
- 写 STC 和 LCD2004 链接时我先凭记忆写了两个链接，复查发现不实，已换成搜索到的真实链接（stcmicro.com 产品页、微雪 LCD2004.pdf）。
