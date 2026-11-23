"""软件工程实验四：面向对象的系统建模 B。

包含三个可独立测试的状态机实现：

* ``water_tank``       —— B1 恒温水箱控制；
* ``control_panel``    —— B2 SafeHome 控制面板；
* ``string_extractor`` —— B3 源文件字符串提取。
"""

from .control_panel import ControlPanel, ControlPanelState
from .string_extractor import (
    ExtractState,
    StringExtractionError,
    UnterminatedStringError,
    extract_strings,
)
from .water_tank import TankState, WaterTankController

__all__ = [
    "ControlPanel",
    "ControlPanelState",
    "ExtractState",
    "StringExtractionError",
    "TankState",
    "UnterminatedStringError",
    "WaterTankController",
    "extract_strings",
]
