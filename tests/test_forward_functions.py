import pandas as pd
import numpy as np
from src.infrastructure.global_interface import return_context
from src.interpreter.common_funcs import binaryOperators
from src.symbol_filters.forward_functions import (
    filter_by_column,
    filter_given,
    symbol_in_portfolio,
)


def test_filter_by_column(context):
    # df = pd.DataFrame.from_dict(
    #     {"symbol": ["TSLA", "AAPL"], "Volume": [40, 60], "Average Volume": [40, 60]}
    # )
    pandas_operations = ["max"]
    columns = ["Volume", "Average Volume"]
    symbols = ["TSLA", "AAPL"]
    operator = ">"
    amount = 50
    result = filter_by_column(
        context,
        {},
        csv="stock_fundamentals",
        pandas_operations=pandas_operations,
        columns=columns,
        symbols=symbols,
        operator=operator,
        amount=amount,
    )
    print(result)
    assert list(result) == ["AAPL", "TSLA"]


def test_given(context):
    # df = pd.DataFrame.from_dict(
    #     {
    #         "index": list(range(0, 10)),
    #         "symbol": ("TSLA " * 5 + "AAPL " * 5).split(),
    #         "percent_away": list(np.linspace(0, 2, 5)) + (list(np.linspace(0, 2, 5))),
    #         "gamma": [5] * 5 + [1] * 5,
    #     }
    # )
    result = filter_given(
        context,
        {},
        csv="greeks",
        conditions=[["percent_away", ">", 0.7], ["percent_away", "<", 1.5]],
        final_pandas_operations=["abs", "mean"],
        columns=["gamma"],
        symbols=["TSLA", "AAPL"],
        operator=">",
        amount=3,
    )
    assert result == []


def test_in_portfolio_false(context):
    result = symbol_in_portfolio(
        context, {"assetType": "EQUITY"}, symbols=["TSLA"], inside=False
    )
    assert result == ["TSLA"]


def test_in_portfolio_true(context):
    result = symbol_in_portfolio(
        context, {"assetType": "EQUITY"}, symbols=["TSLA"], inside=True
    )
    assert result == []
