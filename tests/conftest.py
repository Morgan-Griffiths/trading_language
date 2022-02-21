import pytest
from src.interpreter.interpreter import Interpreter
from src.infrastructure.global_interface import return_context
from trade.api import API
from trade.config import Config
from src.compiler.compiler import Compiler
from src.symbol_filters.compile_functions import SymbolFilterCompiler
from src.compiler.parser import Parser
from src.infrastructure.database_layer import DataBase
from src.infrastructure.redis_layer import RedisInterface
from src.utils import parse_date, parse_datetime
import datetime
import os
import sys


@pytest.fixture(autouse=True)
def backend():
    chrdir = os.getcwd()
    path = os.path.join(chrdir,'backend_startup.sh')
    os.system(f"bash {path}")


@pytest.fixture
def update_context_time_invariant():
    def closure(interpreter):
        interpreter.context.update_value(
            "OPEX", datetime.date(year=2021, month=11, day=19)
        )
        interpreter.context.update_value(
            "TODAY", datetime.datetime(year=2021, month=10, day=25)
        )
        interpreter.context.update_value(
            "TODAY_DATE", datetime.datetime(year=2021, month=10, day=25).date()
        )
        interpreter.context.update_value(
            "DISTANCE_TO_OPEX",
            parse_date(interpreter.context.get_value("OPEX"))
            - datetime.date(year=2021, month=10, day=15),
        )
        interpreter.context.update_value(
            "DAYS_UNTIL_OPEX",
            (
                parse_date(interpreter.context.get_value("OPEX"))
                - datetime.date(year=2021, month=10, day=15)
            ).days,
        )
        interpreter.context.update_value(
            "PREVIOUS_OPEX", datetime.datetime(year=2021, month=10, day=15)
        )
        return interpreter

    return closure


@pytest.fixture
def db():
    return DataBase("test")


@pytest.fixture
def teardown(db):
    yield
    print("Tearing down")
    db.drop_collection("working_orders")
    db.drop_collection("positions")


@pytest.fixture
def redis():
    return RedisInterface()


@pytest.fixture
def parser():
    return Parser()


@pytest.fixture
def symbol_filter_compiler():
    return SymbolFilterCompiler()


@pytest.fixture
def compiler():
    return Compiler()


@pytest.fixture
def context():
    return return_context("test")


@pytest.fixture
def interpreter(context):
    return Interpreter(context)


@pytest.fixture
def config(context):
    config = Config()
    config.test(context)
    return config


@pytest.fixture
def api(config):
    return API(config.params)


@pytest.fixture
def opex_description():
    description = {
        "strategy": "opex",
        "symbol_pool": ["positioning", "!biotech", "!earnings"],
        "position_description": {
            "tradeType": "SELL_SHORT",
            "positionType": "single",
            "assetType": "EQUITY",
            "scheduled_close": 4,
            "betsize": {
                "per_trade": ["*", "^BANKROLL", 0.1],
                "max_bet": ["*", "^BANKROLL", 0.12],
            },
            "stop": ["+", "@SYMBOL_PRICE", ["*", "@SYMBOL_PRICE", 0.1]],
            "entry_point": "MARKET",
        },
        "open_position": {
            "days": ["10-4"],
            "times": ["9:30"],
            "when": {"and": [[">", "^SPY", ["-", "^SPY_20_DAY_MEAN", "^SPY_SIGMA"]]]},
            "symbol_filter": [
                [
                    "filter_csv",
                    "stock_fundamentals",
                    ["list", "None"],
                    ["list", "Volume"],
                    "@symbols",
                    ">",
                    2000000.0,
                ],
                [
                    "filter_csv",
                    "IV",
                    ["list", "None"],
                    ["list", "Imp Vol"],
                    "@symbols",
                    ">",
                    50,
                ],
                [
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
                ],
            ],
        },
        "close_position": {"days": ["10-4"], "times": ["15:59"]},
    }

    return description


@pytest.fixture
def spy_description():
    trade = {
        "strategy": "spy",
        "symbol_pool": ["load_symbols", "SPY"],
        "position_description": {
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
        },
        "open_position": {
            "days": ["32-4"],
            "times": ["9:30"],
            "when": {
                "and": [
                    ["<", "^SPY", ["*", "^SPY_20_DAY_MEAN", 1.03]],
                    [">", "^SPY", "^SPY_20_DAY_MEAN"],
                ]
            },
            "symbol_filter": [["in_portfolio", "@symbols", False]],
        },
        "close_position": {
            "days": ["31-4"],
            "times": ["9:30"],
            "when": {
                "or": [
                    ["<", "^SPY", "^SPY_20_DAY_MEAN"],
                    [">", "^SPY", ["*", "^SPY_20_DAY_MEAN", 1.03]],
                ]
            },
        },
    }

    return trade
