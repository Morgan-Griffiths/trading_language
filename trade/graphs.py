import pandas as pd
import numpy as np
import datetime
import json
import time
import sys
from trade.plot import plot_data
from trade.utils import (
    calc_vanna,
    calc_volga,
    delta1,
    delta2,
    market_position,
    partial_day,
    return_positioning,
)


class Graph(object):
    def __init__(self):
        ...

    def graph_positioning(self, infile="option_fundamentals.csv") -> None:
        start_time = time.time()
        df_fundamentals = pd.read_csv("csv_files/stock_fundamentals.csv")
        df = pd.read_csv(f"csv_files/{infile}")
        df = df.fillna(0)
        partial = partial_day()
        n = 0
        symbols = df["symbol"].unique()
        symbols = ["AAL"]
        for symbol in symbols:
            fundamental_row = df_fundamentals[df_fundamentals["symbol"] == symbol]
            if (fundamental_row["Shares Float"].isnull() == False).values[0]:
                marketCapFloat = fundamental_row["Shares Float"].values[0]
            else:
                marketCapFloat = fundamental_row["Shares Outstanding"].values[0]
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            dealer_current_position = return_positioning(
                0, partial, current_price, option_row
            )
            Y_vals = []
            X_vals = []
            print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            for price in points:
                today_dealer_position = return_positioning(
                    0, partial, price, option_row
                )
                dealer_diff = (today_dealer_position - dealer_current_position) / (
                    price - current_price
                )
                Y_vals.append(dealer_diff)
                X_vals.append(price)
                # print(f'price {price}, positioning {dealer_position}')
            plot_data(
                f"{symbol}_positioning",
                X_vals,
                Y_vals,
                xlabel="Price",
                ylabel="Positioning",
            )

    def graph_3dcharm_positioning(self, infile="option_fundamentals.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        df = df.fillna(0)
        partial = partial_day()
        symbols = df["symbol"].unique()
        symbols = ["SOS"]
        for symbol in symbols:
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            price_dist = {}
            print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            for price in points:
                Y_vals = []
                X_vals = []
                for n in range(0, 10):
                    today_dealer_position = return_positioning(
                        n, partial, price, option_row
                    )
                    tmrw_dealer_position = return_positioning(
                        n + 1, partial, price, option_row
                    )
                    dealer_direction = tmrw_dealer_position - today_dealer_position
                    Y_vals.append(dealer_direction)
                    X_vals.append(n)
                    # print(f'price {price}, positioning {dealer_position}')
                price_dist[price] = {"X": X_vals, "Y": Y_vals}
            with open(f"3d_graphs/{symbol}_charm.json", "w") as json_file:
                json.dump(price_dist, json_file)
            # plot_data(f'{symbol}_positioning',X_vals,Y_vals)
        print(f"graphing took {(time.time() - start_time)/60} minutes")

    def graph_charm_positioning(self, infile="option_fundamentals.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        df = df.fillna(0)
        partial = partial_day()
        n = 0
        symbols = df["symbol"].unique()
        symbols = ["AAL"]
        for symbol in symbols:
            option_row = df[df["symbol"] == symbol]
            current_price = option_row["current_price"].values[0]
            num_digits = len(str(int(current_price)))
            Y_vals = []
            X_vals = []
            print(symbol)
            points = np.linspace(current_price / 3, current_price * 3, num=200)
            for price in points:
                today_dealer_position = return_positioning(
                    0, partial, price, option_row
                )
                tmrw_dealer_position = return_positioning(1, partial, price, option_row)
                dealer_direction = tmrw_dealer_position - today_dealer_position
                Y_vals.append(dealer_direction)
                X_vals.append(price)
                # print(f'price {price}, positioning {dealer_position}')
            plot_data(
                f"{symbol}_positioning",
                X_vals,
                Y_vals,
                xlabel="Position",
                ylabel="Price",
            )
        print(f"graphing took {(time.time() - start_time)/60} minutes")

    def graph_vanna(self, infile="greeks.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        symbols = df["symbol"].unique()
        for i, symbol in enumerate(symbols):
            option_row = df[df["symbol"] == symbol]
            X_vals = option_row["strike"].values
            Y_vals = option_row["vanna"].values
            plot_data(
                f"{symbol}_vanna", X_vals, Y_vals, xlabel="Strike", ylabel="Vanna"
            )
            if i == 25:
                break
        print(f"graphing took {(time.time() - start_time)/60} minutes")

    def graph_volga(self, infile="greeks.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        symbols = df["symbol"].unique()
        for i, symbol in enumerate(symbols):
            option_row = df[df["symbol"] == symbol]
            X_vals = option_row["strike"].values
            Y_vals = option_row["volga"].values
            plot_data(
                f"{symbol}_volga", X_vals, Y_vals, xlabel="Strike", ylabel="Volga"
            )
            if i == 25:
                break
        print(f"graphing took {(time.time() - start_time)/60} minutes")

    def graph_gamma(self, infile="greeks.csv") -> None:
        start_time = time.time()
        df = pd.read_csv(f"csv_files/{infile}")
        symbols = df["symbol"].unique()
        for i, symbol in enumerate(symbols):
            option_row = df[df["symbol"] == symbol]
            X_vals = option_row["strike"].values
            Y_vals = option_row["gamma"].values
            plot_data(
                f"{symbol}_gamma", X_vals, Y_vals, xlabel="Strike", ylabel="Gamma"
            )
            if i == 25:
                break
        print(f"graphing took {(time.time() - start_time)/60} minutes")
