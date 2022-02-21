from typing import Any
import pandas as pd
import numpy as np
import calendar
import datetime
import pickle
import json
import os


def to_readable(res):
    if isinstance(res, list):
        return [to_readable(r) for r in res]
    return res.lexeme


def parse_datetime(dtime):
    """ "2021-11-18 16:02:39.866438" """
    if isinstance(dtime, str):
        try:
            return datetime.datetime.strptime(dtime, "%Y-%m-%d %H:%M:%S.%f")
        except:
            return datetime.datetime.strptime(dtime, "%Y-%m-%d %H:%M:%S")
    return dtime


def parse_date(dtime: str):
    """ "2021-11-18" """
    if isinstance(dtime, str):
        return datetime.datetime.strptime(dtime, "%Y-%m-%d").date()
    return dtime


real_additions = {
    ">": [1e-2, -1e-6],
    ">=": [-1e-2, 1e-6],
    "<": [-1e-2, 1e-6],
    "<=": [-1e-2, 1e-6],
    "==": [0, 1e-2],
    "!=": [1e-2, 0],
}
int_additions = {
    ">": [1, 0],
    ">=": [0, -1],
    "<": [-1, 0],
    "<=": [0, 1],
    "==": [0, 1],
    "!=": [1, 0],
}
datetime_additions = {
    ">": [datetime.timedelta(days=1), datetime.timedelta(days=0)],
    ">=": [datetime.timedelta(days=0), datetime.timedelta(days=-1)],
    "<": [datetime.timedelta(days=-1), datetime.timedelta(days=0)],
    "<=": [datetime.timedelta(days=0), datetime.timedelta(days=1)],
    "==": [datetime.timedelta(days=0), datetime.timedelta(days=1)],
    "!=": [datetime.timedelta(days=1), datetime.timedelta(days=0)],
}


def load_trade(trade: str, folder="output_descriptions") -> dict:
    file_path = os.path.join(os.getcwd(), folder, trade + ".json")
    with open(file_path, "rb") as f:
        positionDescription: dict = json.load(f)
    return positionDescription


def add_to_dict(values, operand, left, right):
    if isinstance(right, float):
        adds = real_additions[operand]
    elif isinstance(right, datetime.date):
        adds = datetime_additions[operand]
    elif isinstance(right, int):
        adds = int_additions[operand]
    if isinstance(right, bool):
        values[left] = [True, False]
    elif left in values:
        values[left].extend([right + adds[0], right + adds[1]])
    else:
        values[left] = [right + adds[0], right + adds[1]]


def return_desired_amount(operand, cutoff, passFail):
    values = {}
    add_to_dict(values, operand, "left", cutoff)
    return values["left"][0] if passFail else values["left"][1]


def load_pickle(file_name: str) -> Any:
    with open(f"{file_name}.pickle", "rb") as handle:
        b = pickle.load(handle)
    return b


def strip_unnamed_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.str.contains("^Unnamed")]


## TEMP UTILS


def get_ATM_volatility(data: pd.DataFrame) -> float:
    price = data["current_price"].values[0]
    diff = data["strikePrice"] - price
    min_val = diff.abs().min()
    df_diff = (
        data[diff == -min_val] if diff[diff == min_val].empty else data[diff == min_val]
    )
    atm_vol: float = df_diff.iloc[0, :]["volatility"]
    return atm_vol


def spy_sigma(spy: float, iv: float, DUE: int) -> float:
    # iv = ATM volatity,days until expiration
    return spy * iv * np.sqrt(DUE / 252.75)


def return_opex(month: int, year: int) -> datetime.date:
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)
    monthcal = c.monthdatescalendar(year, month)
    opex = [
        day
        for week in monthcal
        for day in week
        if day.weekday() == calendar.FRIDAY and day.month == month
    ][2]
    return opex


def third_friday(current_time=datetime.datetime.now().date()) -> datetime.date:
    opex = return_opex(current_time.month, current_time.year)
    if current_time > opex:
        days = calendar.monthrange(current_time.year, current_time.month)[1]
        remaining_days = days - current_time.day
        current_time = datetime.datetime.now() + datetime.timedelta(
            days=remaining_days + 1
        )
        opex = return_opex(current_time.month, current_time.year)
    return opex
