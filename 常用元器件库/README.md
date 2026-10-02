# 常用元器件库（StudentHW）

给本科毕设、大创这类学生硬件项目用的选型与封装库。**上板器件全部是直插件**（模块整块插在排母上的不算贴片）。

现有 189 条：第一批通用件 81 条（A 14、B 66、C 1），第二批主控与显示 39 条（A 2、B 20、C 17），第三批传感器/执行器/通信/电源模块 69 条（A 1、C 68）。等级说明见下文；没做完和没核实的事项见 `待确认.md`。

## 先看哪里

| 想做什么 | 看这个 |
|---|---|
| 按功能挑件（三档推荐、不推荐的原因） | `选型速查.md` |
| 画图前查 I2C 地址冲突、电平、主控引脚、电流 | `reports/兼容性速查.md`，或对项目跑 `tools/check_project.py` |
| 价格、热度、替代料 | `reports/价格与热度表.md`、`价格与热度.csv` |
| 快速查型号、封装 | `常用元器件清单.md` |
| 看封装图、符号图、尺寸证据 | `reports/preview.html`（`python tools/serve.py 18431 .` 后用浏览器打开） |
| 全部字段 | `parts.csv`（UTF-8，Excel 可直接打开） |
| 还没定、没核实、已删掉的 | `待确认.md` |
| 各批做了什么、检查结果 | `reports/batch1_报告.md`、`batch2_报告.md`、`batch3_报告.md`、`reports/检查汇总.md` |

## 在 KiCad 里使用（必须 KiCad 10.x）

库文件是 KiCad 10 格式，KiCad 8、9 打不开，不要降级。

1. **路径变量**：「偏好设置 → 配置路径」新增 `STUDENTHW_DIR`，值为本文件夹的完整路径。自建封装的 3D 模型靠它定位。
2. **封装库**：「偏好设置 → 管理封装库」新增 `StudentHW` → `${STUDENTHW_DIR}/kicad/StudentHW.pretty`。
3. **符号库**：「偏好设置 → 管理符号库」新增两个：

   | 库名 | 路径 | 内容 |
   |---|---|---|
   | `StudentHW_Parts` | `${STUDENTHW_DIR}/kicad/StudentHW_Parts.kicad_sym` | **原子符号**：每个条目（阻值逐个）一个符号，封装、型号、厂家、立创 C 编号、价格、1 脚标识、库内编号全部填好 |
   | `StudentHW` | `${STUDENTHW_DIR}/kicad/StudentHW.kicad_sym` | 模块和自建器件的基础符号（原子符号由它和 KiCad 官方符号生成） |

   可以直接把 `kicad/lib_table_snippet.txt` 里的几行粘进项目的 `sym-lib-table` / `fp-lib-table`。
4. **画图规则**：
   - 优先从 `StudentHW_Parts` 取件。选中即带封装和 C 编号，不会配错封装。
   - 库里没有的件算"库外件"。在 BOM 和原理图的 Value 或备注里标"库外件"，选型、封装要另外核对。

## 级别

| 级别 | 含义 |
|---|---|
| A | V1.1 底板已经实焊验证，封装从 V1.1 原样复制 |
| B | 按厂家尺寸图核对过，并通过全部脚本检查 |
| C | 没有可靠的厂家尺寸图（淘宝通用模块大多如此），或者有关键尺寸、脚序没核实。到货要对照实物 |

C 级模块的底板做法：只焊带脚名丝印的直排针（按 B 级排针图纸），模块用杜邦线按脚名对接，所以模块外形不同不会把板子做废。

## 文件夹

```
src/*.yaml               唯一手填的数据
  b1_*.yaml / b2_*.yaml / b3_modules.yaml   条目
  series.yaml            系列件（阻值逐个，每个值一个 C 编号）
  electrical.yaml        模块和芯片的电气参数（供电、电平、耐 5V、I2C 地址、上拉、电流），每条写 src_ref
  mcu_pins.yaml          主控板逐脚约束（启动脚、占用脚、只能输入、ADC、耐 5V）
  market.yaml            热度、替代、推荐店铺、淘宝价（规则写在文件头）
  price_history.csv      立创价格历史（refresh_prices.py 追加）
  buy_rules.yaml         采购量规则（起订、备损、小件最少量、报警阈值）
  selection.yaml         按功能选型
parts.csv                由 build_csv.py 生成，不要手改
projects/<项目>.yaml     项目器件清单和引脚分配；projects/<项目>/ 是检查结果、成本、采购单
evidence/<编号>/         规格书 PDF、尺寸图 dim_*.png、jlc.json/jlc.txt
kicad/                   StudentHW.pretty、StudentHW.3dshapes、StudentHW.kicad_sym、StudentHW_Parts.kicad_sym
tools/                   脚本（见下）
reports/                 检查结果、自测、测试板与渲染、预览页、速查表
_archive_*/              移走的旧版本和贴片件（不删，留档）
build/                   缓存和中间文件，可删
```

## 一键重建和检查

只改 `src/*.yaml`，然后：

```bash
python3 tools/run_all.py                      # 正常（联网补过证据之后）
STUDENTHW_OFFLINE=1 python3 tools/run_all.py  # 离线：缺 PDF、缺 jlc.json 记为警告，写进检查汇总
```

`run_all.py` 不联网，依次做：生成封装和符号 → 生成 parts.csv → 生成原子符号库 → 四项检查（封装、符号引脚、证据、原子符号）→ 兼容性速查 → 价格与热度表 → 选型速查 → 价格新鲜度 → 样例项目检查和成本 → 检查脚本自测 → 测试板 DRC 和渲染 → 预览页和清单。结果在 `reports/检查汇总.md`，任何一步失败都会写明。

Linux 环境变量：`KICAD_SHARE=/usr/share/kicad KICAD_PY=python3 KICAD_CLI=kicad-cli`。

## 接项目时的流程

1. 在 `选型速查.md` 按功能挑件，记下编号。
2. 写 `projects/<项目名>.yaml`（格式照 `projects/示例1-ESP32S3-OLED-温湿度.yaml`：sets、power、mcu、items、pins、extra_cost）。
3. 画图前检查：

   ```bash
   python3 tools/check_project.py projects/项目.yaml
   ```

   会查 I2C 地址冲突（含改地址建议）、模块输出电平与主控是否耐 5V、引脚用了启动脚/Flash 脚/只能输入的脚/重复分配、峰值电流是否超过供电能力 70%、I2C 上拉并联后是否太小、是否上拉到 5V。结果写到 `projects/<项目名>/检查结果.md`，有错误时退出码为 1。
4. 算成本、出采购单：

   ```bash
   python3 tools/project_cost.py projects/项目.yaml
   ```

   输出到 `projects/<项目名>/`：
   - `成本.md`：每行写明用的哪一档价格、来源和核实日期；缺价的行单独列出，总计旁标"总价不完整"。
   - `立创配单.csv`：列为 商品编号、用量、预设备损量、位号。"用量"已含套数和备损，网站上套数填 1。列名来自立创帮助页摘要，模板原件没核对，见 `待确认.md`。
   - `淘宝清单.md`：搜索关键词、候选店铺、规格选项提醒。

   采购量规则在 `src/buy_rules.yaml`。只生成文件，不下单。

## 工具一览

| 脚本 | 作用 |
|---|---|
| `fetch_evidence.py 编号…` | 联网：调嘉立创/立创接口核实 C 编号、价格、库存，下载规格书 |
| `render_dim.py 编号 页码 x0 y0 x1 y1 名字` | 从 PDF 截尺寸图 |
| `refresh_prices.py [编号…]` | 联网：刷新立创各档价格和库存（含系列件各值）。限速、缓存，结果追加到 `src/price_history.csv`。库存低于阈值、价格变化超过 10% 时报警。`--check` 不联网，只报超过 30 天的价格和低库存 |
| `import_jlcparts.py` | 用 yaqwsx/jlcparts 的嘉立创元件库镜像离线核对 C 编号（官方接口打不开时用） |
| `gen_footprints.py`、`gen_modules.py`（+ `module_defs.py`、`module_defs_b3.py`） | 生成自建封装、模块排针封装和自建符号 |
| `build_csv.py` | yaml → parts.csv（孔径、焊盘从封装文件读） |
| `build_atomic.py` | 生成原子符号库 `StudentHW_Parts.kicad_sym` |
| `build_compat.py` | 生成 `reports/兼容性速查.md`：I2C 地址总表和冲突表、上拉、电平、主控引脚、电流预算；同时检查所有模块和芯片都有电气数据 |
| `check_project.py 项目.yaml` | 画图前查项目冲突（见上） |
| `build_market.py` | 生成价格与热度表，并校验热度依据、淘宝店铺明细（≥3 家、中位数）、替代料编号 |
| `project_cost.py 项目.yaml` | 成本、立创配单、淘宝清单（见上） |
| `build_selection.py` | 生成 `选型速查.md`，并检查候选编号存在、传感器/执行器/通信/电源条目全部被引用、不推荐的件写了出处、驱动库已核对 |
| `build_testboard.py`、`build_preview.py`、`build_list.py` | 测试板、预览页、清单 |
| `run_all.py` | 一键全部 |
| `seed/` | 云端一次性生成 electrical/mcu_pins/market/第三批数据的脚本，留档 |

## 检查脚本查什么

| 脚本 | 检查内容 |
|---|---|
| `check_footprints.py` | 封装存在；**禁止贴片**（mount 写贴片、封装名像贴片、或有贴片焊盘都报错）；焊盘数 = 脚数；脚距误差 ≤0.02；孔 ≥ 引脚最大尺寸 +0.2；环宽；有极性件 1 脚方焊盘；有 courtyard 和 Fab 层；3D 文件存在 |
| `check_symbol_pins.py` | 符号引脚号集合 = 封装焊盘号集合 |
| `check_evidence.py` | `datasheet_url` 不能为空；C 编号对应型号一致；规格书是真 PDF 且能搜到型号；尺寸图存在、不是空白页、不同条目不能用同一张图 |
| `check_atomic.py` | 原子符号与条目一一对应；封装、C 编号、型号等属性正确并隐藏；引脚 = 基础符号 = 封装焊盘；kicad-cli 能整库导出 |
| `selftest/run_selftest.py` | 自测：故意改错 39 处，各检查都要报出来；7 个正向对照（真实数据、3 个样例项目）要通过；另有 15 个成本/价格测试：手算总价、阶梯选档、缺价、过期、刷新报警 |

环宽规则：孔 ≤0.9 时环宽 ≥0.4，孔 >0.9 时环宽 ≥0.5。受脚距限制放不下的，在 `ring_min_mm` 写放宽值并在 notes 说明。A 级封装豁免。

## 数据来源

| 数据 | 来源 |
|---|---|
| 型号、厂家、库存 | 嘉立创元件接口（第一批）；jlcparts 镜像（云端补的条目） |
| 人民币价格 | 立创商城（经立创 EDA 商品接口），目前只存了起订档 |
| 规格书 | 立创商城、厂家官网、GitHub 公开转存 |
| 电气参数、主控引脚 | 规格书、乐鑫/树莓派/ST 官方文档和 SDK、各 Arduino 内核板型定义；出处写在每条里 |
| 热度 | 嘉立创库存、Arduino 官方库注册表库数、Arduino 内核板型（规则见 `src/market.yaml` 文件头） |
| 3D 模型 | KiCad 官方；官方没有的用立创 EDA 导出 |

淘宝价格和销量需要登录，云端没查，只给搜索关键词和候选店铺。
