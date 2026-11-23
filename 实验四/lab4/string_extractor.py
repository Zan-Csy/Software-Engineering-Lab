"""B3：从源代码文本中提取双引号字符串的状态机。

状态只有三个：

* ``NORMAL``    —— 字符串之外，忽略普通字符；
* ``IN_STRING`` —— 位于双引号字符串内，普通字符写入缓冲区；
* ``ESCAPED``   —— 刚读到反斜杠，下一个字符原样写入缓冲区。

反斜杠只负责取消下一个字符的特殊含义，不做 ``\\n``、``\\t`` 等转义
解释。例如 ``\\\"`` 输出双引号本身，``\\\\`` 输出一个反斜杠。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExtractState(Enum):
    """字符串提取状态机的三个状态。"""

    NORMAL = "普通文本"
    IN_STRING = "字符串读取"
    ESCAPED = "转义读取"


class StringExtractionError(ValueError):
    """源文件中的字符串不合法。"""

    def __init__(self, message: str, *, source_name: str, line: int, column: int) -> None:
        self.source_name = source_name
        self.line = line
        self.column = column
        super().__init__(f"{source_name}:{line}:{column}: {message}")


class UnterminatedStringError(StringExtractionError):
    """文件结束时仍有字符串没有闭合。"""


@dataclass(frozen=True)
class StringLiteral:
    """提取到的一个字符串及其起始位置（均为 1 开始）。"""

    value: str
    line: int
    column: int


def extract_strings_with_positions(
    source: str,
    *,
    source_name: str = "<string>",
) -> list[StringLiteral]:
    """按状态机扫描源码，返回全部双引号字符串及其起始位置。"""

    state = ExtractState.NORMAL
    literals: list[StringLiteral] = []
    buffer: list[str] = []
    opening_line = 1
    opening_column = 1
    line = 1
    column = 1

    for character in source:
        if state is ExtractState.NORMAL:
            if character == '"':
                state = ExtractState.IN_STRING
                buffer.clear()
                opening_line, opening_column = line, column
        elif state is ExtractState.IN_STRING:
            if character == "\\":
                state = ExtractState.ESCAPED
            elif character == '"':
                literals.append(
                    StringLiteral(
                        value="".join(buffer),
                        line=opening_line,
                        column=opening_column,
                    )
                )
                buffer.clear()
                state = ExtractState.NORMAL
            else:
                buffer.append(character)
        else:  # ExtractState.ESCAPED
            # 反斜杠只取消下一个字符的特殊含义，保留该字符本身。
            buffer.append(character)
            state = ExtractState.IN_STRING

        if character == "\n":
            line += 1
            column = 1
        else:
            column += 1

    if state is not ExtractState.NORMAL:
        detail = "字符串没有闭合" if state is ExtractState.IN_STRING else "反斜杠后缺少字符"
        raise UnterminatedStringError(
            detail,
            source_name=source_name,
            line=opening_line,
            column=opening_column,
        )

    return literals


def extract_strings(source: str, *, source_name: str = "<string>") -> list[str]:
    """返回源码中的全部字符串内容（不含两侧双引号）。"""

    return [
        literal.value
        for literal in extract_strings_with_positions(source, source_name=source_name)
    ]


def run_demo() -> None:
    """B3 的终端演示，包含题目中的转义示例。"""

    print("[B3] 源文件字符串提取状态机")
    sample = (
        'String s = "一般学习一门编程语言的时候，基本上第一个程序是输出'
        '\\"Hello World!\\"";  // 转义双引号'
    )
    print(f"  输入片段：{sample}")
    print(f"  提取结果：{extract_strings(sample, source_name='Demo.java')}")

    tricky = r'"C:\\Users\\ Zan" "" "a\\\"b"'
    print(f"  复杂样例：{tricky}")
    print(f"  提取结果：{extract_strings(tricky, source_name='tricky.txt')}")

    try:
        extract_strings('ok = "闭合"; bad = "未闭合', source_name="bad.py")
    except UnterminatedStringError as error:
        print(f"  异常样例：{error}")
