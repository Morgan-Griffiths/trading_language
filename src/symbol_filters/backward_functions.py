from src.constructors.pandas_constructor import PandasBuilder
from src.utils import return_desired_amount, strip_unnamed_columns
from src.infrastructure.global_interface import Interface
from src.common_types import operators


def inverted_column_filter(
    context: Interface,
    local_variables: dict,
    data_source,
    pandas_operations: list,
    columns,
    symbols,
    operand,
    amount,
    evaluates_to: bool,
) -> None:
    if len(columns) == 1:
        columns = columns[0]
    df = context.fetch_data(data_source)
    desired_amount = return_desired_amount(operand, amount, evaluates_to)
    print("desired_amount", desired_amount)
    for symbol in symbols:
        df.loc[df["symbol"] == symbol, columns] = desired_amount
        break
    df = strip_unnamed_columns(df)
    context.update_data(data_source, df)


def inverted_given_filter(
    context: Interface,
    local_variables: dict,
    data_source: str,
    conditions: list,
    final_pandas_operations: list,
    columns: list,
    symbols: str,
    operator: str,
    amount: float,
    evaluates_to: bool,
):
    df = context.fetch_data(data_source)
    for symbol in symbols:
        print("symbol", symbol)
        symbol_row = df[df["symbol"] == symbol]
        expr = PandasBuilder().set_name("symbol_row")
        for condition in conditions:
            column, sub_op, amt = condition
            expr.add_column_select_amount_comparison(
                op=sub_op, amount=amt, columns=column
            )
        expr = (
            expr.add_final_column_select(columns, final_pandas_operations)
            .add_final_boolean_op(operator, amount)
            .build()
        )
        print("expr", expr)
        result = eval(expr)
        print("result", result, "evaluates_to", evaluates_to)
        if (not result and evaluates_to == True) or (result and evaluates_to == False):
            # adjust the value
            desired_amount = return_desired_amount(
                operator, amount, evaluates_to
            )  # + 1e-6
            df.loc[df["symbol"] == symbol, columns] = desired_amount
        break
    context.update_data(data_source, df)


def inverted_in_portfolio(
    context: Interface,
    local_variables: dict,
    symbols: list,
    inside: str,
    evaluates_to: bool,
) -> list:
    asset_type = local_variables["assetType"]
    direction = local_variables["tradeDirection"]
    portfolio = context.fetch.positions_by_asset_type(asset_type)
    current_asset_symbols = {position["instrument"]["symbol"] for position in portfolio}
    outside_portfolio = set(symbols) - current_asset_symbols
    inside_portfolio = set(symbols) - outside_portfolio
    # if inside and True make sure symbols are inside
    # if inside and False make sure symbols are not inside
    # if not inside and True make sure symbols are not inside
    # if not inside and False make sure symbols are inside
    if evaluates_to:
        if not bool(inside):
            context.test_portfolio.removeSymbols(symbols)
        else:
            if symbols[0] not in inside_portfolio:
                context.test_portfolio.updateEquities(symbols[0], direction)
    else:
        if bool(inside):
            context.test_portfolio.removeSymbols(symbols)
        else:
            if symbols[0] not in inside_portfolio:
                context.test_portfolio.updateEquities(symbols[0], direction)


def inverted_price_filter(
    context: Interface, local_variables: dict, symbols, op, cutoff, evaluates_to: bool
) -> None:
    desired_amount = return_desired_amount(op, cutoff, evaluates_to)
    context.update.symbol_price(symbols[0], desired_amount)


def inverted_orders_filter(
    context: Interface, local_variables: dict, symbols, field, value, evaluates_to: bool
) -> None:
    # TODO
    # if false, i reject no symbols
    # if true i reject all symbols
    if evaluates_to:
        for symbol in symbols:
            context.update_db(
                "working_orders", {"symbol": symbol}, {"$set": {field: "passing"}}
            )
    else:
        for symbol in symbols:
            context.update_db(
                "working_orders", {"symbol": symbol}, {"$set": {field: value}}
            )
