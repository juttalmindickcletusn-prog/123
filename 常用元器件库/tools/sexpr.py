"""KiCad S 表达式的最小解析/输出工具（符号库、封装文件都能用）。

parse(text) -> 嵌套 list；带引号的字符串解析成 Q（str 子类），其余原子是普通 str。
dump(node) -> 文本（制表符缩进，KiCad 能直接读）。
"""
from __future__ import annotations


class Q(str):
    """带引号的字符串原子。"""


def parse(text: str):
    i, n = 0, len(text)
    stack: list[list] = [[]]
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(":
            stack.append([])
            i += 1
        elif c == ")":
            node = stack.pop()
            stack[-1].append(node)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while True:
                ch = text[j]
                if ch == "\\":
                    nxt = text[j + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
                    j += 2
                    continue
                if ch == '"':
                    break
                buf.append(ch)
                j += 1
            stack[-1].append(Q("".join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()\"":
                j += 1
            stack[-1].append(text[i:j])
            i = j
    if len(stack) != 1:
        raise ValueError("括号不匹配")
    return stack[0][0] if len(stack[0]) == 1 else stack[0]


def _atom(a) -> str:
    if isinstance(a, Q):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    return str(a)


def dump(node, depth: int = 0) -> str:
    if not isinstance(node, list):
        return _atom(node)
    if not any(isinstance(x, list) for x in node):
        return "(" + " ".join(_atom(x) for x in node) + ")"
    pad = "\t" * (depth + 1)
    head = [x for x in node if not isinstance(x, list)]
    parts = ["(" + " ".join(_atom(x) for x in head)]
    for x in node:
        if isinstance(x, list):
            parts.append("\n" + pad + dump(x, depth + 1))
    return "".join(parts) + "\n" + "\t" * depth + ")"


def head(node) -> str | None:
    return node[0] if isinstance(node, list) and node and not isinstance(node[0], list) else None


def children(node, name: str) -> list:
    return [x for x in node if isinstance(x, list) and head(x) == name]


def child(node, name: str):
    c = children(node, name)
    return c[0] if c else None


def find_symbol(lib_node, name: str):
    for s in children(lib_node, "symbol"):
        if s[1] == name:
            return s
    return None
