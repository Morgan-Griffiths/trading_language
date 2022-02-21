from typing import Callable
import pandas as pd
from src.constructors.pandas_constructor import PandasBuilder
from src.infrastructure.global_interface import Interface
from src.common_types import operators


def filter_by_column(
    context: Interface,
    local_variables: dict,
    csv: str,
    pandas_operations: list,
    columns: list,
    symbols: list,
    operator: str,
    amount,
) -> list:
    df = context.fetch_data(csv)
    expr = (
        PandasBuilder()
        .set_name("df")
        .add_column_select_symbol_isin()
        .add_column_select_amount_comparison(
            op=operator, amount=amount, columns=columns, aggs=pandas_operations, axis=1
        )
        .add_final_column_select(["symbol"])
        .add_values()
        .build()
    )
    print("expr", expr)
    return list(eval(expr))


def filter_given(
    context: Interface,
    local_variables: dict,
    csv: pd.DataFrame,
    conditions: list,
    final_pandas_operations: list,
    columns: list,
    symbols: str,
    operator: float,
    amount: bool,
):
    df = context.fetch_data(csv)
    buy_symbols = []
    for symbol in symbols:
        symbol_row = df[df["symbol"] == symbol]
        expr = PandasBuilder().set_name("symbol_row")
        for condition in conditions:
            column, op, amt = condition
            expr.add_column_select_amount_comparison(
                op=operator, amount=amt, columns=column
            )
        expr = (
            expr.add_final_column_select(columns, final_pandas_operations)
            .add_final_boolean_op(operator, amount)
            .build()
        )
        result = eval(expr)
        if result:
            buy_symbols.append(symbol)
    return buy_symbols


def symbol_in_portfolio(
    context: Interface, local_variables: dict, symbols: list, inside: str
) -> list:
    positions = context.fetch.positions_by_asset_type(local_variables["assetType"])
    current_asset_symbols = {position["instrument"]["symbol"] for position in positions}
    outside_portfolio = set(symbols) - current_asset_symbols
    inside_portfolio = set(symbols) - outside_portfolio
    if inside:
        return list(inside_portfolio)
    return list(outside_portfolio)


def filter_price(context: Interface, local_variables: dict, symbols, op, cutoff):
    operator = operators[op]
    available_symbols = []
    for symbol in symbols:
        price = context.fetch.symbol_price(symbol)
        if operator(price, cutoff):
            available_symbols.append(symbol)
    return available_symbols


def filter_orders(context: Interface, local_variables: dict, symbols, field, value):
    orders = context.fetch_working_orders_by(field, value)
    rejected_symbols = {ord["symbol"] for ord in orders}
    return list(set(symbols) - rejected_symbols)
