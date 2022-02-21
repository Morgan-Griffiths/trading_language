from typing import Any
from src.interpreter.utils import (
    compute_entry_point,
    return_option_spread_params,
    close_spread,
)
import src.symbol_filters.functions as sf
import src.interpreter.common_funcs as cf
from src.infrastructure.global_interface import Interface
from src.symbol_pool.functions import symbol_pool_funcs
from trade.utils import twilio_send_message, return_exit_tradeType
import math
import os
import logging
from src.tokens import Tokens

logging.basicConfig(level=logging.INFO, filename="logs/interpreter_activity.log")
logger = logging.getLogger("Interpreter")


class Interpreter:
    def __init__(self, context) -> None:
        self.context: Interface = context
        self.variables: dict = {}
        self.operations: dict = cf.binaryOperators | cf.pythonOperators
        self.context_functions = sf.functions | symbol_pool_funcs
        self.data_store_keys = [
            "tradeType",
            "tradeDirection",
            "strategy",
            "positionType",
            "assetType",
        ]
        self.user = "morgan"

    def lazy_s_parser(self, expr):
        if isinstance(expr, list):
            if isinstance(expr[0], list):
                return self.lazy_s_parser(expr[0])
            args = [self.lazy_s_parser(arg) for arg in expr[1:]]
            # check for None
            for arg in args:
                if arg is None:
                    return None
            if expr[0] in self.context_functions:
                op = self.context_functions[expr[0]]
                return op.forward(self.context, self.variables, *args)
            op = self.operations[expr[0]]
            return op.forward(*args)
        elif isinstance(expr, str):
            try:
                if expr[0] == "^":
                    # global context
                    return self.context.get_value(expr[1:])
                elif expr[0] == "@":
                    # local var
                    return self.variables[expr[1:]]
            except:
                return None
        return expr

    def update_csv_values(self, expr, passFail: bool) -> None:
        print("update_csv_values")
        if isinstance(expr, list):
            assert isinstance(expr[1], str)
            if expr[0] in self.operations:
                left_value = self.operations[expr[0]]
                args = map(self.lazy_s_parser, expr[1:])
                print("expr[0]", expr[0])
                print("passFail", passFail)
                left_value.backward(*args, passFail)
            else:
                left_value = self.context_functions[expr[0]]
                args = map(self.lazy_s_parser, expr[1:])
                print("expr[0]", expr[0])
                print("passFail", passFail)
                left_value.backward(self.context, self.variables, *args, passFail)

    def send_message(self, message):
        if self.context.mode == "real":
            twilio_send_message(f"{message}", os.getenv("RYAN_PHONE"))

    def load_portfolio(self):
        self.variables["symbols"] = self.context.fetch.owned_symbols_by_asset_type(
            self.variables["assetType"]
        )

    def load_symbol_pool(self, trade):
        self.variables["symbols"] = self.lazy_s_parser(trade["symbol_pool"])

    def parse_filter(self, symbol_filter):
        for func in symbol_filter:
            self.variables["symbols"] = self.lazy_s_parser(func)

    def parse_condition(self, criterion):
        conditionals = list(criterion.keys())
        result = None
        for condition in conditionals:
            results = [self.lazy_s_parser(cond) for cond in criterion[condition]]
            if condition == "and":
                result = all(results)
            elif condition == "or":
                result = any(results)
            else:
                raise ValueError(f"Condition not recognized {condition}")
            if result == False:
                break
        return result

    def record_local_values(self, description: dict) -> None:
        for key, value in description.items():
            if isinstance(value, dict):
                self.record_local_values(value)
            else:
                self.variables[key] = self.lazy_s_parser(value)

    def record_prices(self):
        """Bulk fetches symbol price data and stores in redis for lookups"""
        price_data = self.context.api.get_symbols_prices(self.variables["symbols"])
        for symbol, prices in price_data.items():
            print(symbol, prices)
            self.context.update.symbol_price_data(symbol, prices, expiration=5)

    def parse_spread_legs(self, spread: dict):
        legs: dict = {}
        for leg in ["buy", "sell"]:
            legs[leg] = {}
            for k, v in spread[leg].items():
                legs[leg][k] = self.lazy_s_parser(v)
        return legs

    def execute_spread(self, position_description):
        for symbol in self.variables["symbols"]:
            try:
                position_id = self.context.db_interface.create_position(
                    self.user, self.variables["strategy"]
                )
                legs = self.parse_spread_legs(position_description["spread"])
                spread_params = return_option_spread_params(
                    symbol, self.context, self.variables, legs
                )
                trade_params = self.context.api.spread_option_order(spread_params)
                orderId = self.context.api.place_order(trade_params)
                print(orderId)
                data = {k: self.variables[k] for k in self.data_store_keys}
                self.context.db_interface.store_spread_order(
                    data | spread_params,
                    orderId,
                    position_id,
                )
                if self.context.mode == "real":
                    twilio_send_message(f"{trade_params}", os.getenv("RYAN_PHONE"))
            except Exception as e:
                print(e)

    def execute_single(self, position_description):
        for symbol in self.variables["symbols"]:
            try:
                per_contract = min(
                    self.variables["max_bet"] / len(self.variables["symbols"]),
                    self.variables["per_trade"],
                )
                self.execute_open(
                    symbol,
                    position_description,
                    per_contract,
                )
            except Exception as e:
                print(e)

    def open_position(self, position_description):
        print("open_position")
        self.variables["tradeDirection"] = Tokens.OPEN
        self.record_prices()
        if self.variables["positionType"] == Tokens.SPREAD:
            # spread logic.
            self.execute_spread(position_description)
        elif self.variables["positionType"] == Tokens.SINGLE:
            self.execute_single(position_description)
        else:
            raise ValueError(
                f"Position Type not understood {self.variables['positionType']}"
            )

    def execute_open(
        self,
        symbol,
        position_description,
        per_contract,
    ):
        print("here")
        exists = self.context.db_interface.find_duplicate_open_position(
            symbol, self.variables["strategy"]
        )
        print("exists", exists)
        if exists is False:
            price_data = self.context.api.get_symbol_price(symbol)
            inPrice = compute_entry_point(
                price_data, self.variables["entry_point"], self.variables["tradeType"]
            )
            self.variables["symbol_price"] = inPrice
            quantity = math.floor(per_contract / inPrice)
            cash_amount = inPrice * quantity
            print("per_contract", per_contract)
            print("quantity", quantity)
            print("cash_amount", cash_amount)
            if cash_amount < self.context.get_value(Tokens.BANKROLL) and quantity > 0:
                position_id = self.context.db_interface.create_position(
                    self.user, self.variables["strategy"]
                )
                if "stop" in position_description:
                    stop_limit = self.lazy_s_parser(position_description["stop"])
                    sellType = return_exit_tradeType(
                        self.variables["tradeType"], self.variables["assetType"]
                    )
                    equity_params = {
                        "inPrice": inPrice,
                        "inQuantity": quantity,
                        "symbol": symbol,
                        "stopLossPrice": stop_limit,
                        "stopLossQuantity": quantity,
                        "assetType": self.variables["assetType"],
                        "buyType": self.variables["tradeType"],
                        "sellType": sellType,
                    }
                    trade_params = self.context.api.conditional_OTA_stop(equity_params)
                else:
                    orderParams: dict[str, Any] = {
                        "symbol": symbol,
                        "quantity": quantity,
                        "tradeType": self.variables["tradeType"],
                    }
                    trade_params = self.context.api.get_market_order(orderParams)
                print("trade params", trade_params)
                # lock collection
                orderId = self.context.api.place_order(trade_params)
                print(orderId)
                data = {k: self.variables[k] for k in self.data_store_keys}
                self.context.db_interface.store_order(
                    data,
                    inPrice,
                    symbol,
                    quantity,
                    orderId,
                    position_id,
                )
                bankroll = self.context.get_value(Tokens.BANKROLL)
                self.context.update_value(Tokens.BANKROLL, bankroll - cash_amount)
                if self.context.mode == "real":
                    twilio_send_message(f"{trade_params}", os.getenv("RYAN_PHONE"))

    def close_position(self, trade):
        self.variables["tradeDirection"] = Tokens.CLOSE
        close_obj = trade["close_position"]
        self.record_local_values(trade["position_description"])
        self.load_portfolio()
        print(self.variables["symbols"])
        self.record_prices()
        # find all positions with that strategy whose open trades are filled and no close trades
        positionIds = self.context.db_interface.return_open_positions(
            self.variables["strategy"]
        )
        print("portfolio", self.variables["symbols"])
        print("positionIds", positionIds)
        all_orders = self.context.db_interface.return_position_orders(positionIds)
        orders_in_portfolio = [
            order
            for order in all_orders
            if order["symbol"] in self.variables["symbols"]
        ]
        self.variables["symbols"] = [order["symbol"] for order in orders_in_portfolio]
        if "symbol_filter" in close_obj:
            # update symbols
            self.parse_filter(close_obj["symbol_filter"])
            orders_in_portfolio = [
                order
                for order in all_orders
                if order["symbol"] in self.variables["symbols"]
            ]
        print("all_orders", all_orders)
        print("orders_in_portfolio", orders_in_portfolio)
        for order in orders_in_portfolio:
            try:
                self.execute_close(order, trade["position_description"])
            except Exception as e:
                print(e)

    def execute_close(self, order, position_description):
        self.variables["tradeType"] = return_exit_tradeType(
            order["tradeType"], self.variables["assetType"]
        )
        data = {k: self.variables[k] for k in self.data_store_keys}
        print("close_position, original order", order)
        if order["positionType"] == Tokens.SPREAD:
            self.spread_close(position_description, order, data)
        else:
            self.single_close(order, data)

    def spread_close(self, position_description, order, data):
        legs = self.parse_spread_legs(position_description[Tokens.SPREAD])
        spread = close_spread(order, legs)
        quantity = order["buy_quantity"]
        spread_params = return_option_spread_params(
            order["symbol"],
            self.context,
            self.variables,
            spread,
            quantity,
        )
        trade_params = self.context.api.spread_option_order(spread_params)
        print("trade_params", trade_params)
        orderId = self.context.api.place_order(trade_params)
        print(orderId)

        self.context.db_interface.store_spread_order(
            spread_params | data,
            orderId,
            order["positionId"],
        )
        self.send_message(trade_params)

    def single_close(self, order, data):
        symbol = order["symbol"]
        quantity = order["quantity"]
        # cancel any pending stops
        self.context.api.cancel_symbol_order(symbol)
        print("post cancel")
        (
            bidPrice,
            askPrice,
            midpoint,
            margin,
            spread,
        ) = self.context.api.get_price_points(symbol)
        inPrice = (
            bidPrice
            if (
                self.variables["tradeType"] == "SELL"
                or self.variables["tradeType"] == "SELL_TO_CLOSE"
            )
            else askPrice
        )
        orderParams: dict[str, Any] = {
            "symbol": symbol,
            "quantity": quantity,
            "tradeType": self.variables["tradeType"],
        }
        trade_params = self.context.api.get_market_order(orderParams)
        print("trade_params", trade_params)
        orderId = self.context.api.place_order(trade_params)
        print(orderId)
        self.context.db_interface.store_order(
            data, inPrice, symbol, quantity, orderId, order["positionId"]
        )
        self.send_message(trade_params)

    def parse(self, trade: dict, door: str) -> None:
        print("Parsing trade...")
        self.record_local_values(trade["position_description"])
        if door == Tokens.OPEN:
            print("here", self.parse_condition(trade["open_position"][Tokens.WHEN]))
            if Tokens.WHEN not in trade["open_position"] or self.parse_condition(
                trade["open_position"][Tokens.WHEN]
            ):
                self.load_symbol_pool(trade)
                if "symbol_filter" in trade["open_position"]:
                    self.parse_filter(trade["open_position"]["symbol_filter"])
                if len(self.variables["symbols"]):
                    self.open_position(trade["position_description"])
        else:
            if Tokens.WHEN not in trade["close_position"] or self.parse_condition(
                trade["close_position"][Tokens.WHEN]
            ):
                self.close_position(trade)
