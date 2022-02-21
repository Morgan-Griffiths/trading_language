from src.constructors.pandas_constructor import PandasBuilder
import pandas as pd
import pytest


# df[(df["symbol"].isin(symbols))& (operator.forward(df[columns].mean(axis="columns"), amount))]["symbol"].values
# df[(df["symbol"].isin(symbols)) & (operator.forward(df[columns], amount))]["symbol"].values
# df[(df["symbol"].isin(symbols)) & (operator.forward(df[columns], amount))]["symbol"].values
# symbol_gamma[(operator.forward(symbol_gamma["percent_away"],start_percent)) & (symbol_gamma["percent_away"] < end_percent)][greek].abs().mean()


def test_isin():
    result = PandasBuilder().set_name("df").add_column_select_symbol_isin().build()
    assert result == "df[(df['symbol'].isin(symbols))]"


def test_no_agg():
    result = (
        PandasBuilder()
        .set_name("df")
        .add_column_select_symbol_isin()
        .add_column_select_amount_comparison(
            op=">", amount="amount", columns=["columns"]
        )
        .build()
    )
    assert result == "df[(df['symbol'].isin(symbols)) & (df['columns'] > amount)]"


def test_no_agg_values():
    result = (
        PandasBuilder()
        .set_name("df")
        .add_column_select_symbol_isin()
        .add_column_select_amount_comparison(
            op=">", amount="amount", columns=["columns"]
        )
        .add_values()
        .build()
    )
    assert (
        result == "df[(df['symbol'].isin(symbols)) & (df['columns'] > amount)].values"
    )


def test_mean():
    result = (
        PandasBuilder()
        .set_name("df")
        .add_column_select_symbol_isin()
        .add_column_select_amount_comparison(
            op=">", amount="amount", columns=["columns"], aggs=["mean"], axis=1
        )
        .add_values()
        .add_final_column_select(["symbol"])
        .build()
    )

    assert (
        result
        == "df[(df['symbol'].isin(symbols)) & (df['columns'].mean(axis=1) > amount)]['symbol'].values"
    )


def test_abs_mean():
    result = (
        PandasBuilder()
        .set_name("df")
        .add_column_select_symbol_isin()
        .add_column_select_amount_comparison(
            op=">", amount="amount", columns=["columns"], aggs=["mean", "abs"], axis=1
        )
        .add_values()
        .add_final_column_select(["symbol"])
        .build()
    )

    assert (
        result
        == "df[(df['symbol'].isin(symbols)) & (df['columns'].abs().mean(axis=1) > amount)]['symbol'].values"
    )


def test_greek_long():
    result = (
        PandasBuilder()
        .set_name("symbol_gamma")
        .add_column_select_amount_comparison(
            op="<", amount="start_percent", columns=["percent_away"]
        )
        .add_column_select_amount_comparison(
            op=">", amount="end_percent", columns=["percent_away"]
        )
        .add_final_column_select(["greek"], aggs=["abs", "mean"], agg_reversed=False)
        .build()
    )
    assert (
        result
        == "symbol_gamma[(symbol_gamma['percent_away'] < start_percent) & (symbol_gamma['percent_away'] > end_percent)]['greek'].abs().mean()"
    )
