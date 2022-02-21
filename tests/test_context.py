import pandas as pd
from src.infrastructure.global_interface import return_context, Interface
from src.mocks.globals import POSITIONS


def test_context_load_csv(context: Interface):
    df = context.fetch_data("stock_fundamentals")
    assert isinstance(df, pd.DataFrame)


def test_context_fetch_positions_by_asset_type(context: Interface):
    context.update_value("positions", POSITIONS["securitiesAccount"]["positions"])
    res: list = context.fetch.positions_by_asset_type("OPTION")
    print(res)
    assert res[0]["instrument"]["symbol"] == "IGC_082021P3.5"


def test_context_fetch_positions_by_asset_type_equity(context: Interface):
    context.update_value("positions", POSITIONS["securitiesAccount"]["positions"])
    res = context.fetch.positions_by_asset_type("EQUITY")
    print(res)
    assert res[0]["instrument"]["symbol"] == "MARA"
