from typing import Callable
from more_itertools import peekable
from more_itertools.more import value_chain
from src.common_types import (
    CSV,
    Aggregator,
    Binary,
    Column,
    Context,
    Database,
    Group,
    Name,
    Range,
    Restriction,
    Separator,
    Unary,
    Variable,
    Number,
    Symbol,
    Value,
    Conditional,
    type_mapping,
    unary_types,
    restriction_types,
)
from src.compiler.utils import is_member

""" 
s_expr -> value: left op s_expr
left: Variable | Context | Number  
op: Math Operator

unary s_expr -> Number: op left
op: round | -
left: variable | context | number

if_expr: if expr then value else value
expr -> bool: left op right
left: Variable | Context
right: Number | Variable | Context
op: boolean operator

func_expr: func, *args
func: string name
args: list | variable | value | number | string
"""


def s_error(expr):
    raise ValueError(f"Improper s expr {expr}")


def is_expr(
    tokens: peekable, allowable_types=[Symbol, Variable, Context, Number, Group, Unary]
):
    if bool(tokens) and not is_member(tokens.peek(), [Conditional]):
        assert is_member(
            tokens.peek(), allowable_types
        ), f"Expected {allowable_types},got {tokens.peek()}"
        if is_member(tokens.peek(), [Symbol, Variable, Context, Number]):
            allowable = [Binary, Group]
        elif is_member(tokens.peek(), [Binary]):
            allowable = [Symbol, Variable, Context, Number, Group]
        elif is_member(tokens.peek(), [Group]):
            allowable = [Symbol, Variable, Context, Number, Group]
        elif is_member(tokens.peek(), [Unary]):
            allowable = [Group]
        else:
            raise ValueError(f"Err {tokens}")
        next(tokens)
        is_expr(tokens, allowable)
    return True


# if net_position < 0 then BUY else SELL_SHORT
def if_expr(tokens):
    assert tokens.peek().lexeme == "if"
    next(tokens)
    is_expr(tokens)
    assert tokens.peek().lexeme == "then"
    next(tokens)
    assert is_member(tokens.peek(), [Value])
    next(tokens)
    while tokens.peek().lexeme == "elif":
        next(tokens)
        is_expr(tokens)
        assert tokens.peek().lexeme == "then"
        next(tokens)
        assert is_member(tokens.peek(), [Value])
        next(tokens)
    assert tokens.peek().lexeme == "else"
    next(tokens)
    assert is_member(tokens.peek(), [Value])
    return True


# Any string
def name_expr(tokens):
    assert is_member(tokens.peek(), [Name])
    return True


# list of symbols, or positioning + restrictions
def pool_expr(tokens):
    if is_member(tokens.peek(), [Symbol]):
        while bool(tokens):
            assert is_member(tokens.peek(), [Symbol])
            next(tokens)
    elif is_member(tokens.peek(), [CSV]):
        next(tokens)
        while bool(tokens):
            assert is_member(tokens.peek(), [Restriction])
            next(tokens)
    else:
        raise ValueError(f"Invalid Pool expression")
    return True


# market, days 1 5 7, days 31-4,day 4
def day_expr(tokens):
    if tokens.peek().lexeme == "market":
        next(tokens)
        assert bool(tokens) is False
    elif is_member(tokens.peek(), [Range]):
        next(tokens)
        while not bool(tokens):
            assert is_member(tokens.peek(), [Number])
            next(tokens)
    return True


# hr:min hr:min
def time_expr(tokens):
    while not bool(tokens):
        assert is_member(tokens.peek(), [Number])
    return True


# symbol expressions
def symbol_filter_expr(tokens, allowable=[Database, Column, Aggregator, Variable]):
    # Should pull from compiling functions
    assert is_member(tokens.peek(), allowable)
    return True


keyword_grammar: dict[str, Callable] = {
    "strategy": name_expr,
    "symbol_pool": pool_expr,
    "when": is_expr,
    "on": day_expr,
    "at": time_expr,
    "symbol_filter": symbol_filter_expr,
    "trade_type": if_expr,
    "position_type": if_expr,
    "asset_type": if_expr,
    "entry_point": is_expr,
    "scheduled_close": is_expr,
    "stop": is_expr,
    "per_trade": is_expr,
    "max_bet": is_expr,
    "put_call": if_expr,
    "strike": is_expr,
    "expiration": is_expr,
    "contract_type": if_expr,
}


def validate_syntax(tokens: list, keyword: str) -> bool:
    tokens = peekable(tokens)
    func: Callable = keyword_grammar[keyword]
    check = func(tokens)
    return check
