import numpy as np
from scipy.stats import norm
import datetime
from typing import Any
import re
import os
import time
import pandas as pd
import sympy
import pickle
import calendar
from twilio.rest import Client

risk_free = 0.07
CAL = {month: index for index, month in enumerate(calendar.month_abbr) if month}


def twilio_send_message(msg: str, number: int) -> None:
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"{msg}",
        from_="+13344328938",
        provide_feedback=True,
        to=f"+1{number}",
    )
    print("msg", msg)
    print(message.sid)


def shape_price(amount: float) -> float:
    if amount > 1:
        return round(amount, 2)
    else:
        return round(amount, 4)


def return_positioning(
    n: int, partial: float, price: float, option_row: pd.Series
) -> float:
    call_mask = option_row["putCall"] == "CALL"
    put_mask = option_row["putCall"] == "PUT"
    expirations = option_row["tradingDays"].values
    time_til_exp = np.array([(exp - n + partial) / 252.75 for exp in expirations])
    time_til_exp = np.clip(time_til_exp, 0, 5)
    d1: np.array = delta1(
        price,
        option_row["strikePrice"],
        0.007,
        option_row["volatility"] / 100,
        time_til_exp,
    )
    call_deltas = norm.cdf(d1[call_mask])
    put_deltas = -norm.cdf(-d1[put_mask])
    deltas = np.empty_like(option_row["delta"].values)
    deltas[call_mask.values] = call_deltas
    deltas[put_mask.values] = put_deltas
    market_positions: pd.Series = market_position(deltas, option_row["openInterest"])
    return market_positions.sum()


def N_prime(d_1: float) -> float:
    return (np.e ** -(d_1 ** 2 / 2)) * 1 / 2 * np.pi


def calc_vanna(d_1: float, time_til_exp: float) -> float:
    return np.sqrt(time_til_exp) * N_prime(d_1) * (1 - d_1)


def calc_volga(d_1: float, d_2: float, time_til_exp: float, imp_vol: float) -> float:
    return np.sqrt(time_til_exp) * N_prime(d_1) * ((d_1 * d_2) / imp_vol)


def vega(underlying_price: float, d_1: float, time_til_exp: float) -> float:
    return underlying_price * np.sqrt(time_til_exp) * N_prime(d_1)


def delta1(
    price: float,
    strike: float,
    risk_free_rate: float,
    volatility: float,
    time_til_exp: float,
) -> float:
    try:
        result: float = (
            np.log(price / strike)
            + (risk_free_rate + (volatility ** 2 / 2)) * time_til_exp
        ) / (volatility * np.sqrt(time_til_exp))
    except Exception as e:
        result = 0
    return result


def delta2(
    d1: float,
    volatility: float,
    time_til_exp: float,
) -> float:
    try:
        result: float = d1 - volatility * np.sqrt(time_til_exp)
    except Exception as e:
        result = 0
    return result


def deltas(
    price: float,
    strike: float,
    risk_free_rate: float,
    volatility: float,
    time_til_exp: float,
) -> tuple[float, float]:
    d1: float = delta1(price, strike, risk_free_rate, volatility, time_til_exp)
    d2: float = delta2(d1, volatility, time_til_exp)
    return d1, d2


def call_price(
    price: float,
    strike: float,
    risk_free_rate: float,
    volatility: float,
    time_til_exp: float,
    d1: float,
    d2: float,
) -> float:
    C: float = norm.cdf(d1) * price - norm.cdf(d2) * strike * np.exp(
        -risk_free_rate * time_til_exp
    )
    return C


def put_price(
    price: float,
    strike: float,
    risk_free_rate: float,
    volatility: float,
    time_til_exp: float,
    d1: float,
    d2: float,
) -> float:
    C: float = -norm.cdf(d1) * price - norm.cdf(d2) * strike * np.exp(
        -risk_free_rate * time_til_exp
    )
    return C


def delta(d1: float, contract: str) -> float:
    if contract == "CALL":
        call_result: float = norm.cdf(d1)
        return call_result
    elif contract == "PUT":
        put_result: float = -norm.cdf(-d1)
        return put_result
    else:
        raise ValueError(f"Contract type")


def extract_date_from_description(data: list[Any]) -> datetime.date:
    raw: Any = re.search(
        r"\s([A-Za-z]+)\s(\d+)\s(\d+)\s",
        data,
    )
    month = raw.group(1)
    day = raw.group(2)
    year = raw.group(3)
    month_digit = CAL[month]
    expDate = datetime.date(int(year), month_digit, int(day))
    return expDate


def return_porfolio_symbols(positions: list, assetType: str):
    """Only takes 1 symbol type at a type: option or equity"""
    print("return_porfolio_symbols", positions)
    if assetType == "OPTION":
        symbols = [pos["instrument"]["underlyingSymbol"] for pos in positions]
    else:
        symbols = [pos["instrument"]["symbol"] for pos in positions]
    return symbols


def save_pickle(stuff, file_name: str) -> None:
    with open(f"{file_name}.pickle", "wb") as handle:
        pickle.dump(stuff, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(file_name: str) -> Any:
    with open(f"{file_name}.pickle", "rb") as handle:
        b = pickle.load(handle)
    return b


def return_exit_tradeType(tradeType: str, asset_type: str) -> str:
    if asset_type == "EQUITY":
        if tradeType == "BUY":
            exitType = "SELL"
        elif tradeType == "SELL_SHORT":
            exitType = "BUY_TO_COVER"
        else:
            raise ValueError(f"improper tradeType {tradeType}")
    else:
        if tradeType == "BUY_TO_OPEN":
            exitType = "SELL_TO_CLOSE"
        elif tradeType == "SELL_TO_OPEN":
            exitType = "BUY_TO_CLOSE"
        else:
            raise ValueError(f"improper tradeType {tradeType}")
    return exitType


def return_stop(tradeType: str, inPrice: float, distance: float) -> float:
    if tradeType == "BUY" or tradeType == "BUY_TO_OPEN":
        exitPrice = inPrice - (inPrice * distance)
    else:
        exitPrice = inPrice + (inPrice * distance)
    return round(exitPrice, 2)


def n_day_delta(
    price: float,
    expDate: datetime.date,
    contractType: str,
    strike: float,
    volatility: float,
    dayoffset: int,
) -> float:
    """Volatility is / 100"""
    # days_to_exp = trading_days(expDate.day)
    t_delta = expDate - datetime.date.today()
    option_exp_delta = t_delta.days - dayoffset
    time_til_exp = (option_exp_delta + partial_day()) / 252.75
    d1, d2 = deltas(price, strike, risk_free, volatility, time_til_exp)
    #     C = call_price(price,strike,risk_free,volatility,time_til_exp,d1,d2)
    return delta(d1, contractType)


def market_position(delta: np.array, open_interest: pd.Series) -> pd.Series:
    return delta * 100 * open_interest


def actual_trading_days(start, end) -> int:
    """Returns number of trading days starting from today"""
    days: int = np.busday_count(
        np.array(np.datetime64(start)), np.array(np.datetime64(end))
    )
    return days


def trading_days(exp: int, start=datetime.date.today()) -> int:
    """Returns number of trading days starting from today"""
    end = start + datetime.timedelta(days=int(exp))
    days: int = int(np.busday_count(start, end))
    return days


def send_alert(message: str, phoneNumber: int) -> None:
    os.system(
        f"osascript /Users/morgan/Code/Send_text.scpt '{message}' '{phoneNumber}'"
    )


def previous_trading_day() -> int:
    n = 1
    start = (datetime.datetime.now() - datetime.timedelta(days=n)).date()
    end = datetime.datetime.now().date()
    days: int = np.busday_count(start, end)
    while days < 1:
        n += 1
        start = (datetime.datetime.now() - datetime.timedelta(days=n)).date()
        days: np.int = np.busday_count(start, end)
    return int(days)


def remove_earning_symbols(symbols: list[str]) -> list[str]:
    df_earnings = pd.read_csv("csv_files/finviz_earnings.csv")
    df_slice = df_earnings[df_earnings["symbol"].isin(symbols)].dropna()
    earnings_symbols = []
    for index, row in df_slice.iterrows():
        try:
            earnings_date = datetime.datetime.strptime(
                row["Earnings Date"], "%m/%d/%Y %H:%M:%S %p"
            )
        except:
            earnings_date = datetime.datetime.strptime(row["Earnings Date"], "%m/%d/%Y")
        if abs((earnings_date - datetime.datetime.now()).days) <= 1:
            earnings_symbols.append(row["symbol"])
    return earnings_symbols


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


def partial_day() -> float:
    trading_minutes = 390
    now = datetime.datetime.now()
    market_beginning = datetime.datetime(now.year, now.month, now.day, 6, 3)
    market_end = datetime.datetime(now.year, now.month, now.day, 13)
    if now < market_beginning:
        now = market_beginning
    elif now > market_end:
        now = market_end
    diff = (market_end - now).total_seconds() / 60
    return max(diff / trading_minutes, 0)


def strip_unnamed_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.str.contains("^Unnamed")]


def convert_to_timestamp(time_obj: datetime.datetime) -> float:
    return time.mktime(time_obj.timetuple())


def convert_from_timestamp(unix_ts: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(unix_ts, datetime.timezone.utc)


def find_0_charm(greek_df: pd.DataFrame, symbol: str) -> float:
    symbol_row = greek_df[greek_df["symbol"] == symbol]
    position_values = symbol_row["charm"].values
    strike_values = symbol_row["strike"].values
    prev_dealer_position = position_values[0]
    charm_0_strike = np.inf
    for strike, dealer_position in zip(strike_values[1:], position_values[1:]):
        if (
            prev_dealer_position > 0
            and (dealer_position == 0 or dealer_position < 0)
            or prev_dealer_position < 0
            and (dealer_position == 0 or dealer_position > 0)
        ):
            charm_0_strike = strike
            break
    return charm_0_strike


if __name__ == "__main__":
    print(third_friday())
