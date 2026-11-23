"""B2：SafeHome 控制面板 ControlPanel 状态机。

控制面板只接受数字键。密码固定为 4 位；每输满 4 位校验一次，连续错误
3 次后锁定 120 秒，锁定期间拒绝按键。超时后错误次数清零，户主可以重新
输入。密码正确后进入系统功能选择状态。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


PASSWORD_LENGTH = 4
MAX_FAILED_ATTEMPTS = 3
LOCK_SECONDS = 120.0


class ControlPanelState(Enum):
    """控制面板的五个状态。"""

    IDLE = "空闲/待机"
    READING = "读取键入字符"
    VERIFYING = "密码校验"
    SYSTEM_MENU = "系统功能选择"
    LOCKED = "锁定"


class PanelError(RuntimeError):
    """控制面板异常基类。"""


class PanelLockedError(PanelError):
    """在锁定期间按键。"""

    def __init__(self, remaining_seconds: float) -> None:
        self.remaining_seconds = max(0.0, remaining_seconds)
        super().__init__(f"控制面板已锁定，请等待 {self.remaining_seconds:.0f} 秒")


class PanelStateError(PanelError):
    """当前状态不接受该操作。"""


@dataclass(frozen=True)
class PressResult:
    """一次按键后的反馈，便于界面层展示。"""

    state: ControlPanelState
    message: str
    failed_attempts: int
    locked: bool = False


class ControlPanel:
    """纯逻辑控制面板；时间由调用方注入，便于测试 120 秒锁定。"""

    def __init__(self, password: str = "1234") -> None:
        if len(password) != PASSWORD_LENGTH or not password.isdigit():
            raise ValueError("密码必须是 4 位数字")
        self._password = password
        self._state = ControlPanelState.IDLE
        self._buffer = ""
        self._failed_attempts = 0
        self._locked_at: datetime | None = None
        self._last_now = datetime.now()
        self._message = "等待户主按键"

    # ------------------------------------------------------------------ 查询
    @property
    def state(self) -> ControlPanelState:
        return self._state

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    @property
    def message(self) -> str:
        return self._message

    @property
    def buffer_length(self) -> int:
        return len(self._buffer)

    @property
    def display(self) -> str:
        """安全键盘的掩码显示，不暴露已输入的数字。"""

        return "*" * len(self._buffer)

    @property
    def is_locked(self) -> bool:
        return self._state is ControlPanelState.LOCKED

    @property
    def is_authenticated(self) -> bool:
        return self._state is ControlPanelState.SYSTEM_MENU

    # ------------------------------------------------------------------ 事件
    def press_key(self, key: str, now: datetime | None = None) -> PressResult:
        """按下一个数字键。

        锁定期间按键会抛出 :class:`PanelLockedError`；锁定满 120 秒后，
        本次按键会被当作解锁后的第一次输入。
        """

        if len(key) != 1 or not key.isdigit():
            raise ValueError("控制面板只接受单个数字键")
        current = now or datetime.now()
        self._last_now = current

        if self._state is ControlPanelState.LOCKED:
            self._unlock_if_ready(current)
            if self._state is ControlPanelState.LOCKED:
                raise PanelLockedError(self.remaining_lock_seconds(current))

        if self._state is ControlPanelState.SYSTEM_MENU:
            raise PanelStateError("当前处于系统功能选择状态，请先退出")
        if self._state is ControlPanelState.IDLE:
            self._state = ControlPanelState.READING
            self._message = "开始读取键入字符"

        self._buffer += key
        if len(self._buffer) < PASSWORD_LENGTH:
            self._message = f"已输入 {len(self._buffer)} 位，继续输入"
            return self._result()

        # 达到密码长度：先进入校验状态，再根据比较结果迁移。
        self._state = ControlPanelState.VERIFYING
        return self._verify(current)

    def poll(self, now: datetime | None = None) -> ControlPanelState:
        """轮询锁定计时器，超时后自动解除锁定。"""

        if self._state is ControlPanelState.LOCKED:
            current = now or datetime.now()
            self._last_now = current
            self._unlock_if_ready(current)
        return self._state

    def exit_system_menu(self) -> None:
        """从系统功能选择返回空闲状态，供下一次身份认证。"""

        if self._state is not ControlPanelState.SYSTEM_MENU:
            raise PanelStateError("当前不在系统功能选择状态")
        self._buffer = ""
        self._failed_attempts = 0
        self._locked_at = None
        self._state = ControlPanelState.IDLE
        self._message = "已退出系统功能选择"

    def reset(self) -> None:
        """清除输入、错误次数和锁定计时，恢复到初始状态。"""

        self._state = ControlPanelState.IDLE
        self._buffer = ""
        self._failed_attempts = 0
        self._locked_at = None
        self._message = "等待户主按键"

    def remaining_lock_seconds(self, now: datetime | None = None) -> float:
        if self._state is not ControlPanelState.LOCKED or self._locked_at is None:
            return 0.0
        elapsed = (now or datetime.now()) - self._locked_at
        return max(0.0, LOCK_SECONDS - elapsed.total_seconds())

    # ------------------------------------------------------------------ 内部
    def _verify(self, now: datetime) -> PressResult:
        entered = self._buffer
        self._buffer = ""

        if entered == self._password:
            self._failed_attempts = 0
            self._locked_at = None
            self._state = ControlPanelState.SYSTEM_MENU
            self._message = "密码正确，进入系统功能选择"
            return self._result()

        self._failed_attempts += 1
        if self._failed_attempts >= MAX_FAILED_ATTEMPTS:
            self._state = ControlPanelState.LOCKED
            self._locked_at = now
            self._message = "密码连续错误 3 次，控制面板锁定 120 秒"
            return self._result(locked=True)

        self._state = ControlPanelState.READING
        left = MAX_FAILED_ATTEMPTS - self._failed_attempts
        self._message = f"密码错误，还可尝试 {left} 次"
        return self._result()

    def _unlock_if_ready(self, now: datetime) -> None:
        if self._state is not ControlPanelState.LOCKED or self._locked_at is None:
            return
        if self.remaining_lock_seconds(now) <= 0:
            self._state = ControlPanelState.READING
            self._failed_attempts = 0
            self._locked_at = None
            self._buffer = ""
            self._message = "锁定时间已到，允许重新输入"

    def _result(self, locked: bool = False) -> PressResult:
        return PressResult(
            state=self._state,
            message=self._message,
            failed_attempts=self._failed_attempts,
            locked=locked,
        )

    def describe(self) -> str:
        lock = (
            f" 剩余锁定={self.remaining_lock_seconds(self._last_now):.0f}s"
            if self._state is ControlPanelState.LOCKED
            else ""
        )
        return (
            f"状态={self._state.value} | 输入={self.display or '—'} | "
            f"错误次数={self._failed_attempts}{lock}"
        )


def run_demo() -> None:
    """B2 的终端演示：正确登录、三次错误锁定、超时解锁。"""

    clock = datetime(2026, 11, 23, 9, 0, 0)
    panel = ControlPanel()
    print("[B2] SafeHome 控制面板 ControlPanel 状态机")

    for key in "12":
        panel.press_key(key, clock)
        print("  按键 1/2 -> " + panel.describe())
    panel.press_key("3", clock)
    panel.press_key("4", clock)
    print("  输入 1234 -> " + panel.describe())

    panel.exit_system_menu()
    for attempt in range(1, 4):
        for key in "0000":
            result = panel.press_key(key, clock)
        print(f"  第 {attempt} 次错误密码 -> " + panel.describe())
        if result.locked:
            break

    try:
        panel.press_key("1", clock)
    except PanelLockedError as error:
        print(f"  锁定期间按键被拒绝：{error}")

    clock = clock.replace(minute=2)
    panel.poll(clock)
    print("  120 秒后 -> " + panel.describe())
    for key in "1234":
        panel.press_key(key, clock)
    print("  重新输入 1234 -> " + panel.describe())
