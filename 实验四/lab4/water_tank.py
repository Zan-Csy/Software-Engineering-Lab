"""B1：恒温水箱 20℃～100℃ 状态机。

题目把恒温烧水过程描述为一个复合状态：温度检测、加热、停止加热和无水
保护四个子状态共同完成一次恒温控制；23:00 休眠、07:00 恢复以及水箱故障
维修是复合状态之外的迁移。

实现采用事件驱动方式：调用方把温度、水位和时钟事件送入控制器，控制器
只负责状态迁移与继电器动作，不依赖真实传感器，因此便于单元测试。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import Iterable


MIN_HEATING_TEMPERATURE = 20.0
MAX_HEATING_TEMPERATURE = 100.0
SLEEP_HOUR = 23
WAKE_HOUR = 7


class TankState(Enum):
    """恒温水箱的全部状态。"""

    OFF = "关机"
    CHECKING = "温度/水量检测"
    HEATING = "加热"
    HEATER_OFF = "停止加热"
    NO_WATER = "无水保护"
    SLEEPING = "休眠"
    MAINTENANCE = "维修"


RUNNING_STATES = frozenset(
    {
        TankState.CHECKING,
        TankState.HEATING,
        TankState.HEATER_OFF,
        TankState.NO_WATER,
    }
)


class TankStateError(RuntimeError):
    """在当前状态下接收到了不合法的事件。"""


@dataclass(frozen=True)
class TransitionRecord:
    """一条便于演示和写报告的状态迁移记录。"""

    source: TankState
    event: str
    guard: str
    target: TankState
    action: str
    at: datetime | None = None

    def describe(self) -> str:
        at_text = self.at.strftime("%H:%M:%S") if self.at else "--:--:--"
        guard_text = f" [{self.guard}]" if self.guard else ""
        action_text = f" / {self.action}" if self.action else ""
        return (
            f"{at_text}  {self.source.value} --{self.event}{guard_text}--> "
            f"{self.target.value}{action_text}"
        )


class WaterTankController:
    """恒温水箱控制器（纯逻辑，可注入时间以便测试）。"""

    def __init__(self) -> None:
        self._state = TankState.OFF
        self._relay_on = False
        self._temperature: float | None = None
        self._has_water: bool | None = None
        self._history: list[TransitionRecord] = []

    # ------------------------------------------------------------------ 查询
    @property
    def state(self) -> TankState:
        return self._state

    @property
    def relay_on(self) -> bool:
        return self._relay_on

    @property
    def temperature(self) -> float | None:
        return self._temperature

    @property
    def has_water(self) -> bool | None:
        return self._has_water

    @property
    def is_running(self) -> bool:
        """是否处于题目所述“恒温烧水过程”的复合状态中。"""

        return self._state in RUNNING_STATES

    @property
    def history(self) -> tuple[TransitionRecord, ...]:
        return tuple(self._history)

    # ------------------------------------------------------------------ 控制
    def power_on(self, now: datetime | None = None) -> None:
        """上电后进入温度/水量检测，等待第一次传感器采样。"""

        if self._state is not TankState.OFF:
            raise TankStateError(f"当前状态为“{self._state.value}”，不能重复上电")
        self._transition(
            TankState.CHECKING,
            event="系统上电",
            guard="",
            action="继电器断开，等待传感器数据",
            at=now,
        )

    def update(self, temperature: float, has_water: bool) -> None:
        """送入一次温度、水位采样，并执行相应迁移。

        温度使用摄氏度。20℃ 以下开始烧水，100℃ 停止加热；20℃～100℃
        之间保持断开。停止加热后温度再次低于 20℃ 时重新检测，以维持
        恒温烧水循环。
        """

        if temperature < -50 or temperature > 150:
            raise ValueError("温度超出合理范围：-50℃～150℃")
        self._temperature = temperature
        self._has_water = bool(has_water)

        if self._state is TankState.CHECKING:
            self._evaluate_water_temperature(temperature, has_water)
        elif self._state is TankState.HEATING:
            if temperature >= MAX_HEATING_TEMPERATURE:
                self._transition(
                    TankState.HEATER_OFF,
                    event="温度达到 100℃",
                    guard="T ≥ 100℃",
                    action="断开继电器电源",
                )
            # 未达到 100℃ 时继续加热；这是加热状态的内部活动。
        elif self._state is TankState.HEATER_OFF:
            if temperature < MIN_HEATING_TEMPERATURE:
                self._transition(
                    TankState.CHECKING,
                    event="温度低于 20℃",
                    guard="T < 20℃",
                    action="重新检测水量",
                )
                self._evaluate_water_temperature(temperature, has_water)
        elif self._state is TankState.NO_WATER:
            if has_water:
                self._transition(
                    TankState.CHECKING,
                    event="水位恢复",
                    guard="检测到有水",
                    action="重新检测温度",
                )
                self._evaluate_water_temperature(temperature, has_water)
        elif self._state in {TankState.OFF, TankState.SLEEPING}:
            raise TankStateError(
                f"当前状态为“{self._state.value}”，请先上电或唤醒后再送入采样"
            )
        else:  # MAINTENANCE
            raise TankStateError("维修状态下不接收温度采样")

    def _evaluate_water_temperature(self, temperature: float, has_water: bool) -> None:
        if temperature >= MAX_HEATING_TEMPERATURE:
            self._transition(
                TankState.HEATER_OFF,
                event="温度检测",
                guard="T ≥ 100℃",
                action="断开电源",
            )
        elif temperature < MIN_HEATING_TEMPERATURE:
            if has_water:
                self._transition(
                    TankState.HEATING,
                    event="温度/水量检测",
                    guard="T < 20℃ 且 有水",
                    action="打开继电器电源，开始烧水",
                )
            else:
                self._transition(
                    TankState.NO_WATER,
                    event="温度/水量检测",
                    guard="T < 20℃ 且 无水",
                    action="不打开电源，等待补水",
                )
        else:
            self._transition(
                TankState.HEATER_OFF,
                event="温度检测",
                guard="20℃ ≤ T < 100℃",
                action="保持断开",
            )

    def on_clock(self, now: datetime | time | None = None) -> None:
        """处理 23:00 休眠与 07:00 恢复两个时间事件。"""

        clock = self._as_time(now)
        if clock.hour == SLEEP_HOUR and clock.minute == 0:
            self.go_to_sleep(now if isinstance(now, datetime) else None)
        elif clock.hour == WAKE_HOUR and clock.minute == 0:
            self.wake_up(now if isinstance(now, datetime) else None)

    def go_to_sleep(self, now: datetime | None = None) -> None:
        """23:00 断开电源并进入休眠；维修状态不自动覆盖。"""

        if self._state is TankState.SLEEPING:
            return
        if self._state is TankState.MAINTENANCE:
            self._relay_on = False
            return
        if self._state is TankState.OFF:
            raise TankStateError("设备未上电，无法进入休眠")
        self._transition(
            TankState.SLEEPING,
            event="23:00 定时事件",
            guard="",
            action="断开电源，进入休眠",
            at=now,
        )

    def wake_up(self, now: datetime | None = None) -> None:
        """07:00 从休眠恢复，重新进入恒温烧水过程。"""

        if self._state is not TankState.SLEEPING:
            if self._state is TankState.OFF:
                raise TankStateError("设备未上电，无法唤醒")
            return
        self._transition(
            TankState.CHECKING,
            event="07:00 定时事件",
            guard="",
            action="恢复供电，进入温度/水量检测",
            at=now,
        )

    def fault(self, reason: str = "水箱烧坏", now: datetime | None = None) -> None:
        """水箱故障时立即断电并进入维修状态。"""

        if self._state is TankState.MAINTENANCE:
            return
        if self._state is TankState.OFF:
            raise TankStateError("设备未上电，不存在运行故障")
        self._transition(
            TankState.MAINTENANCE,
            event="水箱故障",
            guard=reason,
            action="断开电源，等待维修",
            at=now,
        )

    def repair_completed(self, now: datetime | None = None) -> None:
        """维修完成后复位到检测状态，由下一次采样决定是否加热。"""

        if self._state is not TankState.MAINTENANCE:
            raise TankStateError("当前不在维修状态")
        self._transition(
            TankState.CHECKING,
            event="维修完成",
            guard="",
            action="复位，重新检测",
            at=now,
        )

    # ------------------------------------------------------------------ 内部
    def _transition(
        self,
        target: TankState,
        *,
        event: str,
        guard: str,
        action: str,
        at: datetime | None = None,
    ) -> None:
        record = TransitionRecord(
            source=self._state,
            event=event,
            guard=guard,
            target=target,
            action=action,
            at=at,
        )
        self._history.append(record)
        self._state = target
        if target in {
            TankState.HEATING,
        }:
            self._relay_on = True
        elif target in {
            TankState.HEATER_OFF,
            TankState.NO_WATER,
            TankState.SLEEPING,
            TankState.MAINTENANCE,
            TankState.CHECKING,
            TankState.OFF,
        }:
            self._relay_on = False

    @staticmethod
    def _as_time(value: datetime | time | None) -> time:
        if value is None:
            return datetime.now().time()
        if isinstance(value, datetime):
            return value.time()
        if isinstance(value, time):
            return value
        raise TypeError("now 必须是 datetime、time 或 None")

    def describe(self) -> str:
        """返回一行便于终端展示的当前快照。"""

        temperature = "--" if self._temperature is None else f"{self._temperature:g}℃"
        water = "--" if self._has_water is None else ("有水" if self._has_water else "无水")
        relay = "闭合" if self._relay_on else "断开"
        return (
            f"状态={self._state.value} | 温度={temperature} | "
            f"水位={water} | 继电器={relay}"
        )

    def format_history(self) -> str:
        return "\n".join(record.describe() for record in self._history)


def run_demo() -> None:
    """B1 的终端演示，供实验报告运行截图使用。"""

    controller = WaterTankController()
    print("[B1] 恒温水箱 20℃～100℃ 状态机")
    controller.power_on(datetime(2026, 11, 23, 6, 59, 59))
    print("  " + controller.describe())

    samples: Iterable[tuple[float, bool]] = [
        (18.0, True),
        (65.0, True),
        (100.0, True),
        (19.0, False),
        (19.0, True),
        (101.0, True),
    ]
    for temperature, water in samples:
        controller.update(temperature, water)
        water_text = "有水" if water else "无水"
        print(f"  采样 T={temperature:>5.1f}℃, {water_text} -> " + controller.describe())

    controller.on_clock(datetime(2026, 11, 23, 23, 0, 0))
    print("  23:00 -> " + controller.describe())
    controller.on_clock(datetime(2026, 11, 24, 7, 0, 0))
    controller.update(15.0, True)
    print("  07:00 + 低温采样 -> " + controller.describe())
    controller.fault("水箱烧坏", datetime(2026, 11, 24, 9, 0, 0))
    print("  故障 -> " + controller.describe())
    controller.repair_completed(datetime(2026, 11, 24, 10, 0, 0))
    print("  维修完成 -> " + controller.describe())
