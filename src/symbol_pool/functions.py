from dataclasses import dataclass
from typing import Any, Callable
import pandas as pd
import datetime
from src.common_types import (
    CRYPTO_LIST,
    MATERIAL_LIST,
    SPAC_LIST,
    BIOTECH_LIST,
    BLACKLIST,
    ENERGY_LIST,
)
from src.infrastructure.global_interface import Interface


@dataclass
class SymbolPool:
    forward: Callable[[list[str]], list[str]]


def filter_crypto(context: Interface, symbols) -> list:
    return list(set(symbols) - set(CRYPTO_LIST))


def filter_spacs(context: Interface, symbols) -> list:
    return list(set(symbols) - set(SPAC_LIST))


def filter_biotech(context: Interface, symbols) -> list:
    return list(set(symbols) - set(BIOTECH_LIST))


def filter_energy(context: Interface, symbols) -> list:
    return list(set(symbols) - set(ENERGY_LIST))


def filter_materials(context: Interface, symbols) -> list:
    return list(set(symbols) - set(MATERIAL_LIST))


def filter_earnings(context: Interface, symbols):
    df_earnings = context.fetch_data("finviz_earnings")
    df_slice = df_earnings[df_earnings["symbol"].isin(symbols)].dropna()
    earnings_symbols = set()
    for index, row in df_slice.iterrows():
        try:
            earnings_date = datetime.datetime.strptime(
                row["Earnings Date"], "%m/%d/%Y %H:%M:%S %p"
            )
        except:
            earnings_date = datetime.datetime.strptime(row["Earnings Date"], "%m/%d/%Y")
        if (
            abs((earnings_date - datetime.datetime.now()).days) <= 1
            and abs((earnings_date - datetime.datetime.now()).days) >= -1
        ):
            earnings_symbols.add(row["symbol"])
    return list(set(symbols) - earnings_symbols)


def load_symbols(context: Interface, *args):
    symbols = [arg for arg in args]
    return symbols


def load_csv(context: Interface, local_variables, csv, *args) -> pd.DataFrame:
    df = context.fetch_data(csv)
    symbols = df["symbol"].values
    for arg in args:
        symbols = symbol_pool_funcs[arg].forward(context, local_variables, symbols)
    return symbols


symbol_pool_funcs = {
    "load_symbols": SymbolPool(
        lambda context, local_variables, *args: load_symbols(context, *args)
    ),
    "!energy": SymbolPool(
        lambda context, local_variables, symbols: filter_energy(context, symbols)
    ),
    "!materials": SymbolPool(
        lambda context, local_variables, symbols: filter_materials(context, symbols)
    ),
    "!biotech": SymbolPool(
        lambda context, local_variables, symbols: filter_biotech(context, symbols)
    ),
    "!earnings": SymbolPool(
        lambda context, local_variables, symbols: filter_earnings(context, symbols)
    ),
    "!spac": SymbolPool(
        lambda context, local_variables, symbols: filter_spacs(context, symbols)
    ),
    "!crypto": SymbolPool(
        lambda context, local_variables, symbols: filter_crypto(context, symbols)
    ),
    "positioning": SymbolPool(
        lambda context, local_variables, *args: load_csv(
            context, local_variables, "positioning", *args
        )
    ),
}
