from dataclasses import dataclass
from more_itertools import peekable
from typing import Iterator, Union, Literal, Callable, Iterable, Any

from src.common_types import (
    Conditional,
    Symbol,
    Value,
    Variable,
    Number,
    value_mapping,
    context_types,
    variable_types,
    symbol_types,
)
from src.compiler.utils import is_member
from src.compiler.tokenizer import Token

Assoc = Union[Literal["left"], Literal["right"]]


@dataclass
class Binary:
    token: str
    assoc: Assoc
    prec: int


@dataclass
class UnaryPrefix:
    token: str
    prec: int


@dataclass
class UnaryPostfix:
    token: str
    prec: int


@dataclass
class BooleanInfix:
    token: str
    assoc: Assoc
    prec: int


@dataclass
class Group:
    open: str
    close: str


Op = Union[Binary, UnaryPrefix, UnaryPostfix, Group]


def add_prefix(lexeme: Any):
    if isinstance(lexeme, str):
        if lexeme in context_types or lexeme in symbol_types:
            return "^" + lexeme.upper()
        elif lexeme in variable_types:
            return "@" + lexeme.upper()
    return lexeme


class Parser:
    def __init__(self) -> None:
        self.prec = {}
        self.binary = set()
        self.unary_prefix = set()
        self.unary_postfix = set()
        self.assoc_left = set()
        self.groups = {}
        operators = [
            Binary(token=">", assoc="left", prec=1),
            Binary(token="<", assoc="left", prec=1),
            Binary(token=">=", assoc="left", prec=1),
            Binary(token="<=", assoc="left", prec=1),
            Binary(token="+", assoc="left", prec=2),
            Binary(token="-", assoc="left", prec=2),
            Binary(token="*", assoc="left", prec=3),
            Binary(token="/", assoc="left", prec=3),
            UnaryPrefix(token="round", prec=4),
            Group(open="(", close=")"),
        ]
        for operator in operators:
            if isinstance(operator, Binary):
                self.prec[operator.token] = operator.prec
                self.binary.add(operator.token)
                if operator.assoc == "left":
                    self.assoc_left.add(operator.token)
            elif isinstance(operator, UnaryPrefix):
                self.prec[operator.token] = operator.prec
                self.unary_prefix.add(operator.token)
            elif isinstance(operator, UnaryPostfix):
                self.prec[operator.token] = operator.prec
                self.unary_postfix.add(operator.token)
            elif isinstance(operator, Group):
                self.groups[operator.open] = operator.close

    def parse_s_expr(self, tokens: Iterator[Token]) -> list:
        return self._parse(peekable(tokens))

    def parse_if_expr(self, tokens: peekable, values=[]) -> dict[str, list]:
        if tokens.peek().lexeme == "elif" or tokens.peek().lexeme == "if":
            next(tokens)
            if_expr = self.parse_s_expr(tokens)
            assert is_member(
                tokens.peek(), [Variable, Number, Value, Symbol]
            ), f"Expected type left found {tokens.peek()}"
            values.append([if_expr, tokens.peek().lexeme])
            self.parse_if_expr(tokens, values)
        elif tokens.peek().lexeme == "else":
            next(tokens)
            else_value = self.parse_s_expr(tokens)
            values.append([True, else_value])
        return {"if": values}

    def parse_value_expr(self, tokens: peekable):
        # either value or if expr
        if is_member(tokens.peek(), [Value]):
            res = value_mapping[tokens.peek().lexeme]
            next(tokens)
            assert bool(tokens) is False
        elif is_member(tokens.peek(), [Conditional]):
            res = self.parse_if_expr(tokens)
        else:
            raise ValueError(f"Bad Syntax {tokens.peek()}")
        return res

    def _no_left(self, p: peekable):
        if p.peek().lexeme in self.groups:
            end = self.groups[p.peek().lexeme]
            next(p)
            res = self._parse(p, 0)
            assert next(p).lexeme == end
            return res
        if p.peek().lexeme in self.unary_prefix:
            op = p.peek().lexeme
            next(p)
            return [op, self._no_left(p)]
        return add_prefix(convert_number(next(p)))

    def _parse(self, p: peekable, precedence=0):
        print(p.peek().lexeme)
        res = self._no_left(p)
        while p:
            if p.peek().lexeme in self.binary:
                if p.peek().lexeme in self.assoc_left:
                    if self.prec[p.peek().lexeme] <= precedence:
                        break
                else:
                    if self.prec[p.peek().lexeme] < precedence:
                        break
                op = next(p).lexeme
                if isinstance(res, int) or isinstance(res, float):
                    res = [op, self._parse(p, self.prec[op]), res]
                else:
                    res = [op, res, self._parse(p, self.prec[op])]
            elif p.peek().lexeme in self.unary_postfix:
                op = next(p)
                res = [op, res]
            else:
                break
        return res


def convert_number(token: Token):
    if is_member(token, [Number]):
        num_type = "INT"
        number = ""
        operation = lambda a: a
        for dig in token.lexeme:
            # auto passes commas
            if dig.isdigit() or dig == "-":
                number += dig
            elif dig == ".":
                num_type = "REAL"
                number += dig
            elif dig == "%":
                num_type = "REAL"
                operation = lambda a: a / 1e2
            elif dig == "k":
                operation = lambda a: a * 1e3
            elif dig == "m":
                operation = lambda a: a * 1e6
            elif dig == "b":
                operation = lambda a: a * 1e9
        if num_type == "REAL":
            return operation(float(number))
        else:
            return operation(int(number))
    else:
        return token.lexeme
