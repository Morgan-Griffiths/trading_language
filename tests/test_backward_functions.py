import src.infrastructure.context_test_extensions.api_interface as api
import src.symbol_filters.backward_functions as bf
import pytest
import pandas as pd
from src.infrastructure.global_interface import Interface


def test_column_backwards_false(context: Interface):
    csv = "stock_fundamentals"
    bf.inverted_column_filter(
        context, {}, csv, [None], ["Volume"], ["TSLA"], ">", 50, False
    )
    df = pd.read_csv(f"test_files/test_csvs/{csv}.csv")
    assert df[df["symbol"] == "TSLA"]["Volume"].values == 50


def test_column_backwards_true(context: Interface):
    csv = "stock_fundamentals"
    bf.inverted_column_filter(
        context, {}, csv, [None], ["Volume"], ["TSLA"], ">", 50, True
    )
    df = pd.read_csv(f"test_files/test_csvs/{csv}.csv")
    assert df[df["symbol"] == "TSLA"]["Volume"].values == 51


def test_given_backwards_true(context: Interface):
    csv = "greeks"
    bf.inverted_given_filter(
        context,
        {},
        csv,
        [
            ["percent_away", ">", 0.7],
            ["percent_away", "<", 1.5],
        ],
        ["abs", "mean"],
        ["gamma"],
        ["TSLA"],
        "<",
        0.01,
        True,
    )
    df = pd.read_csv(f"test_files/test_csvs/{csv}.csv")
    symbol_row = df[df["symbol"] == "TSLA"]
    assert (
        symbol_row[
            (symbol_row["percent_away"] > 0.7) & (symbol_row["percent_away"] < 1.5)
        ]["gamma"]
        .abs()
        .mean()
        < 0.01
    )


# TODO doesn't work
def test_given_backwards_false(context):
    csv = "greeks"
    bf.inverted_given_filter(
        context,
        {},
        csv,
        [
            ["percent_away", ">", 0.7],
            ["percent_away", "<", 1.5],
        ],
        ["abs", "mean"],
        ["gamma"],
        ["TSLA"],
        "<",
        0.01,
        False,
    )
    df = pd.read_csv(f"test_files/test_csvs/{csv}.csv")
    symbol_row = df[df["symbol"] == "TSLA"]
    print("check", symbol_row["gamma"].abs().mean())
    print(
        df[df["symbol"] == "TSLA"][
            (df["percent_away"] > 0.7) & (df["percent_away"] < 1.5)
        ]["gamma"]
    )
    assert (
        symbol_row[
            (symbol_row["percent_away"] > 0.7) & (symbol_row["percent_away"] < 1.5)
        ]["gamma"]
        .abs()
        .mean()
        > 0.01
    )


def test_inverted_in_portfolio_false_false(context: Interface):
    context.update_value("TSLA", 100)
    context.test_portfolio.updateEquities(["TSLA"], ["open"])
    bf.inverted_in_portfolio(
        context,
        {"assetType": "EQUITY", "tradeDirection": "open"},
        ["TSLA"],
        False,
        False,
    )
    positions = context.fetch.positions_by_asset_type("EQUITY")
    position_symbols = [pos["instrument"]["symbol"] for pos in positions]
    assert "TSLA" in position_symbols


def test_inverted_in_portfolio_false_true(context: Interface):
    context.update_value("TSLA", 100)
    context.test_portfolio.updateEquities(["TSLA"], ["open"])
    bf.inverted_in_portfolio(
        context,
        {"assetType": "EQUITY", "tradeDirection": "open"},
        ["TSLA"],
        False,
        True,
    )
    positions = context.fetch.positions_by_asset_type("EQUITY")
    position_symbols = [pos["instrument"]["symbol"] for pos in positions]
    assert "TSLA" not in position_symbols


def test_inverted_in_portfolio_true_true(context: Interface):
    context.update_value("TSLA", 100)
    context.test_portfolio.updateEquities(["TSLA"], ["open"])
    bf.inverted_in_portfolio(
        context, {"assetType": "EQUITY", "tradeDirection": "open"}, ["TSLA"], True, True
    )
    positions = context.fetch.positions_by_asset_type("EQUITY")
    position_symbols = [pos["instrument"]["symbol"] for pos in positions]
    assert "TSLA" in position_symbols


def test_inverted_in_portfolio_true_false(context: Interface):
    context.update_value("TSLA", 100)
    context.test_portfolio.updateEquities(["TSLA"], ["open"])
    bf.inverted_in_portfolio(
        context,
        {"assetType": "EQUITY", "tradeDirection": "open"},
        ["TSLA"],
        True,
        False,
    )
    positions = context.fetch.positions_by_asset_type("EQUITY")
    position_symbols = [pos["instrument"]["symbol"] for pos in positions]
    assert "TSLA" not in position_symbols


def test_inverted_orders_true(context: Interface):
    context.insert_order(5, "TSLA", 5, 345345, 987987)
    bf.inverted_orders_filter(context, {}, ["TSLA"], "status", "rejected", True)
    orders = list(context.fetch_working_orders_by("symbol", "TSLA"))
    assert orders[0]["status"] == "passing"


def test_inverted_orders_false(context: Interface):
    context.insert_order(5, "TSLA", 5, 345345, 987987)
    bf.inverted_orders_filter(context, {}, ["TSLA"], "status", "rejected", False)
    orders = list(context.fetch_working_orders_by("symbol", "TSLA"))
    assert orders[0]["status"] == "rejected"


def test_inverted_price_true(context: Interface):
    context.update_value("TSLA", 100)
    bf.inverted_price_filter(context, {}, ["TSLA"], ">", 100, True)
    assert context.fetch.symbol_price("TSLA") > 100


def test_inverted_price_false(context: Interface):
    context.update_value("TSLA", 100)
    bf.inverted_price_filter(context, {}, ["TSLA"], ">", 100, False)
    assert context.fetch.symbol_price("TSLA") == 100
