from dataclasses import dataclass
from src.mocks.globals import POSITIONS, OPTION_POSITION, EQUITY_POSITION
import src.infrastructure.global_interface as int
import copy
import logging

logging.basicConfig(level=logging.INFO, filename="logs/test_portfolio_activity.log")
logger = logging.getLogger("Portfolio")


class FakePortfolio:
    def __init__(self, context) -> None:
        self.context: "int.Interface" = context
        self.clearPositions()

    def clearPositions(self):
        portfolio = copy.deepcopy(POSITIONS)
        portfolio["securitiesAccount"]["positions"] = []
        self.context.update_value("portfolio", portfolio)
        self.context.update_value("positions", [])

    def removeSymbols(self, symbols):
        positions = self.context.fetch.positions()
        pops = []
        for i, position in enumerate(positions):
            if position["instrument"]["symbol"] in symbols:
                pops.append(i)
        for index in sorted(pops, reverse=True):
            del positions[index]
        self.context.update_value("positions", positions)

    def updateEquities(self, symbols, directions):
        self.clearPositions()
        positions: list = self.context.fetch.positions()
        for symbol, direction in zip(symbols, directions):
            positions.append(return_equity_position(symbol, direction))
            self.context.update_value("positions", positions)

    def updateOptions(self, symbols, option_symbols, putCalls, new_positions):
        self.clearPositions()
        positions = self.context.fetch.positions()
        for symbol, option_symbol, putCall, position in zip(
            symbols, option_symbols, putCalls, new_positions
        ):
            positions.append(
                return_option_position(symbol, option_symbol, putCall, position)
            )
            self.context.update_value("positions", positions)

    def craft_portfolio(self, params):
        symbols = params["symbols"]
        option_symbols = params["option_symbols"]
        putCalls = params["putCalls"]
        directions = params["directions"]
        self.clearPositions()
        positions = self.context.fetch.positions()
        for symbol, option_symbol, putCall, direction in zip(
            symbols, option_symbols, putCalls, directions
        ):
            positions.append(
                return_option_position(symbol, option_symbol, putCall, direction)
            )
            self.context.update_value("positions", positions)

    def updatePositions(self, symbol, option_symbol, putCall, direction):
        params = {
            "symbols": [symbol],
            "option_symbols": [option_symbol],
            "putCalls": [putCall],
            "directions": [direction],
        }
        self.craft_portfolio(params)

    def insertOrder(self, data: dict) -> None:
        positions = self.context.fetch.positions()
        for order in data["orderLegCollection"]:
            if order["instrument"]["assetType"] == "EQUITY":
                equity = copy.deepcopy(EQUITY_POSITION)
                equity["instrument"] = order["instrument"]
                if data["orderType"] == "MARKET":
                    equity["orderType"] = data["orderType"]
                    equity["averagePrice"] = None
                else:
                    equity["orderType"] = data["orderType"]
                    equity["averagePrice"] = data["price"]
                if order["instruction"] == "SELL_SHORT":
                    equity["shortQuantity"] += order["quantity"]
                elif order["instruction"] == "SELL":
                    equity["longQuantity"] -= order["quantity"]
                elif order["instruction"] == "BUY_TO_COVER":
                    equity["shortQuantity"] -= order["quantity"]
                else:
                    equity["longQuantity"] += order["quantity"]
                positions.append(equity)
            else:
                option = copy.deepcopy(OPTION_POSITION)
                option["instrument"] = order["instrument"]
                option["instrument"]["underlyingSymbol"] = order["instrument"][
                    "symbol"
                ].split("_")[0]
                option["averagePrice"] = data["price"]
                if order["instruction"] == "SELL_TO_OPEN":
                    option["shortQuantity"] += order["quantity"]
                elif order["instruction"] == "SELL_TO_CLOSE":
                    option["longQuantity"] -= order["quantity"]
                elif order["instruction"] == "BUY_TO_CLOSE":
                    option["shortQuantity"] -= order["quantity"]
                else:
                    option["longQuantity"] += order["quantity"]
                positions.append(option)
        self.context.update_value("positions", positions)


def return_option_position(symbol, option_symbol, putCall, direction):
    opt = copy.deepcopy(OPTION_POSITION)
    opt["instrument"]["symbol"] = option_symbol
    opt["instrument"]["underlyingSymbol"] = symbol
    opt["instrument"]["putCall"] = putCall
    if direction == "SHORT":
        opt["shortQuantity"] = 11
        opt["longQuantity"] = 0
    else:
        opt["longQuantity"] = 11
        opt["shortQuantity"] = 0

    descrip = opt["instrument"]["description"].split(" ")
    descrip[0] = symbol
    descrip[-1] = option_symbol
    opt["instrument"]["description"] = " ".join(descrip)
    return opt


def return_equity_position(symbol, direction):
    opt = copy.deepcopy(EQUITY_POSITION)
    opt["instrument"]["symbol"] = symbol
    if direction == "SHORT":
        opt["shortQuantity"] = 11
        opt["longQuantity"] = 0
    else:
        opt["longQuantity"] = 11
        opt["shortQuantity"] = 0
    return opt
