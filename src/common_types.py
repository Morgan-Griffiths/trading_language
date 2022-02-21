import pandas as pd
import os
from dataclasses import dataclass
from typing import Any
import json

with open("columns.json", "rb") as f:
    csv_mapping: dict = json.load(f)

CRYPTO_LIST: list = [
    "RIOT",
    "MARA",
    "MSTR",
    "SI",
    "BTBT",
    "FTFT",
    "SOS",
    "GRNQ",
    "XNET",
    "SRAX",
    "OLB",
    "EBON",
    "GBOX",
    "PBTS",
    "NXTD",
    "MOGO",
    "CLSK",
    "CAN",
    "EQOS",
    "BITO",
]

SPAC_LIST: list = list(
    pd.read_csv(f"{os.getcwd()}/csv_files/SPACs - Sheet1.csv")["Ticker"].unique()
)


earnings_df = pd.read_csv(f"{os.getcwd()}/csv_files/finviz_earnings.csv")
BIOTECH_LIST: list = list(
    earnings_df[earnings_df["Industry"] == "Biotechnology"]["symbol"].values
)

MATERIAL_LIST: list = list(
    earnings_df[earnings_df["Sector"] == "Basic Materials"]["symbol"].values
)
ENERGY_LIST: list = list(
    earnings_df[earnings_df["Sector"] == "Energy"]["symbol"].values
)
EXCLUDE_LIST: list = ["SOGO", "VIH"]
BLACKLIST: list = []
BLACKLIST.extend(EXCLUDE_LIST)
BLACKLIST.extend(SPAC_LIST)
BLACKLIST.extend(CRYPTO_LIST)
BLACKLIST.extend(BIOTECH_LIST)

SYMBOLS: list = list(
    pd.read_csv(f"{os.getcwd()}/csv_files/stock_fundamentals.csv")["symbol"].values
)
SYMBOLS.extend(["SPY", "$VIX.X"])


class Binary:
    ...


class Aggregator:
    ...


class Column:
    ...


class Variable:
    ...


class Context:
    ...


class CSV:
    ...


class English:
    ...


class Key:
    ...


class Unary:
    ...


class Range:
    ...


class Time:
    ...


class Datetime:
    ...


class Separator:
    ...


class Group:
    ...


class Logic:
    ...


class Conditional:
    ...


class Query:
    ...


class Number:
    ...


class Value:
    ...


class Symbol:
    ...


class Name:
    ...


class Restriction:
    ...


class Database:
    ...


class Field:
    ...


database_names = ["order"]
database_types = {e: Database() for e in database_names}

field_names = ["status", "filled"]
field_types = {e: Field() for e in field_names}

symbol_types = {s.lower(): Symbol() for s in SYMBOLS}

conditional_names = ["if", "elif", "else", "then"]
conditional_types = {e: Conditional() for e in conditional_names}

query_names = ["given", "where", "select"]
query_types = {e: Query() for e in query_names}

logic_names = ["and", "or", "not"]
logic_types = {e: Logic() for e in logic_names}

group_names = ["(", ")"]
group_types = {e: Group() for e in group_names}

separator_names = ["to"]
separator_types = {s: Separator() for s in separator_names}

range_names = ["day", "days", "range"]
range_types = {r: Range() for r in range_names}

time_names = ["yesterday", "yesterday's"]
time_types = {y: Datetime() for y in time_names}

key_names = [
    "strategy",
    "symbol_pool",
    "position_description",
    "open_position",
    "close_position",
    "on",
    "at",
    "when",
    "symbol_filter",
]
key_types = {k: Key() for k in key_names}


value_names = [
    "market",
    "option",
    "equity",
    "buy",
    "buy_to_open",
    "buy_to_close",
    "buy_to_cover",
    "sell",
    "sell_to_open",
    "sell_to_close",
    "sell_short",
    "limit",
    "spread",
    "single",
    "call",
    "put",
    "2/3rds",
    "midpoint",
    "rejected",
    "success",
]
value_types = {k: Value() for k in value_names}

aggregator_names = ["mean", "max", "min", "abs"]
aggregator_types = {l: Aggregator() for l in aggregator_names}

unary_names = ["round"]
unary_types = {l: Unary() for l in unary_names}

binary_names = ["*", "/", "-", "+", ">", "<", ">=", "<=", "==", "!="]
binary_types = {l: Binary() for l in binary_names}

greek_names = [
    "charm",
    "vanna",
    "gamma",
    "volga",
    "vomma",
    "vega",
    "rho",
    "delta",
    "theta",
]

column_names = ["volume", "average volume", "marketcap", "iv", "percent_away", "price"]
column_types = {col: Column() for col in column_names + greek_names}

csv_names = ["greeks", "positioning", "stock_fundamentals"]
csv_types = {csv: CSV() for csv in csv_names}

context_names = [
    "charm_0",
    "net_position",
    "bankroll",
    "spy_20_day_mean",
    "spy_sigma",
    "portfolio",
    "positions",
    "days_until_opex",
    "opex",
]
context_types = {v: Context() for v in context_names}
context_at_types = {"^" + v: Context() for v in context_names}

variable_names = [
    "symbol_price",
]
variable_types = {v: Variable() for v in variable_names}
variable_at_types = {"@" + v: Variable() for v in variable_names}


english_names = ["from", "of", "the", "in"]
english_types = {e: English() for e in english_names}

restriction_names = ["!earnings", "!biotech", "!crypto", "!spac", "!materials"]
restriction_types = {e: Restriction() for e in restriction_names}


operator_swaps = {">": "<", ">=": "<=", "<": ">", "<=": ">="}
operators = {
    ">": lambda x, y: x > y,
    "<": lambda x, y: x < y,
    ">=": lambda x, y: x >= y,
    "<=": lambda x, y: x <= y,
}


type_mapping = (
    english_types
    | field_types
    | database_types
    | value_types
    | restriction_types
    | context_types
    | variable_types
    | csv_types
    | column_types
    | binary_types
    | unary_types
    | aggregator_types
    | time_types
    | group_types
    | conditional_types
    | range_types
    | separator_types
    | logic_types
    | query_types
)

column_mapping = {
    "shares outstanding": "Shares Outstanding",
    "shares float": "Shares Float",
    "marketcapfloat": "marketCapFloat",
    "insider ownership": "Insider Ownership",
    "insider transactions": "Insider Transactions",
    "institutional ownership": "Institutional Ownership",
    "institutional transactions": "Institutional Transactions",
    "float short": "Float Short",
    "short ratio": "Short Ratio",
    "price": "price",
    "strike": "strike",
    "charm": "charm",
    "gamma": "gamma",
    "vanna": "vanna",
    "volga": "volga",
    "last": "Last",
    "iv": "Imp Vol",
    "options vol": "Options Vol",
    "call open int": "Call Open Int",
    "put open int": "Put Open Int",
    "put/call oi": "Put/Call OI",
    "put/call vol": "Put/Call Vol",
    "percent_away": "percent_away",
    "volume": "Volume",
    "average volume": "Average Volume",
    "marketcap": "Market Cap",
}

value_mapping = {
    "market": "MARKET",
    "option": "OPTION",
    "equity": "EQUITY",
    "spread": "spread",
    "single": "single",
    "buy_to_close": "BUY_TO_CLOSE",
    "buy": "BUY",
    "sell_short": "SELL_SHORT",
    "sell_to_close": "SELL_TO_CLOSE",
    "buy_to_cover": "BUY_TO_COVER",
    "sell_to_open": "SELL_TO_OPEN",
    "call": "CALL",
    "put": "PUT",
    "2/3rds": "2/3rds",
    "midpoint": "midpoint",
}

keyword_mapping: dict = {
    "strategy": "strategy",
    "symbol_pool": "symbol_pool",
    "position_description": "position_description",
    "when": "when",
    "on": "days",
    "at": "times",
    "symbol_filter": "symbol_filter",
    "open_position": "open_position",
    "close_position": "close_position",
    "trade_type": "tradeType",
    "position_type": "positionType",
    "asset_type": "assetType",
    "entry_point": "entry_point",
    "scheduled_close": "scheduled_close",
    "stop": "stop",
    "spread": "spread",
    "per_trade": "per_trade",
    "max_bet": "max_bet",
    "betsize": "betsize",
    "put_call": "putCall",
    "strike": "strike",
    "expiration": "expiration",
    "contract_type": "contractType",
    "sell": "sell",
    "buy": "buy",
}

# keyword_grammar = {
#     "strategy": set(str),
#     "symbol_pool": set('positioning','!earnings',"!biotech","!crypto","!spac","!materials",*SYMBOLS),
#     "when": set(),
#     "on": "days",
#     "at": "times",
#     "symbol_filter": "symbol_filter",
#     "open_position": "open_position",
#     "close_position": "close_position",
#     "trade_type": "tradeType",
#     "position_type": "positionType",
#     "asset_type": "assetType",
#     "entry_point": "entry_point",
#     "scheduled_close": "scheduled_close",
#     "stop": "stop",
#     "spread": "spread",
#     "per_trade": "per_trade",
#     "max": "max",
#     "betsize": "betsize",
#     "put_call": "putCall",
#     "strike": "strike",
#     "expiration": "expiration",
#     "contract_type": "contractType",
#     "sell": "sell",
#     "buy": "buy",
# }
