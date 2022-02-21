from src.compiler.tokenizer import tokenize_strings
from src.compiler.syntax_validator import validate_syntax
from src.common_types import Number
import pytest


def test_simple_s_expr():
    expr = ["bankroll", "*", "1%"]
    keyword = "max_bet"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_complex_s_expr():
    expr = ["spy", "+", "spy", "*", "0.03%", "*", "(", "days_until_opex", "-", "3", ")"]
    keyword = "when"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_unary_s_expr():
    expr = [
        "round",
        "(",
        "spy",
        "+",
        "spy",
        "*",
        "0.06%",
        "*",
        "(",
        "days_until_opex",
        "-",
        "3",
        ")",
        ")",
    ]
    keyword = "when"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_bool_expr():
    expr = ["spy", "<", "1.03%", "*", "spy_20_day_mean"]
    keyword = "when"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_if_expr():
    expr = ["if", "net_position", "<", "0", "then", "buy", "else", "sell_short"]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_if_elif_expr():
    expr = [
        "if",
        "net_position",
        "<",
        "0",
        "then",
        "buy",
        "elif",
        "net_position",
        "==",
        "0",
        "then",
        "sell",
        "else",
        "sell_short",
    ]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_pool_expr_symbols():
    expr = ["spy", "tsla", "aapl"]
    keyword = "symbol_pool"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_pool_expr_positioning():
    expr = ["positioning", "!biotech", "!crypto"]
    keyword = "symbol_pool"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_strategy():
    expr = ["baliefj"]
    keyword = "strategy"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_days():
    expr = ["days", "7", "5", "4"]
    keyword = "on"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_day():
    expr = ["day", "4"]
    keyword = "on"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_day_range():
    expr = ["days", "30-4"]
    keyword = "on"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_time():
    expr = ["9:30"]
    keyword = "at"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_times():
    expr = ["9:30", "10:30"]
    keyword = "at"
    tokens = tokenize_strings(1, expr, keyword)
    res = validate_syntax(tokens, keyword)
    assert res == True


def test_symbol_filters():
    exprs = [
        ["volume", ">", "2m"],
        ["iv", ">", "50"],
        [
            "mean",
            "(",
            "positioning",
            "(",
            "days",
            "(",
            "0",
            "to",
            "4",
            ")",
            ")",
            ")",
            "<",
            "-0.0025",
        ],
        ["symbol_price", ">", "2"],
        ["order", "status", "rejected"],
    ]
    keyword = "symbol_filter"
    for expr in exprs:
        tokens = tokenize_strings(1, expr, keyword)
        res = validate_syntax(tokens, keyword)
        assert res == True
