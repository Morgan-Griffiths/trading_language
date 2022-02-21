import datetime
from src.infrastructure.lazy_evaluator import resolve_dependencies
from src.interpreter.interpreter import Interpreter, compute_entry_point
import pytest


@pytest.fixture
def opex_description():
    description = {
        "position_description": {
            "strategy": "test",
            "tradeType": "SELL_SHORT",
            "positionType": "single",
            "assetType": "EQUITY",
            "scheduled_close": 4,
            "betsize": {
                "per_trade": ["*", "^BANKROLL", 0.1],
                "max_bet": ["*", "^BANKROLL", 0.12],
            },
            "stop": ["+", "^SYMBOL_PRICE", ["*", "^SYMBOL_PRICE", 0.1]],
            "entry_point": "MARKET",
        },
        "close_position": {"days": ["10-4"], "times": ["15:59"]},
    }
    return description


@pytest.fixture
def spy_description():
    description = {
        "position_description": {
            "strategy": "test",
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
                    "contractType": "put",
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
                    "contractType": "put",
                },
            },
        }
    }
    return description


def test_compute_entry_point(interpreter: Interpreter, teardown):
    price_data = interpreter.context.api.get_symbol_price("TSLA")
    res = compute_entry_point(price_data, "MARKET", "BUY")
    assert res == price_data["askPrice"]


def test_lazy_func(interpreter: Interpreter, teardown):
    res = resolve_dependencies(interpreter.context, "BANKROLL")
    assert res == 38000


def test_parse_context(interpreter: Interpreter, teardown):
    expr = ["*", "^BANKROLL", 0.01]
    res = interpreter.lazy_s_parser(expr)
    assert res == 380.0


def test_s_parser(interpreter: Interpreter, teardown):
    expr = ["*", 5, 2]
    res = interpreter.lazy_s_parser(expr)
    assert res == 10


def test_s_parser_none(interpreter: Interpreter, teardown):
    expr = ["*", 5, "^a"]
    res = interpreter.lazy_s_parser(expr)
    assert res == None


def test_record_locals(interpreter: Interpreter, teardown):
    d = {
        "position_description": {
            "tradeType": "SELL_TO_OPEN",
            "assetType": "OPTION",
            "positionType": "spread",
        }
    }
    interpreter.record_local_values(d["position_description"])
    assert interpreter.variables["assetType"] == "OPTION"
    assert interpreter.variables["tradeType"] == "SELL_TO_OPEN"
    assert interpreter.variables["positionType"] == "spread"


def test_record_locals_complex(interpreter: Interpreter, teardown):
    d = {
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
                "contractType": "put",
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
                "contractType": "put",
            },
        },
    }
    interpreter.record_local_values(d)
    assert interpreter.variables["assetType"] == "OPTION"
    assert interpreter.variables["tradeType"] == "SELL_TO_OPEN"
    assert interpreter.variables["positionType"] == "spread"
    assert interpreter.variables["entry_point"] == "2/3rds"
    assert interpreter.variables["scheduled_close"] == 4


def test_record_prices(interpreter: Interpreter, teardown):
    interpreter.variables["symbols"] = ["TSLA"]
    interpreter.record_prices()
    new_value = interpreter.context.get_value("TSLA")
    print(new_value)
    assert isinstance(new_value, float) or isinstance(new_value, int)


def test_load_symbol_pool(interpreter: Interpreter, teardown):
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "TSLA", "AAPL"]})
    assert interpreter.variables["symbols"] == ["TSLA", "AAPL"]


def test_execute_open(interpreter: Interpreter, opex_description, teardown):
    interpreter.record_local_values(opex_description["position_description"])
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "TSLA", "AAPL"]})
    interpreter.variables["tradeDirection"] = "open"
    interpreter.execute_open("TSLA", {"stop": 4}, 500)
    print(interpreter.context.get_value("BANKROLL"))
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    assert orders != []


def test_execute_single(interpreter: Interpreter, opex_description, teardown):
    interpreter.record_local_values(opex_description["position_description"])
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "TSLA", "AAPL"]})
    interpreter.execute_single(opex_description["position_description"])


def test_open_position(interpreter: Interpreter, opex_description, teardown):
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "TSLA", "AAPL"]})
    interpreter.record_local_values(opex_description["position_description"])
    interpreter.open_position(opex_description["position_description"])


def test_execute_spread(
    interpreter: Interpreter, spy_description, update_context_time_invariant, teardown
):
    interpreter.record_local_values(spy_description["position_description"])
    interpreter.variables["tradeDirection"] = "open"
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "SPY"]})
    interpreter = update_context_time_invariant(interpreter)
    interpreter.execute_spread(spy_description["position_description"])
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    assert orders != []
    assert orders[0]["buy_instruction"] == "BUY_TO_OPEN"
    assert orders[0]["sell_instruction"] == "SELL_TO_OPEN"


def test_execute_close(
    interpreter: Interpreter, spy_description, update_context_time_invariant, teardown
):
    interpreter.record_local_values(spy_description["position_description"])
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "SPY"]})
    interpreter = update_context_time_invariant(interpreter)
    interpreter.variables["tradeDirection"] = "open"
    interpreter.execute_spread(spy_description["position_description"])
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    assert orders != []
    assert orders[0]["buy_instruction"] == "BUY_TO_OPEN"
    assert orders[0]["sell_instruction"] == "SELL_TO_OPEN"
    interpreter.variables["tradeDirection"] = "close"
    interpreter.execute_close(orders[0], spy_description["position_description"])
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    print("orders", orders)
    assert orders != []
    assert orders[-1]["buy_instruction"] == "BUY_TO_CLOSE"
    assert orders[-1]["sell_instruction"] == "SELL_TO_CLOSE"


def test_close_position(
    interpreter: Interpreter, opex_description, update_context_time_invariant, teardown
):
    interpreter.record_local_values(opex_description["position_description"])
    interpreter.load_symbol_pool({"symbol_pool": ["load_symbols", "TSLA"]})
    interpreter = update_context_time_invariant(interpreter)
    interpreter.open_position(opex_description["position_description"])
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    assert orders != []
    assert orders[0]["tradeType"] == "SELL_SHORT"
    print(orders)
    order = orders[0]
    interpreter.context.db_interface.update_order(
        order["symbol"], order["tradeDirection"], order["tradeType"], order["strategy"]
    )
    interpreter.context.db_interface.update_position_open(orders[0]["positionId"])
    interpreter.context.db_interface.add_enter_trade_to_position(
        orders[0]["positionId"], orders[0]["orderId"]
    )
    interpreter.variables["tradeDirection"] = "close"
    interpreter.close_position(opex_description)
    orders = list(interpreter.context.db_interface.find("working_orders", {}))
    print("orders", orders)
    assert len(orders) > 1
    assert orders[-1]["tradeType"] == "BUY_TO_COVER"
