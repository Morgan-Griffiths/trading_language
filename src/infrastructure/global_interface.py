from dataclasses import dataclass
from src.infrastructure.lazy_evaluator import resolve_dependencies
from src.infrastructure.repository_layer import RepositoryInterface
from src.infrastructure.database_layer import DataBase
from src.infrastructure.redis_layer import RedisInterface
from src.infrastructure.functions import function_list
from src.infrastructure.context_test_extensions.api_interface import FakeAPI
from src.infrastructure.context_test_extensions.portfolio_interface import FakePortfolio
from trade.api import API
from trade.config import Config
import logging

logging.basicConfig(level=logging.INFO, filename="logs/context_activity.log")
logger = logging.getLogger("Context")


@dataclass
class DataLayer:
    context: "Interface"

    def positions_by_asset_type(self, asset_type) -> list:
        positions: dict = self.context.fetch.positions()
        return [
            position
            for position in positions
            if position["instrument"]["assetType"] == asset_type
        ]

    def owned_symbols_by_asset_type(self, asset_type) -> list:
        positions: dict = self.positions_by_asset_type(asset_type)
        return [position["instrument"]["symbol"] for position in positions]

    def spy_20_day(self):
        spy_df = self.context.repo_interface.fetch("SPY")
        return spy_df["close"].mean()

    def symbol_price(self, keyword):
        value = self.context.redis_interface.retrieve_value(keyword)
        if value is None:
            value = resolve_dependencies(self, keyword)
        assert isinstance(value, int) or isinstance(value, float)
        return value

    def positions(self) -> list:
        return self.context.get_value("positions")


@dataclass
class UpdateLayer:
    context: "Interface"

    def symbol_price(self, symbol, price, expiration=5):
        assert isinstance(price, int) or isinstance(price, float)
        self.context.update_value(symbol, price, expiration)

    def symbol_price_data(self, symbol: str, price_data: dict, expiration=5):
        assert isinstance(price_data, dict)
        self.context.update_value(symbol, price_data["lastPrice"], expiration)


@dataclass
class Interface:
    repo_interface: RepositoryInterface
    db_interface: DataBase
    redis_interface: RedisInterface
    mode: str

    def __post_init__(self):
        config = Config()
        if self.mode == "test":
            config.test(self)
            self.test_portfolio = FakePortfolio(self)
        else:
            config.real()
        self.api = API(config.params)
        self.update = UpdateLayer(self)
        self.fetch = DataLayer(self)
        self.function_mapping = {func.keyword: func for func in function_list}

    def fetch_data(self, source):
        return self.repo_interface.fetch(source)

    def fetch_working_orders_by(self, field: str, value: str):
        return self.db_interface.find("working_orders", {field: value})

    def fetch_working_orders_by_params(self, params):
        return self.db_interface.find("working_orders", params)

    def update_data(self, source, data):
        return self.repo_interface.update(source, data)

    def update_value(self, keyword, value, expiration=None):
        self.redis_interface.store_value(keyword, value, expiration)

    def update_db(self, collection, search, data):
        self.db_interface.update(collection, search, data)

    def insert_order(self, inPrice, symbol, num_shares, orderId, positionId):
        self.db_interface.store_order(
            {}, inPrice, symbol, num_shares, orderId, positionId
        )

    def get_value(self, keyword):
        value = self.redis_interface.retrieve_value(keyword)
        if value is None:
            value = resolve_dependencies(self, keyword)
        return value

    def func_lookup(self, keyword):
        try:
            return self.function_mapping[keyword]
        except KeyError:
            raise KeyError(f"Missing key {keyword}")


def return_context(mode: str):
    assert mode in ["real", "test"], f"Improper mode {mode}"
    if mode == "real":
        redis = RedisInterface()
        repo = RepositoryInterface("csv_files")
        db = DataBase("ameritrade")
    else:
        redis = RedisInterface()
        repo = RepositoryInterface("test_files/test_csvs")
        db = DataBase("test")
    return Interface(repo, db, redis, mode)
