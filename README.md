# 软件工程实验

本仓库为《软件工程》课程实验项目，按实验分目录归档。

| 目录 | 内容 |
| --- | --- |
| [`实验一/`](实验一/) | 软件工程实验一文档与 Python 示例 |
| [`实验二/`](实验二/) | 软件工程实验二报告、PDF 与 Rational Rose 源文件 |
| [`实验三/`](实验三/) | 软件工程实验三报告、Python 实现与 draw.io 类图 |
| [`实验四/`](实验四/) | 软件工程实验四报告、三个状态机、draw.io 状态图与测试 |

## 实验四

实验四围绕“面向对象的系统建模 B”完成三个状态机：

- B1 恒温水箱 20℃～100℃ 控制；
- B2 SafeHome 控制面板 ControlPanel 认证与锁定；
- B3 源文件双引号字符串提取。

代码使用 Python 实现，测试框架为 `unittest`；状态图使用 draw.io 绘制。
详见 [`实验四/README_实验四.md`](实验四/README_实验四.md) 和
[`实验四/202410120232-陈烁宇-软件工程实验四.docx`](实验四/202410120232-陈烁宇-软件工程实验四.docx)。

## 运行

```powershell
cd 实验四
python experiment4.py all
python -m unittest discover -s tests -v
```

## 仓库

<https://github.com/Zan-Csy/Software-Engineering-Lab>
