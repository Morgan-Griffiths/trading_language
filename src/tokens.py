from typing import ClassVar


from src.common_types import Column
from typing import Type
from dataclasses import dataclass


@dataclass
class Token:
    token_type: str
    lexeme: str
    literal: str
    line: int

    def __str__(self):
        return self.token_type + " " + self.lexeme + " " + self.literal


class Tokens:
    # Single-character tokens.
    LEFT_PAREN = "("
    RIGHT_PAREN = ")"
    LEFT_BRACE = "{"
    RIGHT_BRACE = "}"
    COMMA = ","
    DOT = "."
    MINUS = "-"
    PLUS = "+"
    SEMICOLON = ";"
    SLASH = "/"
    STAR = "*"

    # One or two character tokens.
    BANG = "!"
    BANG_EQUAL = "!="
    EQUAL = "="
    EQUAL_EQUAL = "=="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="

    # Literals.
    # IDENTIFIER
    # STRING
    # NUMBER

    AND = "and"
    NOT = "not"
    ELSE = "else"
    ELIF = "elif"
    FALSE = "false"
    IF = "if"
    OR = "or"
    TRUE = "true"

    # Keywords.
    SYMBOL_POOL = "symbol_pool"
    STRATEGY = "strategy"
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    WHEN = "when"
    AT = "at"
    ON = "on"
    SYMBOL_FILTER = "symbol_filter"
    POSITION_DESCRIPTION = "position_description"
    TRADE_TYPE = "trade_type"
    POSITION_TYPE = "position_type"
    ASSET_TYPE = "asset_type"
    BETSIZE = "betsize"
    PER_TRADE = "per_trade"
    MAX = "max"
    STOP = "stop"
    ENTRY_POINT = "entry_point"
    SCHEDULED_CLOSE = "scheduled_close"
    SPREAD = "spread"
    BUY = "buy"
    SELL = "sell"
    EXPIRATION = "expiration"
    STRIKE = "strike"
    CONTRACT_TYPE = "contract_type"

    GIVEN = "given"
    IN = "in"

    # context
    BANKROLL = "BANKROLL"
    NET_POSITION = "NET_POSITION"
    SPY_SIGMA = "SPY_SIGMA"
    SPY_20_DAY_MEAN = "SPY_20_DAY_MEAN"
    OPEX = "OPEX"
    TODAY = "TODAY"
    TODAY_DATE = "TODAY_DATE"
    DAYS_UNTIL_OPEX = "DAYS_UNTIL_OPEX"
    DISTANCE_UNTIL_OPEX = "DISTANCE_UNTIL_OPEX"
    POSITION = "POSITION"
    ATM_OPTION = "atm_option"
    PREVIOUS_OPEX = "PREVIOUS_OPEX"

    # variables
    SYMBOL_PRICE = "SYMBOL_PRICE"

    OPEN = "open"
    CLOSE = "close"
    SINGLE = "single"

    EOF = "eof"
