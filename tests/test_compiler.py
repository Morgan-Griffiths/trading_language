from more_itertools.more import peekable
from src.compiler.dict_parser import DictParser
from src.compiler.compiler import Compiler


def test_symbol_pool(compiler: Compiler):
    text = "symbol_pool: positioning !biotech !earnings"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_symbol_pool(parsed_trade["symbol_pool"])
    assert res == ["positioning", "!biotech", "!earnings"]
    print(res)


def test_symbol_pool_symbol(compiler: Compiler):
    text = "symbol_pool: spy"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_symbol_pool(parsed_trade["symbol_pool"])
    assert res == ["load_symbols", "SPY"]
    print(res)


def test_symbol_pool_symbols(compiler: Compiler):
    text = "symbol_pool: spy tsla aapl"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_symbol_pool(parsed_trade["symbol_pool"])
    assert res == ["load_symbols", "SPY", "TSLA", "AAPL"]
    print(res)


def test_description_23rds(compiler: Compiler):
    text = """
        entry_point: 2/3rds"""
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade)
    res = compiler.parse_description_values(parsed_trade)
    assert res["entry_point"] == "2/3rds"


def test_parse_description_values(compiler: Compiler):
    text = """ 
    position_description:
        trade_type: sell_to_open
        asset_type: option
        position_type: spread
        betsize:
            per_trade: 1% * bankroll
            max_bet: 1% * bankroll
        entry_point: 2/3rds
        scheduled_close: 4
        spread:
            sell:
                strike: spy + spy * 0.3% * (days_until_opex - 3)
                expiration: opex
                contract_type: put
            buy:
                strike: round(spy - spy * 0.6% * (days_until_opex - 3))
                expiration: opex
                contract_type: put """
    parser = DictParser(text)
    parsed_trade: dict = parser.parse()
    res = compiler.parse_description_values(parsed_trade["position_description"])
    assert res == {
        "tradeType": "SELL_TO_OPEN",
        "assetType": "OPTION",
        "positionType": "spread",
        "betsize": {
            "per_trade": ["*", "^BANKROLL", 0.01],
            "max_bet": ["*", "^BANKROLL", 0.01],
        },
        "entry_point": "2/3rds",
        "scheduled_close": 4,
        "spread": {
            "sell": {
                "strike": [
                    "+",
                    "^SPY",
                    ["*", ["*", "^SPY", 0.003], ["-", "^DAYS_UNTIL_OPEX", 3]],
                ],
                "expiration": "^OPEX",
                "contractType": "PUT",
            },
            "buy": {
                "strike": [
                    "round",
                    [
                        "-",
                        "^SPY",
                        ["*", ["*", "^SPY", 0.006], ["-", "^DAYS_UNTIL_OPEX", 3]],
                    ],
                ],
                "expiration": "^OPEX",
                "contractType": "PUT",
            },
        },
    }


def test_on_market(compiler: Compiler):
    text = "on: market"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade)
    res = compiler.parse_on(peekable(parsed_trade["days"]))
    assert res == ["*"]
    print(res)


def test_on_range(compiler: Compiler):
    text = "on: Days 32-4"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade)
    res = compiler.parse_on(peekable(parsed_trade["days"]))
    assert res == ["32-4"]
    print(res)


def test_on_days(compiler: Compiler):
    text = "on: days 8 5 4"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_on(peekable(parsed_trade["days"]))
    assert res == ["8", "5", "4"]
    print(res)


def test_on_day(compiler: Compiler):
    text = "on: day 8"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_on(peekable(parsed_trade["days"]))
    assert res == ["8"]
    print(res)


def test_at(compiler: Compiler):
    text = "at: 9:30"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_at(peekable(parsed_trade["times"]))
    assert res == ["9:30"]
    print(res)


def test_at_multi(compiler: Compiler):
    text = "at: 9:30 10:30"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_at(peekable(parsed_trade["times"]))
    assert res == ["9:30", "10:30"]
    print(res)


def test_when(compiler: Compiler):
    text = """
    when:
        spy < 1.03 * spy_20_day_mean and
        spy > spy_20_day_mean"""
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_when(parsed_trade["when"], "open")
    assert res["and"] == [
        ["<", "^SPY", ["*", "^SPY_20_DAY_MEAN", 1.03]],
        [">", "^SPY", "^SPY_20_DAY_MEAN"],
    ]


def test_when_or(compiler: Compiler):
    text = """
    when:
        spy < 1.03 * spy_20_day_mean or
        spy > spy_20_day_mean"""
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_when(parsed_trade["when"], "close")
    assert res["or"] == [
        ["<", "^SPY", ["*", "^SPY_20_DAY_MEAN", 1.03]],
        [">", "^SPY", "^SPY_20_DAY_MEAN"],
    ]


def test_market(compiler: Compiler):

    text = """ 
    position_description:
        trade_type: sell_to_open
        asset_type: option
        position_type: spread
        betsize:
            per_trade: 1% * bankroll
            max_bet: 1% * bankroll
        entry_point: market
        scheduled_close: 4
        """
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    res = compiler.parse_description_values(parsed_trade["position_description"])
    assert res == {
        "tradeType": "SELL_TO_OPEN",
        "assetType": "OPTION",
        "positionType": "spread",
        "betsize": {
            "per_trade": ["*", "^BANKROLL", 0.01],
            "max_bet": ["*", "^BANKROLL", 0.01],
        },
        "entry_point": "MARKET",
        "scheduled_close": 4,
    }
