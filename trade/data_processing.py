from typing import Any
from trade.utils import (
    calc_vanna,
    calc_volga,
    convert_to_timestamp,
    delta1,
    delta2,
    market_position,
    partial_day,
    return_positioning,
    trading_days,
)
from trade.api import API
from src.infrastructure.database_layer import DataBase
from trade.config import Config
from scipy.stats import norm
import pandas as pd
import numpy as np
import datetime
import json
import time
import sys
import os

RISK_FREE_RATE = 0.07


class DataProcessor(object):
    def __init__(self):
        config = Config()
        config.real()
        self.api = API(config.params)
        self.db = DataBase("ameritrade")

    def update_fundamentals_csv(self) -> None:
        start_time = time.time()
        df_stock = pd.read_csv("csv_files/stock_fundamentals.csv")
        df_fundamentals = pd.read_csv("csv_files/finviz_fundamentals.csv")
        labels = [col for col in df_stock.columns if "Unnamed" in col]
        if labels:
            df_stock = df_stock.drop(labels, axis="columns")
        labels = [col for col in df_fundamentals.columns if "Unnamed" in col]
        if labels:
            df_fundamentals = df_fundamentals.drop(labels, axis="columns")
        symbols = set(df_stock["symbol"].values)
        fundamental_symbols = set(df_fundamentals["symbol"].values)
        remaining = np.array(list(set(symbols) - set(fundamental_symbols)))
        df = pd.concat(
            [df_fundamentals, df_stock[df_stock["symbol"].isin(remaining)]],
            ignore_index=True,
        )
        missing_float_symbols = df[df["Shares Float"].isnull()]["symbol"].unique()
        for i, symbol in enumerate(missing_float_symbols):
            try:
                stock_data = self.api.get_fundamentals(symbol)[symbol]["fundamental"]
                row_idx = df.index[df["symbol"] == symbol].tolist()
                df.loc[row_idx, df.columns == "Shares Float"] = stock_data[
                    "marketCapFloat"
                ]
            except Exception as e:
                print(f"{symbol}, {e}")
            # sys.stdout.write("\r")
            # sys.stdout.write(
            #     "[%-60s] %d%%"
            #     % (
            #         "=" * (60 * (i + 1) // len(missing_float_symbols)),
            #         (100 * (i + 1) // len(missing_float_symbols)),
            #     )
            # )
            # sys.stdout.write(f",{i} / {len(missing_float_symbols)}")
            # sys.stdout.flush()
        print(f"Elapsed time {(time.time() - start_time) / 60}")
        df.to_csv("csv_files/stock_fundamentals.csv")

    def convert_charm_to_csv(self) -> None:
        with open("files/dealer_charm.json") as json_file:
            dealer_charm = dict(json.load(json_file))
        pd_dict: dict[str, list[str]] = {
            "symbol": [],
            "price": [],
            "positioning": [],
        }
        for symbol in dealer_charm.keys():
            for price, position in zip(
                dealer_charm[symbol]["price"], dealer_charm[symbol]["positioning"]
            ):
                pd_dict["symbol"].append(symbol)
                pd_dict["price"].append(price)
                pd_dict["positioning"].append(position)
        df = pd.DataFrame.from_dict(pd_dict)
        print(len(df["symbol"].unique()))
        df.to_csv("csv_files/charm.csv")

    def convert_greeks_to_csv(self) -> None:
        start = time.time()
        current_date = datetime.datetime.now().date()
        df_finviz = pd.read_csv("csv_files/finviz.csv")
        with open("files/dealer_greeks.json") as json_file:
            dealer_vanna = dict(json.load(json_file))
        pd_dict: dict[str, list[str]] = {
            "symbol": [],
            "price": [],
            "strike": [],
            "charm": [],
            "gamma": [],
            "vanna": [],
            "volga": [],
            "percent_away": [],
            "date": [],
        }
        symbols = list(dealer_vanna.keys())
        for i, symbol in enumerate(symbols):
            try:
                # if i % 100 == 0:
                #     price_data = self.get_symbols_prices(symbols[:100])
                stock_price = df_finviz[df_finviz["symbol"] == symbol]["Price"].values[
                    0
                ]
                # stock_price = price_data[symbol]["lastPrice"]
            except:
                try:
                    (
                        bidPrice,
                        askPrice,
                        midpoint,
                        margin,
                        spread,
                    ) = self.api.get_price_points(symbol)
                    stock_price = midpoint
                except:
                    stock_price = 1e-7
            values = []
            symbol_dict: dict[str, list[str]] = {
                "symbol": [],
                "price": [],
                "strike": [],
                "charm": [],
                "gamma": [],
                "vanna": [],
                "volga": [],
                "percent_away": [],
                "date": [],
            }
            charm = dealer_vanna[symbol]["charm"]
            gamma = dealer_vanna[symbol]["gamma"]
            vanna = dealer_vanna[symbol]["vanna"]
            volga = dealer_vanna[symbol]["volga"]
            strikes = dealer_vanna[symbol]["strikes"]
            for strike, charm, gamma, vanna, volga in zip(
                strikes, charm, gamma, vanna, volga
            ):
                percent_away = round(float(strike) / stock_price, 3)
                symbol_dict["symbol"].append(symbol)
                symbol_dict["price"].append(stock_price)
                symbol_dict["strike"].append(strike)
                symbol_dict["charm"].append(charm)
                symbol_dict["gamma"].append(gamma)
                symbol_dict["vanna"].append(vanna)
                symbol_dict["volga"].append(volga)
                symbol_dict["percent_away"].append(percent_away)
                symbol_dict["date"].append(current_date)
                if percent_away > 0.7 or percent_away < 1.5:
                    values.append(gamma)
            if abs(values[0]) != np.inf and not np.isnan(values[0]):
                for index in range(len(symbol_dict["symbol"])):
                    pd_dict["symbol"].append(symbol_dict["symbol"][index])
                    pd_dict["price"].append(symbol_dict["price"][index])
                    pd_dict["strike"].append(symbol_dict["strike"][index])
                    pd_dict["charm"].append(symbol_dict["charm"][index])
                    pd_dict["gamma"].append(symbol_dict["gamma"][index])
                    pd_dict["vanna"].append(symbol_dict["vanna"][index])
                    pd_dict["volga"].append(symbol_dict["volga"][index])
                    pd_dict["percent_away"].append(symbol_dict["percent_away"][index])
                    pd_dict["date"].append(symbol_dict["date"][index])
        df = pd.DataFrame.from_dict(pd_dict)
        print(len(df["symbol"].unique()))
        df.to_csv("csv_files/greeks.csv")
        print(f"Convert to greeks took {(time.time() - start) / 60} minutes")

    def convert_gamma_to_csv(self) -> None:
        current_date = datetime.datetime.now().date()
        df_finviz = pd.read_csv("csv_files/finviz.csv")
        with open("dealer_gamma.json") as json_file:
            dealer_gamma = dict(json.load(json_file))
        pd_dict: dict[str, list[str]] = {
            "symbol": [],
            "strike": [],
            "gamma": [],
            "percent_away": [],
            "date": [],
        }
        for symbol in dealer_gamma.keys():
            try:
                stock_price = df_finviz[df_finviz["symbol"] == symbol]["Price"].values[
                    0
                ]
            except:
                try:
                    (
                        bidPrice,
                        askPrice,
                        midpoint,
                        margin,
                        spread,
                    ) = self.api.get_price_points(symbol)
                    stock_price = midpoint
                except:
                    stock_price = 1e-7
            values = []
            symbol_dict: dict[str, list[str]] = {
                "symbol": [],
                "strike": [],
                "gamma": [],
                "percent_away": [],
                "date": [],
            }
            for k, v in dealer_gamma[symbol].items():
                percent_away = round(float(k) / stock_price, 3)
                symbol_dict["symbol"].append(symbol)
                symbol_dict["strike"].append(k)
                symbol_dict["gamma"].append(v)
                symbol_dict["percent_away"].append(percent_away)
                symbol_dict["date"].append(current_date)
                if percent_away > 0.7 or percent_away < 1.5:
                    values.append(v)
            if abs(values[0]) != np.inf and not np.isnan(values[0]):
                for index in range(len(symbol_dict["symbol"])):
                    pd_dict["symbol"].append(symbol_dict["symbol"][index])
                    pd_dict["strike"].append(symbol_dict["strike"][index])
                    pd_dict["gamma"].append(symbol_dict["gamma"][index])
                    pd_dict["percent_away"].append(symbol_dict["percent_away"][index])
                    pd_dict["date"].append(symbol_dict["date"][index])
        df = pd.DataFrame.from_dict(pd_dict)
        print(len(df["symbol"].unique()))
        df.to_csv("csv_files/gamma.csv")

    def get_symbol_greeks(
        self,
        fundamental_path="/stock_fundamentals.csv",
        IV_path="IV.csv",
        market_path="option_fundamentals.csv",
        out_path="files/dealer_greeks.json",
    ):
        df_fundamentals = pd.read_csv(f"csv_files/{fundamental_path}")
        df_IV = pd.read_csv(f"csv_files/{IV_path}").replace(regex=r"[\%\,]+", value="")
        df_IV = df_IV.astype({"IV %": float, "Imp Vol": float}, copy=False)
        df_market = pd.read_csv(f"csv_files/{market_path}")
        fundamental_symbols = df_fundamentals["symbol"].unique()
        option_symbols = df_market["symbol"].unique()
        symbols = np.intersect1d(option_symbols, fundamental_symbols)
        num_rows = len(symbols)
        partial = partial_day()
        json_out = {}
        for i, symbol in enumerate(symbols):
            try:
                if df_IV[df_IV["symbol"] == symbol]["Imp Vol"].values[0] < 40:
                    continue
            except:
                print(f"missing symbol {symbol} in finviz")
                continue
            symbol_row = df_market[df_market["symbol"] == symbol]
            fundamental_row = df_fundamentals[df_fundamentals["symbol"] == symbol]
            expirations = symbol_row["tradingDays"].values
            strikes = symbol_row["strikePrice"].unique()
            strikes.sort()
            time_til_exp = np.array([(exp + partial) / 252.75 for exp in expirations])
            time_til_exp = np.clip(time_til_exp, 0, 5)
            call_mask = symbol_row["putCall"] == "CALL"
            put_mask = symbol_row["putCall"] == "PUT"
            if (fundamental_row["Shares Float"].isnull() == False).values[0]:
                shares_float = fundamental_row["Shares Float"]
            else:
                shares_float = fundamental_row["Shares Outstanding"]

            charm = [
                (
                    (
                        return_positioning(1, partial, strike, symbol_row)
                        - return_positioning(0, partial, strike, symbol_row)
                    )
                    / shares_float
                    / 1e6
                ).values[0]
                for strike in strikes
            ]
            gamma = [
                self.get_dealer_gamma(
                    symbol_row, strike, time_til_exp, shares_float, call_mask, put_mask
                ).values[0]
                for strike in strikes
            ]
            vanna = [
                self.get_dealer_vanna(
                    symbol_row, strike, time_til_exp, shares_float
                ).values[0]
                for strike in strikes
            ]
            volga = [
                self.get_dealer_volga(
                    symbol_row, strike, time_til_exp, shares_float
                ).values[0]
                for strike in strikes
            ]
            json_out[symbol] = {
                "charm": charm,
                "gamma": gamma,
                "vanna": vanna,
                "volga": volga,
                "strikes": list(strikes),
            }
            sys.stdout.write("\r")
            sys.stdout.write(
                "[%-60s] %d%%"
                % (
                    "=" * (60 * (i + 1) // num_rows),
                    (100 * (i + 1) // num_rows),
                )
            )
            sys.stdout.write(f",{i} / {num_rows}")
            sys.stdout.flush()
        with open(out_path, "w") as json_file:
            json.dump(json_out, json_file)

    def get_dealer_volga(
        self,
        symbol_row: pd.DataFrame,
        price: np.array,
        time_til_exp: np.array,
        shares_float: pd.Series,
    ) -> np.array:
        d1: np.array = delta1(
            price,
            symbol_row["strikePrice"],
            RISK_FREE_RATE,
            symbol_row["volatility"] / 100,
            time_til_exp,
        )
        d2: np.array = delta2(d1, symbol_row["volatility"] / 100, time_til_exp)
        volgas = calc_volga(d1, d2, time_til_exp, symbol_row["volatility"] / 100)
        denominator = shares_float * 1e6
        volga = np.sum(volgas * symbol_row["openInterest"] * 100) / denominator
        return volga

    def get_dealer_vanna(
        self,
        symbol_row: pd.DataFrame,
        price: np.array,
        time_til_exp: np.array,
        shares_float: pd.Series,
    ) -> np.array:
        d1: np.array = delta1(
            price,
            symbol_row["strikePrice"],
            RISK_FREE_RATE,
            symbol_row["volatility"] / 100,
            time_til_exp,
        )
        vannas = calc_vanna(d1, time_til_exp)
        denominator = shares_float * 1e6
        vanna = np.sum(vannas * symbol_row["openInterest"] * 100) / denominator
        return vanna

    def get_dealer_gamma(
        self,
        symbol_row: pd.DataFrame,
        price: np.array,
        time_til_exp: np.array,
        shares_float: pd.Series,
        call_mask: pd.Series,
        put_mask: pd.Series,
    ) -> np.array:
        d1: np.array = delta1(
            price,
            symbol_row["strikePrice"],
            RISK_FREE_RATE,
            symbol_row["volatility"] / 100,
            time_til_exp,
        )
        call_deltas = norm.cdf(d1[call_mask])
        put_deltas = -norm.cdf(-d1[put_mask])
        deltas = np.concatenate([call_deltas, put_deltas], axis=0)
        denominator = shares_float * 1e6
        gamma = np.sum(deltas * symbol_row["openInterest"] * 100) / denominator
        return gamma

    def charm_hedging(self, infile="option_fundamentals.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        df = df.fillna(0)
        partial = partial_day()
        n = 0
        symbols = df["symbol"].unique()
        json_out: dict = {}
        for i, symbol in enumerate(symbols):
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            json_out[symbol] = {"price": [], "positioning": []}
            # print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            for price in points:
                today_dealer_position = return_positioning(
                    0, partial, price, option_row
                )
                tmrw_dealer_position = return_positioning(1, partial, price, option_row)
                dealer_direction = tmrw_dealer_position - today_dealer_position
                json_out[symbol]["positioning"].append(dealer_direction)
                json_out[symbol]["price"].append(price)
            sys.stdout.write("\r")
            sys.stdout.write(
                "[%-60s] %d%%"
                % (
                    "=" * (60 * (i + 1) // len(symbols)),
                    (100 * (i + 1) // len(symbols)),
                )
            )
            sys.stdout.write(f",{i} / {len(symbols)}")
            sys.stdout.flush()
        with open("files/dealer_charm.json", "w") as json_file:
            json.dump(json_out, json_file)
        print(f"Charm took {(time.time() - start_time)/60} minutes")

    def charm_0(self, symbols: list[str], infile="option_fundamentals.csv") -> dict:
        # print("symbols", symbols)
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        partial = partial_day()
        n = 0
        symbol_positioning = {}
        # symbols = ['SNAP']
        for i, symbol in enumerate(symbols):
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            Y_vals = []
            X_vals = []
            # print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            for price in points:
                today_dealer_position = return_positioning(
                    0, partial, price, option_row
                )
                tmrw_dealer_position = return_positioning(1, partial, price, option_row)
                dealer_direction = tmrw_dealer_position - today_dealer_position
                Y_vals.append(abs(dealer_direction))
                X_vals.append(price)
                # print(f'price {price}, positioning {dealer_position}')
            Y_vals = np.array(Y_vals)
            X_vals = np.array(X_vals)
            min_mask = np.where(Y_vals == np.min(Y_vals))[0]
            symbol_positioning[symbol] = {
                "price": X_vals[min_mask][0],
                "position": Y_vals[min_mask][0],
            }
            sys.stdout.write("\r")
            sys.stdout.write(
                "[%-60s] %d%%"
                % (
                    "=" * (60 * (i + 1) // len(symbols)),
                    (100 * (i + 1) // len(symbols)),
                )
            )
            sys.stdout.write(f",{i} / {len(symbols)}")
            sys.stdout.flush()
        print(f"charm 0 took {(time.time() - start_time)/60} minutes")
        return symbol_positioning

    def add_option_deltas(self, outfile="option_fundamentals.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{outfile}")
        df = df.fillna(0)
        call_mask = df["putCall"] == "CALL"
        put_mask = df["putCall"] == "PUT"
        expirations = df["tradingDays"].values
        partial = partial_day()
        for n in range(-1, 32):
            time_til_exp = np.array(
                [(exp - n + partial) / 252.75 for exp in expirations]
            )
            time_til_exp = np.clip(time_til_exp, 0, 5)
            d1: np.array = delta1(
                df["current_price"],
                df["strikePrice"],
                0.007,
                df["volatility"] / 100,
                time_til_exp,
            )
            call_deltas = norm.cdf(d1[call_mask])
            put_deltas = -norm.cdf(-d1[put_mask])
            deltas = np.empty_like(df["delta"].values)
            deltas[call_mask.values] = call_deltas
            deltas[put_mask.values] = put_deltas
            market_positions = market_position(deltas, df["openInterest"])
            df = df.assign(**{f"day_{n}": pd.Series(deltas).values})
            df = df.assign(
                **{f"dealer_position_day_{n}": pd.Series(market_positions).values}
            )
        df.to_csv(f"csv_files/{outfile}")
        print(f"Option deltas took {(time.time() - start_time)/60} minutes")

    def add_0_positioning(self, csv_path="daily_options.csv") -> dict:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{csv_path}")
        df = df.fillna(0)
        partial = partial_day()
        n = 0
        symbols = df["symbol"].unique()
        min_dealer_positions = {}
        for symbol in symbols:
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            Y_vals = []
            X_vals = []
            print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            prev_dealer_position = return_positioning(n, partial, 0, option_row)
            for price in points:
                dealer_position = return_positioning(n, partial, price, option_row)
                Y_vals.append(dealer_position)
                X_vals.append(price)
                if (
                    prev_dealer_position > 0
                    and (dealer_position == 0 or dealer_position < 0)
                    or prev_dealer_position < 0
                    and (dealer_position == 0 or dealer_position > 0)
                ):
                    # which is closer
                    if abs(prev_dealer_position) < dealer_position:
                        min_dealer_positions[symbol] = {
                            "price": price,
                            "positioning": prev_dealer_position,
                        }
                    else:
                        min_dealer_positions[symbol] = {
                            "price": price,
                            "positioning": dealer_position,
                        }
                    print(f"price {price}, positioning {dealer_position}")
                    break
                prev_dealer_position = dealer_position
        print(f"Option deltas took {(time.time() - start_time)/60} minutes")
        return min_dealer_positions

    def get_market_positioning(
        self,
        symbols=np.array([]),
        optionfile="option_fundamentals.csv",
        outfile="positioning.csv",
    ) -> None:
        start_time = time.time()
        current_date = datetime.datetime.now().date()
        df = pd.read_csv(f"{os.getcwd()}/csv_files/{optionfile}")
        fundamental_df = pd.read_csv(f"{os.getcwd()}/csv_files/stock_fundamentals.csv")
        IV_df = pd.read_csv(f"{os.getcwd()}/csv_files/IV.csv")

        expirations = df["daysToExpiration"].unique()
        expirations.sort()
        overall_positioning: dict[str, Any] = {
            "symbol": [],
            "marketCapFloat": [],
            "IV": [],
            "date": [],
        }
        for i in range(-1, 31):
            overall_positioning[f"scaled_direction_day_{i}"] = []
        for expiration in expirations:
            overall_positioning[f"OI_exp_day_{expiration}"] = []
        if symbols.size == 0:
            option_symbols = df["symbol"].unique()
            fundamental_symbols = fundamental_df["symbol"].unique()
            iv_symbols = IV_df["symbol"].unique()
            intsymbols = np.intersect1d(option_symbols, fundamental_symbols)
            symbols = np.intersect1d(intsymbols, iv_symbols)
        print(f"get_market_positioning num symbols {len(symbols)}")
        for i, symbol in enumerate(symbols):
            try:
                # symbol_data = self.get_fundamentals(symbol)
                # marketCapFloat = symbol_data[symbol]["fundamental"]["marketCapFloat"]
                option_row = df[df["symbol"] == symbol]
                fundamental_row = fundamental_df[fundamental_df["symbol"] == symbol]
                # Get marketcapfloat, or shares outstand if marketcap doesn't exist
                if (fundamental_row["Shares Float"].isnull() == False).values[0]:
                    marketCapFloat = fundamental_row["Shares Float"].values[0]
                else:
                    marketCapFloat = fundamental_row["Shares Outstanding"].values[0]
                print(symbol, marketCapFloat)
                if marketCapFloat > 0:
                    for expiration in expirations:
                        exp_row = option_row[
                            option_row["daysToExpiration"] == expiration
                        ]
                        if exp_row.empty:
                            exp_val = 0
                        else:
                            exp_val = exp_row[
                                "openInterest"
                            ].sum()  # +(exp_row["totalVolume"].sum() * 0.2)
                        overall_positioning[f"OI_exp_day_{expiration}"].append(exp_val)
                    for j in range(-1, 31):
                        dealer_position = option_row[f"dealer_position_day_{j}"].sum()
                        dealer_position2 = option_row[
                            f"dealer_position_day_{j+1}"
                        ].sum()
                        direction_difference = (
                            (dealer_position2 - dealer_position) / marketCapFloat / 1e6
                        )
                        overall_positioning[f"scaled_direction_day_{j}"].append(
                            direction_difference
                        )
                    symbol_iv = IV_df[IV_df["symbol"] == symbol]["Imp Vol"].values[0]
                    iv = symbol_iv if symbol_iv else 0
                    overall_positioning["IV"].append(iv)
                    overall_positioning["symbol"].append(symbol)
                    overall_positioning["marketCapFloat"].append(marketCapFloat)
                    overall_positioning["date"].append(current_date)
            except Exception as e:
                print(symbol, e)
            # sys.stdout.write("\r")
            # sys.stdout.write(
            #     "[%-60s] %d%%"
            #     % (
            #         "=" * (60 * (i + 1) // len(symbols)),
            #         (100 * (i + 1) // len(symbols)),
            #     )
            # )
            # sys.stdout.write(f",{i} / {len(symbols)}")
            # sys.stdout.flush()
        score_df = pd.DataFrame.from_dict(overall_positioning)
        score_df = score_df.sort_values(by=["scaled_direction_day_0"], ascending=False)
        score_df.apply(lambda x: x.replace(",", ""))
        score_df.to_csv(f"csv_files/{outfile}")
        print(f"Dealer positioning takes {(time.time() - start_time)/60} minutes")

    def get_option_fundamentals(
        self, symbol_list: list[str], outfile="option_fundamentals.csv"
    ) -> None:
        function_time = time.time()
        print(f"get_option_fundamentals len symbols {len(symbol_list)}")
        interval = 100
        # For each contract
        positioning_dict: dict[str, Any] = {
            "symbol": [],
            "optionSymbol": [],
            "putCall": [],
            "strikePrice": [],
            "openInterest": [],
            "volatility": [],
            "daysToExpiration": [],
            "tradingDays": [],
            "delta": [],
            "last_price": [],
            "bid": [],
            "ask": [],
            "description": [],
            "inTheMoney": [],
            "gamma": [],
            "weekly": [],
            "current_price": [],
            "totalVolume": [],
        }
        idx = 0
        for i, symbol in enumerate(symbol_list):
            if i % interval == 0:
                bulk_symbol_data = self.api.get_symbols_prices(
                    symbol_list[idx * interval : interval * (idx + 1)]
                )
                idx += 1
            try:
                data = self.api.get_option_chain(symbol)
                symbol_data = bulk_symbol_data[symbol]
                current_price = symbol_data["lastPrice"]
                calls = data["callExpDateMap"]
                puts = data["putExpDateMap"]
                for contractType in [calls, puts]:
                    for contractDates in contractType.values():
                        for strike, value in contractDates.items():
                            try:
                                # if value[0]["daysToExpiration"] < 64:
                                tradingDays: int = int(
                                    trading_days(value[0]["daysToExpiration"])
                                )
                                optionSymbol: str = value[0]["symbol"]
                                delta: float = value[0]["delta"]
                                volatility: float = value[0]["volatility"]
                                strikePrice: float = value[0]["strikePrice"]
                                daysToExpiration: int = value[0]["daysToExpiration"]
                                putCall: str = value[0]["putCall"]
                                openInterest: int = value[0]["openInterest"]
                                bid: float = value[0]["bid"]
                                ask: float = value[0]["ask"]
                                last_price: float = value[0]["last"]
                                gamma: float = value[0]["gamma"]
                                inTheMoney: bool = value[0]["inTheMoney"]
                                description: str = value[0]["description"]
                                totalVolume: int = value[0]["totalVolume"]
                                weekly: bool = (
                                    True if description.find("Weekly") > -1 else False
                                )
                                positioning_dict["symbol"].append(symbol)
                                positioning_dict["optionSymbol"].append(optionSymbol)
                                positioning_dict["delta"].append(delta)
                                positioning_dict["volatility"].append(volatility)
                                positioning_dict["strikePrice"].append(strikePrice)
                                positioning_dict["daysToExpiration"].append(
                                    daysToExpiration
                                )
                                positioning_dict["tradingDays"].append(tradingDays)
                                positioning_dict["putCall"].append(putCall)
                                positioning_dict["openInterest"].append(openInterest)
                                positioning_dict["bid"].append(bid)
                                positioning_dict["ask"].append(ask)
                                positioning_dict["last_price"].append(last_price)
                                positioning_dict["gamma"].append(gamma)
                                positioning_dict["inTheMoney"].append(inTheMoney)
                                positioning_dict["description"].append(description)
                                positioning_dict["weekly"].append(weekly)
                                positioning_dict["current_price"].append(current_price)
                                positioning_dict["totalVolume"].append(totalVolume)
                            except Exception as e:
                                print(f"Exception {symbol},{putCall},{strike}, {e}")
            except Exception as e:
                print(f"{symbol} {e}")
            # sys.stdout.write("\r")
            # sys.stdout.write(
            #     "[%-60s] %d%%"
            #     % (
            #         "=" * (60 * (i + 1) // len(symbol_list)),
            #         (100 * (i + 1) // len(symbol_list)),
            #     )
            # )
            # sys.stdout.write(f",{i} / {len(symbol_list)}")
            # sys.stdout.flush()
        df = pd.DataFrame.from_dict(positioning_dict)
        df.replace("NaN", np.nan, regex=True, inplace=True)
        df.dropna(inplace=True)
        df["delta"] = df["delta"].replace(-999, 0)
        df["volatility"] = df["volatility"].replace(-999, 0)
        df.to_csv(f"csv_files/{outfile}")
        print(f"Option fundamentals took {(time.time() - function_time) / 60} minutes")

    def update_current_prices(self) -> None:
        start_time = time.time()
        df = pd.read_csv("csv_files/option_fundamentals.csv")
        df_IV = pd.read_csv(f"{os.getcwd()}/csv_files/finviz.csv").replace(
            regex=r"[\%\,]+", value=""
        )
        iv_symbols = df_IV["symbol"].values
        for symbol in iv_symbols:
            df.loc[df["symbol"] == symbol, "current_price"] = df_IV.loc[
                df_IV["symbol"] == symbol
            ]["Price"].values[0]
        df.to_csv("csv_files/option_fundamentals.csv")
        print(f"Updating current prices took {(time.time() - start_time)/60} minutes")

    def extract_option_info(self) -> None:
        df = pd.read_csv("csv_files/option_fundamentals.csv")
        option_info: dict[str, Any] = {
            "symbol": [],
            "daysUntilExpiration": [],
            "CallOpenInterest": [],
            "PutOpenInterest": [],
            "avgVolatility": [],
        }
        symbol_list = df["symbol"].unique()
        for symbol in symbol_list:
            symbol_vals = df[df["symbol"] == symbol]
            symbol_calls = symbol_vals[symbol_vals["putCall"] == "CALL"]
            symbol_puts = symbol_vals[symbol_vals["putCall"] == "PUT"]
            call_expirations = symbol_calls["daysToExpiration"].unique()
            for exp in call_expirations:
                if exp < 29:
                    call_OI = symbol_calls[symbol_calls["daysToExpiration"] == exp][
                        "openInterest"
                    ].sum()
                    put_OI = symbol_puts[symbol_puts["daysToExpiration"] == exp][
                        "openInterest"
                    ].sum()
                    avgVolatility = symbol_puts[symbol_puts["daysToExpiration"] == exp][
                        "volatility"
                    ].sum() / len(
                        symbol_puts[symbol_puts["daysToExpiration"] == exp].index
                    )
                    option_info["symbol"].append(symbol)
                    option_info["daysUntilExpiration"].append(exp)
                    option_info["CallOpenInterest"].append(call_OI)
                    option_info["PutOpenInterest"].append(put_OI)
                    option_info["avgVolatility"].append(avgVolatility)
        option_df = pd.DataFrame.from_dict(option_info)
        option_df.to_csv("csv_files/option_info.csv")

    def historical_positioning(self, symbols):
        endDate = int(convert_to_timestamp(datetime.datetime.utcnow()) * 1000)
        # To always get 5 days. Not optimal but W/E
        num_days = 0
        initial_days = 4
        while num_days < 5:
            initial_days += 1
            num_days = trading_days(initial_days)
        startDate = int(
            convert_to_timestamp(
                datetime.datetime.today() - datetime.timedelta(days=initial_days)
            )
            * 1000
        )
        params: dict[str, Any] = {
            "periodType": "year",
            "period": 1,
            "frequencyType": "daily",
            "frequency": 1,
            "startDate": startDate,
            "endDate": endDate,
        }
        for symbol in symbols:
            print(symbol)
            if not os.path.exists(f"historical/{symbol}.csv"):
                self.historical_candles([symbol], params, outdir="historical")
        if not os.path.exists("historical/SPY.csv"):
            self.historical_candles(["SPY"], params, outdir="historical")
