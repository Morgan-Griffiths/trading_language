import copy
from src.utils import load_trade
from src.interpreter.interpreter import Interpreter
import pytest
from trade.api import API
from tests.trade_utils import update_variables_and_verify_outcome
from trade.utils import return_exit_tradeType
import os
import json


@pytest.fixture
def streaming_update():
    def closure(interpreter):
        orders = interpreter.context.db_interface.find("working_orders", {})
        for order in orders:
            interpreter.context.db_interface.update_order(
                order["symbol"],
                order["tradeDirection"],
                order["tradeType"],
                order["strategy"],
            )
            positionId = order["positionId"]
            interpreter.context.db_interface.update_position_open(positionId)
            interpreter.context.db_interface.add_enter_trade_to_position(
                positionId, order["orderId"]
            )

    return closure


def test_spy(
    interpreter: Interpreter, spy_description, update_context_time_invariant, teardown
):
    # trade = load_trade("spy")
    update_variables_and_verify_outcome(
        interpreter, spy_description, "open_position", outcome=True, passFilter=True
    )
    interpreter = update_context_time_invariant(interpreter)
    interpreter.parse(spy_description, "open")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    assert res != []


def test_spy_close(
    interpreter: Interpreter, spy_description, update_context_time_invariant, teardown
):
    trade = copy.deepcopy(spy_description)
    update_variables_and_verify_outcome(
        interpreter, spy_description, "open_position", outcome=True, passFilter=True
    )
    interpreter = update_context_time_invariant(interpreter)
    interpreter.parse(spy_description, "open")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    assert res != []

    update_variables_and_verify_outcome(
        interpreter, spy_description, "close_position", outcome=True, passFilter=True
    )
    interpreter.parse(spy_description, "close")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    print(res)
    assert res[-1]["tradeType"] == "SELL_TO_OPEN"


def test_opex(
    interpreter: Interpreter, opex_description, update_context_time_invariant, teardown
):
    # trade = load_trade("spy")
    update_variables_and_verify_outcome(
        interpreter, opex_description, "open_position", outcome=True, passFilter=True
    )
    interpreter = update_context_time_invariant(interpreter)
    interpreter.parse(opex_description, "open")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    assert res != []


def test_opex_close(
    interpreter: Interpreter,
    opex_description,
    update_context_time_invariant,
    streaming_update,
    teardown,
):
    update_variables_and_verify_outcome(
        interpreter, opex_description, "open_position", outcome=True, passFilter=True
    )
    interpreter = update_context_time_invariant(interpreter)
    interpreter.parse(opex_description, "open")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    assert res != []
    streaming_update(interpreter)
    positionsIds = interpreter.context.db_interface.return_open_positions(
        opex_description["strategy"]
    )
    interpreter.context.db_interface.update_position_open(positionsIds[0])
    update_variables_and_verify_outcome(
        interpreter, opex_description, "close_position", outcome=True, passFilter=True
    )
    interpreter.parse(opex_description, "close")
    res = list(interpreter.context.db_interface.find("working_orders", {}))
    print(res)
    exit_type = return_exit_tradeType(res[0]["tradeType"], res[0]["assetType"])
    print(exit_type)
    assert res[-1]["tradeType"] == exit_type


# @pytest.fixture
# def test_trade_open():
#     def open(interpreter, trade, update_context_time_invariant):
#         update_variables_and_verify_outcome(
#             interpreter, trade, "open_position", outcome=True, passFilter=True
#         )
#         interpreter = update_context_time_invariant(interpreter)
#         interpreter.parse(trade, "open")
#         res = list(interpreter.context.db_interface.find("working_orders", {}))
#         assert res != []

#     return open


# @pytest.fixture
# def test_trade_open_close():
#     def open_close(interpreter, trade, update_context_time_invariant):
#         update_variables_and_verify_outcome(
#             interpreter, trade, "open_position", outcome=True, passFilter=True
#         )
#         interpreter = update_context_time_invariant(interpreter)
#         interpreter.parse(trade, "open")
#         res = list(interpreter.context.db_interface.find("working_orders", {}))
#         assert res != []
#         update_variables_and_verify_outcome(
#             interpreter,
#             trade,
#             "close_position",
#             outcome=True,
#             passFilter=True,
#         )
#         interpreter.parse(trade, "close")
#         res = list(interpreter.context.db_interface.find("working_orders", {}))

#     return open_close


# def test_folder(
#     interpreter, update_context_time_invariant, test_trade_open_close, test_trade_open
# ):
#     for file_path in os.listdir("output_descriptions"):
#         if file_path != ".DS_Store":
#             with open(os.path.join("output_descriptions", file_path), "rb") as f:
#                 trade = json.load(f)
#                 test_trade_open_close(interpreter, trade, update_context_time_invariant)
