"""实验四三个状态机的单元测试。

运行：python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from lab4.control_panel import (
    ControlPanel,
    ControlPanelState,
    PanelLockedError,
    PanelStateError,
)
from lab4.string_extractor import (
    UnterminatedStringError,
    extract_strings,
    extract_strings_with_positions,
)
from lab4.water_tank import TankState, TankStateError, WaterTankController


class WaterTankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tank = WaterTankController()
        self.tank.power_on()

    def test_power_on_enters_checking(self) -> None:
        self.assertEqual(self.tank.state, TankState.CHECKING)
        self.assertFalse(self.tank.relay_on)
        self.assertTrue(self.tank.is_running)

    def test_cold_with_water_starts_heating(self) -> None:
        self.tank.update(18.0, True)
        self.assertEqual(self.tank.state, TankState.HEATING)
        self.assertTrue(self.tank.relay_on)

    def test_cold_without_water_does_not_heat(self) -> None:
        self.tank.update(18.0, False)
        self.assertEqual(self.tank.state, TankState.NO_WATER)
        self.assertFalse(self.tank.relay_on)

    def test_temperature_between_thresholds_keeps_heater_off(self) -> None:
        self.tank.update(20.0, True)
        self.assertEqual(self.tank.state, TankState.HEATER_OFF)
        self.tank.update(99.9, True)
        self.assertEqual(self.tank.state, TankState.HEATER_OFF)
        self.assertFalse(self.tank.relay_on)

    def test_reaching_100_stops_heating(self) -> None:
        self.tank.update(19.0, True)
        self.tank.update(100.0, True)
        self.assertEqual(self.tank.state, TankState.HEATER_OFF)
        self.assertFalse(self.tank.relay_on)

    def test_cooling_below_20_restarts_detection_and_heating(self) -> None:
        self.tank.update(18.0, True)
        self.tank.update(100.0, True)
        self.tank.update(19.0, True)
        self.assertEqual(self.tank.state, TankState.HEATING)
        self.assertTrue(self.tank.relay_on)

    def test_water_restored_after_no_water(self) -> None:
        self.tank.update(10.0, False)
        self.assertEqual(self.tank.state, TankState.NO_WATER)
        self.tank.update(10.0, True)
        self.assertEqual(self.tank.state, TankState.HEATING)

    def test_23_sleep_and_7_wake(self) -> None:
        self.tank.update(18.0, True)
        self.tank.on_clock(datetime(2026, 11, 23, 23, 0, 0))
        self.assertEqual(self.tank.state, TankState.SLEEPING)
        self.assertFalse(self.tank.relay_on)
        self.tank.on_clock(datetime(2026, 11, 24, 7, 0, 0))
        self.assertEqual(self.tank.state, TankState.CHECKING)

    def test_clock_ignores_non_exact_minutes(self) -> None:
        self.tank.on_clock(datetime(2026, 11, 23, 22, 59, 0))
        self.assertEqual(self.tank.state, TankState.CHECKING)
        self.tank.on_clock(datetime(2026, 11, 23, 23, 1, 0))
        self.assertEqual(self.tank.state, TankState.CHECKING)

    def test_fault_and_repair(self) -> None:
        self.tank.update(30.0, True)
        self.tank.fault("温控失效")
        self.assertEqual(self.tank.state, TankState.MAINTENANCE)
        self.assertFalse(self.tank.relay_on)
        self.tank.repair_completed()
        self.assertEqual(self.tank.state, TankState.CHECKING)

    def test_cannot_power_on_twice(self) -> None:
        with self.assertRaises(TankStateError):
            self.tank.power_on()

    def test_rejects_impossible_temperature(self) -> None:
        with self.assertRaises(ValueError):
            self.tank.update(200.0, True)


class ControlPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 11, 23, 9, 0, 0)
        self.panel = ControlPanel(password="1234")

    def press(self, digits: str, at: datetime | None = None) -> None:
        for digit in digits:
            self.panel.press_key(digit, at or self.start)

    def test_correct_password_enters_system_menu(self) -> None:
        self.press("1234")
        self.assertEqual(self.panel.state, ControlPanelState.SYSTEM_MENU)
        self.assertTrue(self.panel.is_authenticated)
        self.assertEqual(self.panel.failed_attempts, 0)

    def test_partial_password_stays_reading(self) -> None:
        self.press("12")
        self.assertEqual(self.panel.state, ControlPanelState.READING)
        self.assertEqual(self.panel.buffer_length, 2)
        self.assertEqual(self.panel.display, "**")

    def test_one_wrong_password_allows_retry(self) -> None:
        self.press("0000")
        self.assertEqual(self.panel.state, ControlPanelState.READING)
        self.assertEqual(self.panel.failed_attempts, 1)
        self.press("1234")
        self.assertEqual(self.panel.state, ControlPanelState.SYSTEM_MENU)

    def test_three_wrong_passwords_lock_panel(self) -> None:
        for _ in range(3):
            self.press("0000")
        self.assertEqual(self.panel.state, ControlPanelState.LOCKED)
        self.assertEqual(self.panel.failed_attempts, 3)
        self.assertAlmostEqual(self.panel.remaining_lock_seconds(self.start), 120.0)

    def test_locked_panel_rejects_key(self) -> None:
        for _ in range(3):
            self.press("0000")
        with self.assertRaises(PanelLockedError):
            self.panel.press_key("1", self.start + timedelta(seconds=119))

    def test_lock_expires_after_120_seconds(self) -> None:
        for _ in range(3):
            self.press("0000")
        later = self.start + timedelta(seconds=120)
        state = self.panel.poll(later)
        self.assertEqual(state, ControlPanelState.READING)
        self.assertEqual(self.panel.failed_attempts, 0)
        self.press("1234", later)
        self.assertEqual(self.panel.state, ControlPanelState.SYSTEM_MENU)

    def test_key_after_expiry_is_accepted(self) -> None:
        for _ in range(3):
            self.press("0000")
        later = self.start + timedelta(seconds=120)
        self.panel.press_key("1", later)
        self.assertEqual(self.panel.state, ControlPanelState.READING)
        self.assertEqual(self.panel.buffer_length, 1)

    def test_exit_system_menu(self) -> None:
        self.press("1234")
        self.panel.exit_system_menu()
        self.assertEqual(self.panel.state, ControlPanelState.IDLE)

    def test_reject_non_digit_key(self) -> None:
        with self.assertRaises(ValueError):
            self.panel.press_key("a")

    def test_reject_bad_password_configuration(self) -> None:
        with self.assertRaises(ValueError):
            ControlPanel(password="12ab")


class StringExtractorTests(unittest.TestCase):
    def test_extract_textbook_example(self) -> None:
        source = (
            'String s = "一般学习一门编程语言的时候，基本上第一个程序是输出'
            '\\"Hello World!\\"";'
        )
        self.assertEqual(
            extract_strings(source),
            ["一般学习一门编程语言的时候，基本上第一个程序是输出\"Hello World!\""],
        )

    def test_multiple_strings_and_empty_string(self) -> None:
        source = 'a = "first"; b = ""; c = "third";'
        self.assertEqual(extract_strings(source), ["first", "", "third"])

    def test_escaped_quote_is_content(self) -> None:
        source = r'"say \"hi\""'
        self.assertEqual(extract_strings(source), ['say "hi"'])

    def test_double_backslash_becomes_one(self) -> None:
        source = r'"C:\\temp\\file"'
        self.assertEqual(extract_strings(source), [r"C:\temp\file"])

    def test_backslash_before_ordinary_char_keeps_char(self) -> None:
        source = r'"a\nb"'
        self.assertEqual(extract_strings(source), ["anb"])

    def test_ignore_text_outside_strings(self) -> None:
        source = "print('single'); // 这里没有双引号"
        self.assertEqual(extract_strings(source), [])

    def test_unterminated_string_reports_position(self) -> None:
        source = 'ok = "closed";\nbad = "open'
        with self.assertRaises(UnterminatedStringError) as context:
            extract_strings(source, source_name="demo.py")
        self.assertEqual(context.exception.line, 2)
        self.assertEqual(context.exception.column, 7)
        self.assertIn("demo.py:2:7", str(context.exception))

    def test_backslash_at_eof_is_error(self) -> None:
        with self.assertRaises(UnterminatedStringError):
            extract_strings('"abc\\', source_name="eof.txt")

    def test_positions_of_strings(self) -> None:
        literals = extract_strings_with_positions('x = "a"\n"b"', source_name="s.txt")
        self.assertEqual([(item.value, item.line, item.column) for item in literals], [
            ("a", 1, 5),
            ("b", 2, 1),
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
