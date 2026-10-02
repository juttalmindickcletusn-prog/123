# 一次性种子脚本（留档，不在 run_all 里）

云端（2026-10-02）用这几个脚本一次性生成了 src 下的数据文件。之后数据以 src/*.yaml 为准，直接改 yaml，不要再跑这些脚本（会覆盖手改）。

| 脚本 | 生成 | 依赖的外部资料（当时放在云端临时目录，路径写死在脚本里） |
|---|---|---|
| gen_b3.py | src/b3_modules.yaml（第三批 69 条） | 各模块资料链接（写在条目的 datasheet_url / dim_source） |
| gen_elec.py | src/electrical.yaml | 规格书/教程站摘录，每条写在 src_ref |
| gen_mcu_pins.py | src/mcu_pins.yaml | ESP-IDF gpio .inc、esp-hardware-design-guidelines、pico-sdk、stm32duino/arduino-esp32/esp8266 板型定义 |
| gen_market.py | src/market.yaml | arduino/library-registry 仓库（commit df95082）、各 Arduino 内核 boards.txt、evidence/*/jlc.json |

要复现：把脚本里的临时目录改成本机路径，再按脚本头部注释准备资料。
