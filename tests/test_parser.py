from src.compiler.dict_parser import DictParser
from src.compiler.parser import Parser
from more_itertools import peekable


def test_s_parser(parser: Parser):
    text = "when: spy * (spy - 5)"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade["when"])
    res = parser.parse_s_expr(parsed_trade["when"])
    assert res == ["*", "^SPY", ["-", "^SPY", 5]]


def test_s_parser_unary(parser: Parser):
    text = "when: round(spy - spy * 0.6% * (days_until_opex - 3))"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade["when"])
    res = parser.parse_s_expr(parsed_trade["when"])
    assert res == [
        "round",
        ["-", "^SPY", ["*", ["*", "^SPY", 0.006], ["-", "^DAYS_UNTIL_OPEX", 3]]],
    ]


def test_if_parser(parser: Parser):
    text = "trade_type: if net_position < 0 then buy else sell_short"
    lexer = DictParser(text)
    parsed_trade: dict = lexer.parse()
    print("parsed_trade", parsed_trade)
    res = parser.parse_if_expr(peekable(parsed_trade["tradeType"]))
    assert res == {"if": [[["<", "^NET_POSITION", 0], "buy"]]}
