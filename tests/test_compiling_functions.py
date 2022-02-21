from more_itertools.more import peekable
from src.compiler.tokenizer import tokenize_strings
from src.symbol_filters.compile_functions import SymbolFilterCompiler


def test_column_filter_volume(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["volume", ">", "2m"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "stock_fundamentals",
        ["list", "None"],
        ["list", "Volume"],
        "@symbols",
        ">",
        2000000,
    ]
    print(res)


def test_column_filter(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["iv", ">", "50"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "IV",
        ["list", "None"],
        ["list", "Imp Vol"],
        "@symbols",
        ">",
        50,
    ]
    print(res)


def test_agg_column_volume(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["max", "(", "volume", "average volume", ")", ">", "2m"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_agg_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "stock_fundamentals",
        ["list", "max"],
        ["list", "Volume", "Average Volume"],
        "@symbols",
        ">",
        2000000.0,
    ]


def test_agg_abs_column_volume(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["max", "(", "abs", "(", "volume", "average volume", ")", ")", ">", "2m"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_agg_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "stock_fundamentals",
        ["list", "max", "abs"],
        ["list", "Volume", "Average Volume"],
        "@symbols",
        ">",
        2000000.0,
    ]


def test_column_agg(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [
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
        ]
    ]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_agg_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "positioning",
        ["list", "mean"],
        [
            "list",
            "scaled_direction_day_0",
            "scaled_direction_day_1",
            "scaled_direction_day_2",
            "scaled_direction_day_3",
            "scaled_direction_day_4",
        ],
        "@symbols",
        "<",
        -0.0025,
    ]
    print("res", res)


def test_not_in_portfolio(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["not", "in", "the", "portfolio"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_in_portfolio(peekable(tokens[0]))
    assert res == [
        "in_portfolio",
        "@symbols",
        False,
    ]


def test_portfolio(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["in", "the", "portfolio"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_in_portfolio(peekable(tokens[0]))
    assert res == [
        "in_portfolio",
        "@symbols",
        True,
    ]


def test_order_filter(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["order", "status", "rejected"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_order_filter(peekable(tokens[0]))
    assert res == ["filter_orders", "@symbols", "status", "rejected"]


def test_given_filter(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [
        [
            "given",
            "percent_away",
            ">",
            "70%",
            "and",
            "percent_away",
            "<",
            "150%",
            "select",
            "mean",
            "(",
            "abs",
            "(",
            "gamma",
            ")",
            ")",
            "<",
            "1%",
        ]
    ]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_given_filter(peekable(tokens[0]))
    assert res == [
        "filter_given",
        "greeks",
        [
            "list",
            ["list", "percent_away", ">", 0.7],
            ["list", "percent_away", "<", 1.5],
        ],
        ["list", "abs", "mean"],
        ["list", "gamma"],
        "@symbols",
        "<",
        0.01,
    ]


def test_price_filter(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["symbol_price", ">", "2"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_symbol_price(peekable(tokens[0]))
    assert res == ["filter_price", "@symbols", ">", 2]


def test_column_marketcap(symbol_filter_compiler: SymbolFilterCompiler):
    expr = [["marketcap", ">", "100"]]
    keyword = "symbol_filter"
    tokens = tokenize_strings(1, expr, keyword)
    res = symbol_filter_compiler.compile_column_filter(peekable(tokens[0]))
    assert res == [
        "filter_csv",
        "stock_fundamentals",
        ["list", "None"],
        ["list", "Market Cap"],
        "@symbols",
        ">",
        100,
    ]

    # marketcap = """symbol_filter:
    #     marketcap > 100"""

    # ["symbol_price", ">", "2"],
    # ["order", "status", "rejected"],

    # positioning = """symbol_filter:
    #     mean(positioning(days(0 to 4))) < -0.0025"""
    # volume = """symbol_filter:
    #     max(Volume,'average volume') > 2M"""
    # volume_multi = """symbol_filter:
    #     max(abs(Volume, 'average volume')) > 2M"""
    # volume_simple = """symbol_filter:
    #     Volume > 2M"""
    # price = """symbol_filter:
    #     symbol_price > 2"""
    # marketcap = """symbol_filter:
    #     marketcap > 100"""
    # given = """symbol_filter:
    # given percent_away > 70% and percent_away < 150% select mean(abs(gamma)) < 1%"""
    # answer_given = [
    #     "filter_given",
    #     "greeks",
    #     [
    #         "list",
    #         ["list", "percent_away", ">", 0.7],
    #         ["list", "percent_away", "<", 1.5],
    #     ],
    #     "[mean,abs]",
    #     "[gamma]",
    #     "@symbols",
    #     "<",
    #     0.01,
    # ]
