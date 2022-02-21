from src.compiler.dict_parser import DictParser
from src.utils import to_readable

expr = """
strategy: SPY
symbol_pool: spy
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
            strike: round(SPY - SPY * 0.6% * (days_until_opex - 3))
            expiration: opex
            contract_type: put
open_position:
	On:	Days 32-4
	At:	9:30
	When:
		spy < 1.03 * spy_20_day_mean and
		spy > spy_20_day_mean
	symbol_filter:
		not in the portfolio
close_position:
	On: days 31-4
	At: 9:30
	When:
		spy < spy_20_day_mean or 
		spy > spy_20_day_mean * 1.03"""


def test_unary():
    expr1 = """when:
                spy_20_day_mean * -1.03"""
    lex = DictParser(expr1)
    res = lex.parse()
    print(res)


def test_day():
    expr1 = "On: days 31-4"
    lex = DictParser(expr1)
    res = lex.parse()
    # assert res == {"days": ["days", "31-4"]}
    print(res)


def test_time():
    expr1 = "at: 9:30"
    lex = DictParser(expr1)
    res = lex.parse()
    # assert res == {'times': [Token(token_type=Number, lexeme='9:30', column=0, line='at: 9:30')]}
    print(res)


def test_symbol_filter():
    expr1 = """
        Volume > 2M and
        IV > 50 and
        mean(positioning(days(0 to 4))) < -0.0025 and
        symbol_price > 2 and
        order status rejected"""
    lex = DictParser(expr1)
    res = lex.parse()
    # assert res == {'times': [Token(token_type=Number, lexeme='9:30', column=0, line='at: 9:30')]}
    print(res)


def test_description_parser():
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
                strike: round(SPY - SPY * 0.6% * (days_until_opex - 3))
                expiration: opex
                contract_type: put"""
    lex = DictParser(text)
    res = lex.parse()
    # assert res == {'times': [Token(token_type=Number, lexeme='9:30', column=0, line='at: 9:30')]}
    print(res)


def test_columns():
    text = """
    symbol_filter:
        max(Volume,'average volume') > 2M"""
    lex = DictParser(text)
    res = lex.parse()
    result = to_readable(res["symbol_filter"])
    assert result == [
        [
            "max",
            "(",
            "volume",
            "average volume",
            ")",
            ">",
            "2m",
        ]
    ]


def test_columns_aggs():
    text = """
    symbol_filter:
        max(abs(volume,'average volume')) > 2M"""
    lex = DictParser(text)
    res = lex.parse()
    result = to_readable(res["symbol_filter"])
    assert result == [
        [
            "max",
            "(",
            "abs",
            "(",
            "volume",
            "average volume",
            ")",
            ")",
            ">",
            "2m",
        ]
    ]


def test_when():
    text = """
    when:
        spy < 1.03 * spy_20_day_mean and
        spy > spy_20_day_mean"""
    lex = DictParser(text)
    res = lex.parse()
    result = to_readable(res["when"])
    assert result == [
        ["spy", "<", "1.03", "*", "spy_20_day_mean"],
        ["spy", ">", "spy_20_day_mean"],
    ]


def test_times():
    expr1 = "at: 9:30 10:30"
    lex = DictParser(expr1)
    res = lex.parse()
    print("res", res)
    result = to_readable(res["times"])
    assert result == ["9:30", "10:30"]


# def test_lexer():
#     lex = Lexer(expr)
#     res = lex.parse()
#     assert res == {
#         "strategy": "spy",
#         "symbol_pool": "spy",
#         "position_description": {
#             "tradeType": "sell_to_open",
#             "assetType": "option",
#             "positionType": "spread",
#             "betsize": {
#                 "per_trade": ["1%", "*", "bankroll"],
#                 "max_bet": ["1%", "*", "bankroll"],
#             },
#             "entry_point": "2/3rds",
#             "scheduled_close": "4",
#             "spread": {
#                 "sell": {
#                     "strike": [
#                         "spy",
#                         "+",
#                         "spy",
#                         "*",
#                         "0.3%",
#                         "*",
#                         "(",
#                         "days_until_opex",
#                         "-",
#                         "3",
#                         ")",
#                     ],
#                     "expiration": "opex",
#                     "contractType": "put",
#                 },
#                 "buy": {
#                     "strike": [
#                         "round",
#                         "(",
#                         "spy",
#                         "-",
#                         "spy",
#                         "*",
#                         "0.6%",
#                         "*",
#                         "(",
#                         "days_until_opex",
#                         "-",
#                         "3",
#                         ")",
#                         ")",
#                     ],
#                     "expiration": "opex",
#                     "contractType": "put",
#                 },
#             },
#         },
#         "open_position": {
#             "days": ["days", "32-4"],
#             "times": "9:30",
#             "when": [
#                 ["spy", "<", "1.03", "*", "spy_20_day_mean"],
#                 ["spy", ">", "spy_20_day_mean"],
#             ],
#             "symbol_filter": [["not", "in", "the", "portfolio"]],
#         },
#         "close_position": {
#             "days": ["days", "31-4"],
#             "times": "9:30",
#             "when": [
#                 ["spy", "<", "spy_20_day_mean"],
#                 ["spy", ">", "spy_20_day_mean", "*", "1.03"],
#             ],
#         },
#     }
