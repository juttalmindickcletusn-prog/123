"""本机工具路径。默认是作者 Windows 机器；别的机器用环境变量覆盖：
  KICAD_SHARE  KiCad 库根目录（含 footprints/ symbols/ 3dmodels/），Linux 一般是 /usr/share/kicad
  KICAD_PY     能 import pcbnew 的 Python，Linux 一般是 /usr/bin/python3
  KICAD_CLI    kicad-cli 可执行文件，Linux 一般是 kicad-cli
  PYLIB        装了 easyeda2kicad 的额外 site-packages（可空）
"""
import os
from pathlib import Path

KICAD_SHARE = Path(os.environ.get("KICAD_SHARE", "D:/kicad/share/kicad"))
FP_OFF = KICAD_SHARE / "footprints"
SYM_OFF = KICAD_SHARE / "symbols"
MODELS_3D = KICAD_SHARE / "3dmodels"
KICAD_PY = os.environ.get("KICAD_PY", "D:/kicad/bin/python.exe")
KICAD_CLI = os.environ.get("KICAD_CLI", "D:/kicad/bin/kicad-cli.exe")
PYLIB = os.environ.get("PYLIB", "D:/pylibs_studenthw")
