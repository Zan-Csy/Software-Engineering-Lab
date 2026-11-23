#!/usr/bin/env python3
"""软件工程实验四入口：运行三个状态机演示，或从源文件中提取字符串。

用法：
    python experiment4.py            # 运行 B1、B2、B3 全部演示
    python experiment4.py b1         # 只运行恒温水箱状态机
    python experiment4.py b2         # 只运行控制面板状态机
    python experiment4.py b3         # 只运行字符串提取演示
    python experiment4.py b3 a.java  # 从指定源文件提取字符串
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab4.control_panel import run_demo as run_control_panel_demo
from lab4.string_extractor import StringExtractionError, extract_strings, run_demo as run_extractor_demo
from lab4.water_tank import run_demo as run_water_tank_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="软件工程实验四：三个状态机的演示与字符串提取工具"
    )
    parser.add_argument(
        "exercise",
        nargs="?",
        default="all",
        choices=("all", "b1", "b2", "b3"),
        help="要运行的实验编号，默认全部运行",
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="B3 可选：待提取字符串的源文件路径",
    )
    return parser


def run_all() -> None:
    run_water_tank_demo()
    print()
    run_control_panel_demo()
    print()
    run_extractor_demo()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = build_parser().parse_args(argv)
    if args.exercise == "b1":
        run_water_tank_demo()
    elif args.exercise == "b2":
        run_control_panel_demo()
    elif args.exercise == "b3":
        if args.source is None:
            run_extractor_demo()
        else:
            try:
                text = args.source.read_text(encoding="utf-8-sig")
                values = extract_strings(text, source_name=str(args.source))
            except (OSError, UnicodeError, StringExtractionError) as error:
                print(f"错误：{error}", file=sys.stderr)
                return 1
            print(f"从 {args.source} 提取到 {len(values)} 个字符串：")
            for index, value in enumerate(values, start=1):
                print(f"{index:>2}. {value!r}")
    else:
        run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
