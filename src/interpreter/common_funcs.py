from dataclasses import dataclass
from typing import Callable


@dataclass
class ReversibleFunction:
    forward: Callable
    backward: Callable


class PythonFunction(ReversibleFunction):
    ...


class Binary(ReversibleFunction):
    ...


pythonOperators = {
    "round": PythonFunction(lambda x: round(x, 0), lambda x: x),
    "list": PythonFunction(lambda *args: list(args), lambda *args: list(args)),
    "dict": PythonFunction(lambda *args: dict(args), lambda *args: dict(args)),
}
binaryOperators = {
    "-": Binary(lambda x, y: x - y, lambda x, y: x + y),
    "+": Binary(lambda x, y: x + y, lambda x, y: x - y),
    "*": Binary(lambda x, y: x * y, lambda x, y: x / y),
    "/": Binary(lambda x, y: x / y, lambda x, y: x * y),
    "==": Binary(lambda x, y: x == y, lambda x, y: x != y),
    "!=": Binary(lambda x, y: x != y, lambda x, y: x == y),
    "and": Binary(lambda x, y: x and y, lambda x, y: x and y),
    "or": Binary(lambda x, y: x or y, lambda x, y: not x and not y),
    ">": Binary(lambda x, y: x > y, lambda x, y: x <= y),
    "<": Binary(lambda x, y: x < y, lambda x, y: x >= y),
    ">=": Binary(lambda x, y: x >= y, lambda x, y: x < y),
    "<=": Binary(lambda x, y: x <= y, lambda x, y: x > y),
}
