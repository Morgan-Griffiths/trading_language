from pymongo import MongoClient
import pymongo
from pymongo.collection import ReturnDocument
import time
import datetime
import logging

logging.basicConfig(level=logging.ERROR, filename="logs/database_activity.log")
logger = logging.getLogger("Database_layer")


""" 
DATA MODEL
position_schema = {
    "date_created": "2021-05-01",
    "date_exited": "2021-05-01",
    "strategy": "opex",
    "user": "morgan",
    "open": False,
    "closed": False,
    "exit_placed": False,
    "enter_trades": [ids],
    "exit_trades": [ids],
}
trade_schema = {
    "placed_time": "time.time()",
    "filled_time": "None",
    "price": "inPrice",
    "symbol": "TSLA",
    "quantity": 14,
    "orderId": 12391384,
    "filled": False,
    "positionId": 435948353,
    "tradeType": "BUY",
    "tradeDirection": "OPEN",
    "assetType": "EQUITY",
} 
"""


class DataBase(object):
    def __init__(self, db):
        client = MongoClient("localhost", 27017)
        self.db = client[db]

    def drop_collection(self, collection):
        self.db.drop_collection(collection)

    def find(self, collection, data) -> pymongo.CursorType:
        return self.db[collection].find({**data})

    def update(self, collection, search_data, update_data) -> pymongo.CursorType:
        return self.db[collection].find_one_and_update(
            {**search_data}, {**update_data}, return_document=ReturnDocument.AFTER
        )

    def insert(self, collection, data) -> pymongo.CursorType:
        return self.db[collection].insert_one({**data})

    ### TRADES ###
    def find_working_orders(self, data) -> pymongo.CursorType:
        return self.db["working_orders"].find({**data})

    def find_open_order(self, data) -> bool:
        order_exists = False
        try:
            orders = self.db["working_orders"].find({**data})
            for order in orders:
                today = datetime.datetime.now()
                order_day = datetime.datetime.fromtimestamp(order["time"])
                if today.date() == order_day.date():
                    order_exists = True
                    logger.info("Order exists", order)
                    break
        except Exception as e:
            logger.info("New order")
        return order_exists

    def update_order(self, symbol, tradeDirection, tradeType, strategy) -> None:
        self.db["working_orders"].find_one_and_update(
            {
                "symbol": symbol,
                "tradeDirection": tradeDirection,
                "tradeType": tradeType,
                "strategy": strategy,
            },
            {"$set": {"filled": True, "status": "success"}},
        )

    def update_spread_order(self, symbol, tradeDirection, tradeType, strategy) -> None:
        self.db["working_orders"].find_one_and_update(
            {
                "buy_symbol": symbol,
                "positionType": "spread",
                "tradeDirection": tradeDirection,
                "tradeType": tradeType,
                "strategy": strategy,
            },
            {"$set": {"filled": True, "status": "success"}},
        )

    def find_order(
        self, symbol, user, tradeDirection, tradeType, strategy
    ) -> pymongo.CursorType:
        return self.db["working_orders"].find_one(
            {
                "symbol": symbol,
                "tradeDirection": tradeDirection,
                "tradeType": tradeType,
                "user": user,
                "strategy": strategy,
            }
        )

    def store_spread_order(
        self,
        data,
        orderId,
        positionId,
    ) -> str:
        logger.info("store_spread_order", data)
        result = self.db["working_orders"].insert_one(
            {
                "time": time.time(),
                "date": str(datetime.datetime.now().date()),
                "orderId": orderId,
                "filled": False,
                "status": "working",
                "positionId": positionId,
                "orderType": "spread",
                **data,
            }
        )
        return result.inserted_id

    def store_order(
        self, data, inPrice, symbol, num_shares, orderId, positionId
    ) -> str:
        result = self.db["working_orders"].insert_one(
            {
                "time": time.time(),
                "date": str(datetime.datetime.now().date()),
                "price": inPrice,
                "symbol": symbol,
                "quantity": num_shares,
                "orderId": orderId,
                "filled": False,
                "status": "working",
                "positionId": positionId,
                "orderType": "single",
                **data,
            }
        )
        return result.inserted_id

    def return_position_orders(self, positionIds: list) -> list:
        return list(
            self.db["working_orders"].find({"positionId": {"$in": positionIds}})
        )

    ### POSITIONS ###
    def return_open_positions(self, strategy: str) -> list:
        # find unique position ids with open trades
        res = self.db["positions"].find(
            {"open": True, "exit_placed": False, "strategy": strategy},
            {"positionId": 1},
        )
        return [r["_id"] for r in res]

    def return_exit_placed_positions(self, strategy: str) -> list:
        # find unique position ids with open trades
        res = self.db["positions"].find(
            {"open": True, "closed": False, "exit_placed": True, "strategy": strategy},
            {"positionId": 1},
        )
        return list(res)

    def close_position(self, positionId: str) -> None:
        # find unique position ids with open trades
        self.db["positions"].update_one(
            {"_id": positionId},
            {"$set": {"closed": True}},
        )

    def create_position(self, user, strategy) -> str:
        result = self.db["positions"].insert_one(
            {
                "time_created": time.time(),
                "date_created": str(datetime.date.today()),
                "date_exited": None,
                "time_exited": None,
                "strategy": strategy,
                "user": user,
                "open": False,
                "closed": False,
                "exit_placed": False,
                "enter_trades": [],
                "exit_trades": [],
            }
        )
        return result.inserted_id

    def update_position_open(self, positionId):
        self.db["positions"].update_one(
            {"_id": positionId},
            {"$set": {"open": True}},
        )

    def add_enter_trade_to_position(self, positionId, orderId):
        self.db["positions"].update_one(
            {"_id": positionId},
            {"$push": {"enter_trades": orderId}},
        )

    def update_position_close(self, positionId):
        self.db["positions"].update_one(
            {"_id": positionId},
            {"$set": {"exit_placed": True}},
        )

    def add_exit_trade_to_position(self, positionId, orderId):
        self.db["positions"].update_one(
            {"_id": positionId},
            {"$push": {"exit_trades": orderId}},
        )

    def clean_trades(self):
        unfilled_trades = list(self.db["working_trades"].find({"filled": False}))
        positionIds = set([unfilled["positionId"] for unfilled in unfilled_trades])
        self.db["working_trades"].delete_many({"filled": False})
        # delete positions without any associated trades. can do this entirely in mongo
        for positionId in positionIds:
            orders = list(self.db["working_trades"].find({"positionId": positionId}))
            if len(orders) == 0:
                self.db["positions"].delete_one({"_id": positionId})

    ### POSITIONS ###
    def find_duplicate_open_position(self, symbol, strategy) -> bool:
        print("symbol", symbol)
        positionIds = self.return_open_positions(strategy)
        orders = list(
            self.db["working_orders"].find(
                {
                    "$and": [
                        {"positionId": {"$in": positionIds}},
                        {"tradeDirection": "OPEN", "symbol": symbol},
                    ]
                }
            )
        )
        exists = True if len(orders) > 0 else False
        return exists
