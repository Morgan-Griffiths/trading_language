from src.compiler.tokenizer import tokenize_strings
from src.utils import to_readable


def test_tokenizer():
    expr = ["1%", "*", "bankroll"]
    res = tokenize_strings(1, expr, "blah")
    print(res)


def test_complex():
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


def test_if():
    expr = ["if", "net_position", "<", "0", "then", "buy", "else", "sell_short"]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)


def test_day():
    expr = ["day", "4"]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)


def test_days():
    expr = ["days", "7", "5", "4"]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)


def test_day_range():
    expr = ["days", "30-4"]
    keyword = "trade_type"
    tokens = tokenize_strings(1, expr, keyword)


def test_time():
    expr = ["9:30"]
    keyword = "at"
    tokens = tokenize_strings(1, expr, keyword)
    # assert


def test_times():
    expr = ["9:30", "10:30"]
    keyword = "at"
    tokens = tokenize_strings(1, expr, keyword)


def test_symbol_filter():
    expr = [
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
    keyword = "at"
    tokens = tokenize_strings(1, expr, keyword)
    res = to_readable(tokens)
    assert res == expr


def test_nested():
    expr = [
        ["<", "spy", ["*", "spy_20_day_mean", "1.03"]],
        [">", "spy", "spy_20_day_mean"],
    ]
    keyword = "when"
    tokens = tokenize_strings(1, expr, keyword)
    res = to_readable(tokens)
    assert res == expr
