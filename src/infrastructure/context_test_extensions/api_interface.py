import copy
import numpy as np
import json

from numpy.lib.arraysetops import isin
from src.mocks.globals import (
    SYMBOL_DATA,
    DEFAULT_HEADERS,
    POSITIONS,
    QUOTE,
    WORKING_ORDER,
)
from src.utils import load_pickle
import logging

logging.basicConfig(level=logging.INFO, filename="logs/fake_api_activity.log")
logger = logging.getLogger("FakeAPI")


def return_symbol_price(symbol, price=440):
    equity = copy.deepcopy(SYMBOL_DATA)
    equity["symbol"] = symbol
    descrip = equity["description"].split(" ")
    descrip[0] = symbol
    logger.info("descrip", descrip)
    equity["description"] = " ".join(descrip)
    equity["bidPrice"] = price
    equity["askPrice"] = price
    equity["lastPrice"] = price
    return equity


def return_working_order_from_symbol(db_orders: list):
    res = {}
    if db_orders:
        for order in db_orders:
            if order["filled"] == True:
                res = copy.deepcopy(WORKING_ORDER)
                res["orderLegCollection"][0]["instrument"]["symbol"] = order["symbol"]
                res["orderId"] = order["orderId"]
                break
    return [res]


class FakeResponse(object):
    def __init__(self, content, headers):
        self.c = content
        self.h = headers

    @property
    def content(self):
        return self.c

    @property
    def headers(self):
        return self.h


class FakeAPI(object):
    def __init__(self, context):
        self.TOKEN_NAME = "test"
        self.spy_options = load_pickle("files/spy_options")
        self.context = context

    def get(self, url: str, params: dict):
        global DEFAULT_HEADERS
        logger.info("fake get", url, params)
        components = url.split("/")
        query = components[-1].split("?")
        if "symbol" in params:
            symbols = params["symbol"]
            logger.info(symbols)
            assert isinstance(symbols, list) and isinstance(symbols[0], str)
            prices = {sym: return_symbol_price(sym) for sym in symbols}
            return FakeResponse(json.dumps(prices), DEFAULT_HEADERS)
        elif "positions" in params.values():
            return FakeResponse(
                json.dumps(self.context.get_value("portfolio")), DEFAULT_HEADERS
            )
        elif query[0] == "quotes":
            symbol = components[-2]
            symbol_quote = QUOTE["SPY"]
            return FakeResponse(json.dumps({symbol: symbol_quote}), DEFAULT_HEADERS)
        elif query[0] == "chains":
            return FakeResponse(json.dumps(self.spy_options), DEFAULT_HEADERS)
        elif query[0] == "pricehistory":
            symbol = components[-2]
            return FakeResponse(
                json.dumps(return_symbol_price(symbol)), DEFAULT_HEADERS
            )
        elif query[0] == "orders":
            db_orders = list(self.context.db_interface.find("working_orders", {}))
            logger.info("db_orders", db_orders)
            res = return_working_order_from_symbol(db_orders)
            logger.info("res", res)
            return FakeResponse(json.dumps(res), DEFAULT_HEADERS)
        else:
            raise ValueError(f"Unsupported query {query}")

    def delete(self, url, params):
        logger.info("fake delete", url, params)
        return FakeResponse(json.dumps({}), DEFAULT_HEADERS)

    def post(self, url, data, headers):
        logger.info("POST")
        global DEFAULT_HEADERS
        resp_headers = copy.deepcopy(DEFAULT_HEADERS)
        resp_headers["location"] = f"blah/{np.random.randint(0,1e6)}"
        if url.split("/")[-1] == "orders":
            self.context.test_portfolio.insertOrder(json.loads(data))
        return FakeResponse(json.dumps(self.spy_options), resp_headers)
