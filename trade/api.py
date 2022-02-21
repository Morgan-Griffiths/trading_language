import operator
from typing import Any
import json
import datetime
import math
from requests_oauthlib import OAuth2Session
import pandas as pd
import time
import sys
import numpy as np
import os
from trade.redis_interface import RedisInterface
from src.infrastructure.database_layer import DataBase
from trade.utils import (
    trading_days,
    n_day_delta,
    extract_date_from_description,
    convert_to_timestamp,
    convert_from_timestamp,
    CAL,
    get_ATM_volatility,
    third_friday,
    save_pickle,
    load_pickle,
)
import logging

logging.basicConfig(level=logging.INFO, filename="logs/api_activity.log")
logger = logging.getLogger("API")

TIME_BUFFER = 0.7


class API(object):
    def __init__(self, params: dict[str, Any]) -> None:
        self.redis = RedisInterface(expiration=params["expiration"])
        self.API_KEY = params["API_KEY"]
        self.SECRET_PATH = params["SECRET_PATH"]
        self.ACCOUNT_ID = params["ACCOUNT_ID"]
        self.CALLBACK_URI = params["CALLBACK_URI"]
        self.TOKEN_NAME = params["TOKEN_NAME"]
        self.auth = params["AUTH"]
        self.client = params["client"]
        self.previous_query = time.time() - 100
        self.db = DataBase(params["db"])

    def _get_data(self, url, params: dict[str, Any] = {}):
        time_elapsed = time.time() - self.previous_query
        if time_elapsed < TIME_BUFFER:
            time.sleep(TIME_BUFFER - time_elapsed)
        self.previous_query = time.time()
        params["apikey"] = self.API_KEY
        page = self.client.get(url=url, params=params)
        new_content: Any = json.loads(page.content)
        return new_content

    def get_data(self, url: str, params: dict[str, Any] = {}) -> Any:
        key = "api." + str(params) + url
        content = self.redis.get_value(key)
        if content is None:
            new_content = self._get_data(url, params)
            self.redis.set_value(key, json.dumps(new_content))
            return new_content
        else:
            return json.loads(content.decode())

    # def get_batch(self, url: str, params: dict[str, Any] = {}):
    #     unknown = []
    #     for value in params.values():
    #         content = self.redis.get_value(key)
    #     new_content = self._get_data()
    #     # store new_content

    def post_data(self, url: str, params: dict[str, Any] = {}) -> int:
        headers = {"Content-Type": "application/json", "apikey": self.API_KEY}
        resp = self.client.post(url, data=json.dumps(params), headers=headers)
        try:
            content = json.loads(resp.content.decode("utf8").replace("'", '"'))
            logging.info(content, type(content))
            if content["error"]:
                logging.info(f"Error: {content['error']}")
        except Exception as e:
            logging.info(f"Error {e}")
        orderId = int(resp.headers["location"].split("/")[-1])
        return orderId

    def put_data(self, url: str, params: dict[str, Any] = {}) -> dict[str, Any]:
        params["apikey"] = self.API_KEY
        page = self.client.post(url=url, params=params)
        content: dict[str, Any] = json.loads(page.content)
        return content

    def delete_data(self, url: str, params: dict[str, Any] = {}) -> dict[str, Any]:
        params["apikey"] = self.API_KEY
        page = self.client.delete(url=url, params=params)
        content: dict[str, Any] = page.headers
        return content

    def get_balance(self) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/accounts/{account}"
        endpoint = url.format(account=self.ACCOUNT_ID)
        content: dict[str, Any] = self.get_data(endpoint, {"fields": "positions"})
        buyingPower = content["securitiesAccount"]["projectedBalances"][
            "availableFunds"
        ]
        cashBalance = content["securitiesAccount"]["currentBalances"]["cashBalance"]
        logging.info("buyingPower", buyingPower)
        logging.info("cashBalance", cashBalance)
        return content

    def get_buying_power(self) -> float:
        url = "https://api.tdameritrade.com/v1/accounts/{account}"
        endpoint = url.format(account=self.ACCOUNT_ID)
        content: dict[str, Any] = self.get_data(endpoint, {"fields": "positions"})
        buyingPower = content["securitiesAccount"]["projectedBalances"][
            "availableFunds"
        ]
        return buyingPower

    def get_bankroll(self) -> float:
        url = "https://api.tdameritrade.com/v1/accounts/{account}"
        endpoint = url.format(account=self.ACCOUNT_ID)
        content: dict[str, Any] = self.get_data(endpoint, {"fields": "positions"})
        bankroll = content["securitiesAccount"]["currentBalances"]["availableFunds"]
        return bankroll

    def get_positions(self) -> list[Any]:
        url = "https://api.tdameritrade.com/v1/accounts/{account}"
        endpoint = url.format(account=self.ACCOUNT_ID)
        content: dict[str, Any] = self.get_data(endpoint, {"fields": "positions"})
        try:
            positions: list[Any] = content["securitiesAccount"]["positions"]
        except KeyError:
            positions = []
            logging.info("No current positions")
        return positions

    def get_option_chain(self, stock_ticker: str) -> dict[str, Any]:
        base_url = (
            "https://api.tdameritrade.com/v1/marketdata/chains?&symbol={stock_ticker}"
        )
        endpoint = base_url.format(stock_ticker=stock_ticker)
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_option_strikes(
        self, stock_ticker: str, contractType: str, expDate: str
    ) -> dict[str, Any]:
        """stock_ticker:'AAPL',contractType:'PUT',expDate : '2021-1-8'"""
        base_url = "https://api.tdameritrade.com/v1/marketdata/chains?&symbol={stock_ticker}&contractType={contractType}&fromDate={date}&toDate={date}"
        endpoint = base_url.format(
            stock_ticker=stock_ticker, contractType=contractType, date=expDate
        )
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_option(
        self, stock_ticker: str, contractType: str, expDate: str, strike: int
    ) -> dict[str, Any]:
        """stock_ticker:'AAPL',contractType:'PUT',expDate : '2021-1-8',strike:200"""
        base_url = "https://api.tdameritrade.com/v1/marketdata/chains?&symbol={stock_ticker}&contractType={contract_type}&strike={strike}&fromDate={date}&toDate={date}"
        endpoint = base_url.format(
            stock_ticker=stock_ticker,
            contract_type=contractType,
            strike=strike,
            date=expDate,
        )
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_symbols_prices(self, stock_tickers: list) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/marketdata/quotes?"
        limit = 500
        content: dict = {}
        if len(stock_tickers) > limit:
            start: int = 0
            end: int = min(start + limit, len(stock_tickers))
            while start != len(stock_tickers):
                endpoint = url.format(stock_tickers=stock_tickers[start:end])
                new_content: dict[str, Any] = self.get_data(
                    endpoint, params={"symbol": stock_tickers[start:end]}
                )
                logging.info(new_content)
                content |= new_content
                start = end
                end = min(start + limit, len(stock_tickers))
                time.sleep(TIME_BUFFER)
        else:
            endpoint = url.format(stock_tickers=stock_tickers)
            content: dict[str, Any] = self.get_data(
                endpoint, params={"symbol": stock_tickers}
            )
        return content

    def get_symbol_price(self, stock_ticker: str) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?"
        endpoint = url.format(stock_ticker=stock_ticker)
        content: dict[str, Any] = self.get_data(endpoint)
        return content[stock_ticker]

    def get_historical_price(
        self, ticker: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if "startDate" in params:
            url = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?periodType={periodType}&frequencyType={frequencyType}&frequency={frequency}&endDate={endDate}&startDate={startDate}"
            endpoint = url.format(
                stock_ticker=ticker,
                periodType=params["periodType"],
                endDate=params["endDate"],
                startDate=params["startDate"],
                frequencyType=params["frequencyType"],
                frequency=params["frequency"],
            )
        else:
            url = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?periodType={periodType}&period={period}&frequencyType={frequencyType}&frequency={frequency}"
            endpoint = url.format(
                stock_ticker=ticker,
                periodType=params["periodType"],
                period=params["period"],
                frequencyType=params["frequencyType"],
                frequency=params["frequency"],
            )
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_weekly_data(self, stock_ticker: str) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?periodType={periodType}&period={period}&frequencyType={frequencyType}&frequency={frequency}"
        endpoint = url.format(
            stock_ticker=stock_ticker,
            periodType="year",
            period=1,
            frequencyType="weekly",
            frequency=1,
        )
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_instruments(self, cusip: str) -> dict[str, Any]:
        base_url = "https://api.tdameritrade.com/v1/instruments/{cusip}"
        endpoint = base_url.format(cusip=cusip)
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_fundamentals(self, stock_ticker: str) -> dict[str, Any]:
        base_url = "https://api.tdameritrade.com/v1/instruments?&symbol={stock_ticker}&projection={projection}"
        endpoint = base_url.format(stock_ticker=stock_ticker, projection="Fundamental")
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def get_top_movers(self, index: int, direction: str, change: str) -> dict[str, Any]:
        """direction:(up,down),change:(percent)"""
        url = "https://api.tdameritrade.com/v1/marketdata/{index}/movers"
        endpoint = url.format(index=f"${index}")
        content: dict[str, Any] = self.get_data(
            endpoint, {"direction": direction, "change": change}
        )
        return content

    def cancel_order(self, orderId: int) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/accounts/{accountId}/orders/{orderId}"
        endpoint = url.format(orderId=orderId, accountId=self.ACCOUNT_ID)
        content = self.delete_data(endpoint)
        return content

    def get_orders(self, params: dict[str, Any] = {}) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/orders"
        params["accountId"] = self.ACCOUNT_ID
        content: dict[str, Any] = self.get_data(url, params)
        return content

    def get_order(self, orderId: int) -> dict[str, Any]:
        url = "https://api.tdameritrade.com/v1/accounts/{accountId}/orders/{orderId}"
        endpoint = url.format(orderId=orderId, accountId=self.ACCOUNT_ID)
        content: dict[str, Any] = self.get_data(endpoint)
        return content

    def place_order(self, market_order: dict[str, Any]) -> Any:
        url = "https://api.tdameritrade.com/v1/accounts/{accountId}/orders"
        endpoint = url.format(accountId=self.ACCOUNT_ID)
        orderId = self.post_data(url=endpoint, params=market_order)
        return orderId

    def save_order(self, buy_order: dict[str, Any]) -> Any:
        url = "https://api.tdameritrade.com/v1/accounts/{accountId}/savedorders"
        endpoint = url.format(accountId=self.ACCOUNT_ID)
        content = self.post_data(url=endpoint, params=buy_order)
        return content

    def get_price_points(self, symbol: str) -> tuple[float, float, float, float, float]:
        price_data = self.get_symbol_price(symbol)
        bidPrice = price_data["bidPrice"]
        askPrice = price_data["askPrice"]
        lastPrice = price_data["lastPrice"]
        margin = askPrice - bidPrice
        midPrice = round((bidPrice + askPrice) / 2, 2)
        if bidPrice > 0:
            spread = margin / bidPrice
        else:
            spread = margin / lastPrice
        return bidPrice, askPrice, midPrice, margin, spread

    def get_last_price(self, symbol: str) -> float:
        price_data = self.get_symbol_price(symbol)
        lastPrice = price_data["lastPrice"]
        return lastPrice

    def price_asset(self, symbol: str, direction: str) -> float:
        bidPrice, askPrice, midpoint, margin, spread = self.get_price_points(symbol)
        if direction == "BUY":
            if spread < 0.1:
                price = max(midpoint, 0.01)
            else:
                price = bidPrice + 0.02
        elif direction == "SELL":
            if spread < 0.1:
                price = max(askPrice - 0.01, 0.04)
            else:
                price = askPrice - 0.02
        else:
            raise ValueError(f"Direction not understood {direction}")
        price = round(price, 2) if price > 1 else round(price, 4)
        return price

    def get_specific_option(
        self,
        stock_ticker: str,
        contractType: str,
        expDate: datetime.date,
        strike: int,
        option_exp_delta,
    ) -> dict[str, Any]:
        option_data = self.get_option(stock_ticker, contractType, str(expDate), strike)
        option_list = (
            option_data["callExpDateMap"]
            if contractType == "CALL"
            else option_data["putExpDateMap"]
        )
        option_date_key = str(expDate) + f":{option_exp_delta.days}"
        error = True
        amount = 1
        index = 0
        while error:
            try:
                option = option_list[option_date_key][str(float(strike))]
                error = False
            except:
                strike = strike - amount if index % 2 == 0 else strike + amount
                amount += 1
                index += 1
                if index > 500:
                    break
        return option

    def get_option_stats(
        self, stock_ticker: str, contractType: str, expDate: datetime.date, strike: int
    ) -> dict[str, Any]:
        """expDate: date object"""
        option_data = self.get_option(stock_ticker, contractType, str(expDate), strike)
        delta = expDate - datetime.date.today()
        option_exp_delta = delta.days
        option_date_key = str(expDate) + f":{option_exp_delta}"
        option_list = option_data["callExpDateMap"][option_date_key][str(float(strike))]
        OI = option_list[0]["openInterest"]
        IV = option_list[0]["volatility"]
        delta = option_list[0]["delta"]
        gamma = option_list[0]["gamma"]
        option_ask = option_list[0]["ask"]
        option_bid = option_list[0]["bid"]
        option_margin = option_ask - option_bid
        option_midPrice = round((option_ask + option_bid) / 2, 2)
        option_id = option_list[0]["symbol"]
        last_price = option_list[0]["last_price"]
        data = {
            "IV": IV,
            "OI": OI,
            "delta": delta,
            "gamma": gamma,
            "option_ask": option_ask,
            "option_bid": option_bid,
            "option_margin": option_margin,
            "option_midPrice": option_midPrice,
            "option_id": option_id,
            "last_price": last_price,
        }
        return data

    def get_option_price_points(
        self, stock_ticker: str, contractType: str, expDate: datetime.date, strike: int
    ) -> tuple[float, float, float, float, float]:
        """expDate: date object"""
        option_data = self.get_option(stock_ticker, contractType, str(expDate), strike)
        delta = expDate - datetime.date.today()
        option_exp_delta = delta.days
        option_date_key = str(expDate) + f":{option_exp_delta}"
        option_list = option_data["callExpDateMap"][option_date_key][str(float(strike))]
        option_ask = option_list[0]["ask"]
        option_bid = option_list[0]["bid"]
        option_margin = option_ask - option_bid
        option_midPrice = round((option_ask + option_bid) / 2, 2)
        option_id = option_list[0]["symbol"]
        return option_bid, option_ask, option_midPrice, option_margin, option_id

    def get_option_calls(self, symbol_list: list[str]) -> list[str]:
        possible_options = []
        for symbol in symbol_list:
            option_data = self.get_option_chain(symbol)
            calls = option_data["callExpDateMap"]
            for contractDates in calls.values():
                for strike, value in contractDates.items():
                    try:
                        contract: str = value[0]["symbol"]
                        delta: float = value[0]["delta"]
                        tradingDays: int = int(
                            trading_days(value[0]["daysToExpiration"])
                        )
                        if tradingDays < 14 and delta > 0.1:
                            possible_options.append(contract)
                    except:
                        pass
        return possible_options

    def return_option_volume(
        self, symbol: str, option_data: dict[str, Any]
    ) -> tuple[int, int]:
        totals: dict[str, Any] = {"CALL": [], "PUT": []}
        try:
            calls = option_data["callExpDateMap"]
            puts = option_data["putExpDateMap"]
            for contractType in [calls, puts]:
                for contractDates in contractType.values():
                    for strike, value in contractDates.items():
                        volume = value[0]["totalVolume"]
                        putCall = value[0]["putCall"]
                        totals[putCall].append(volume)
        except Exception as e:
            logging.info("Error")
        return sum(totals["CALL"]), sum(totals["PUT"])

    def historical_candles(
        self, symbol_list: list[str], params: dict[str, Any], outdir="candles"
    ) -> None:
        start_time = time.time()
        logging.info(params)
        for i, symbol in enumerate(symbol_list):
            logging.info(symbol)
            symbol_duration = time.time()
            try:
                hist_data = self.get_historical_price(symbol, params)
                pd.DataFrame(hist_data["candles"]).to_csv(f"{outdir}/{symbol}.csv")
            except Exception as e:
                try:
                    logging.info(hist_data["error"])
                    time.sleep(5)
                except KeyError:
                    logging.info(symbol, e)
            time_spent = time.time() - symbol_duration
            if time_spent < TIME_BUFFER * 1.5:
                time.sleep(TIME_BUFFER * 1.5 - time_spent)
            sys.stdout.write("\r")
            sys.stdout.write(
                "[%-60s] %d%%"
                % (
                    "=" * (60 * (i + 1) // len(symbol_list)),
                    (100 * (i + 1) // len(symbol_list)),
                )
            )
            sys.stdout.write(f",{i} / {len(symbol_list)}")
            sys.stdout.flush()
        logging.info(
            f"Historical download took {(start_time-time.time()) / 60} minutes"
        )

    def buy_equity(self, name: str, amount: int) -> None:
        assetParams: dict[str, Any] = {
            "symbol": name,
            "quantity": amount,
            "tradeType": "BUY",
        }
        trade_params = self.get_market_order(assetParams)
        logging.info(trade_params)

    def close_option(self, contract: str) -> None:
        positions = self.get_positions()
        logging.info(contract)
        for position in positions:
            # logging.info(position)
            instrument = position["instrument"]
            assetType = instrument["assetType"]
            logging.info(instrument["symbol"])
            logging.info(instrument["symbol"] == contract)
            if assetType == "OPTION" and instrument["symbol"] == contract:
                quantity = (
                    position["shortQuantity"]
                    if position["shortQuantity"] > 0
                    else position["longQuantity"]
                )
                symbol = instrument["symbol"]
                marketValue = position["marketValue"]
                direction = "BUY" if position["shortQuantity"] > 0 else "SELL"
                try:
                    price = self.price_asset(symbol, direction)
                    assetParams: dict[str, Any] = {
                        "symbol": symbol,
                        "quantity": quantity,
                        "price": price,
                    }
                    underlying = instrument["underlyingSymbol"]
                    # if underlying == "SOS":
                    today = datetime.date.today()
                    num_days_til_exp = (
                        extract_date_from_description(instrument["description"]) - today
                    ).days
                    logging.info("num_days_til_exp", num_days_til_exp)
                    # if num_days_til_exp < 30 and price > 0.05:
                    tradeType = (
                        "BUY_TO_CLOSE"
                        if position["shortQuantity"] > 0
                        else "SELL_TO_CLOSE"
                    )
                    assetParams["tradeType"] = tradeType
                    trade_params = self.option_order(assetParams)
                    logging.info(trade_params)
                    orderId = self.place_order(trade_params)
                    logging.info("orderId", orderId)
                except Exception as e:
                    logging.info(e)

    def get_ITM_option(
        self, symbol: str, maxDays: int, optionType: str, distance: float
    ) -> dict:
        price = self.get_last_price(symbol)
        today = datetime.datetime.today()
        data = self.get_option_chain(symbol)
        puts = data["putExpDateMap"] if optionType == "PUT" else data["callExpDateMap"]
        keys = list(puts.keys())
        days_out = [
            (datetime.datetime.strptime(k.split(":")[0], "%Y-%m-%d") - today).days
            for k in keys
        ]
        last_diff = -np.inf
        for i, day in enumerate(days_out):
            diff = day - maxDays
            if diff == 0:
                target_index = i
                break
            elif diff > 0 and last_diff < 0:
                if abs(days_out[i - 1]) < abs(days_out[i]):
                    target_index = i - 1
                else:
                    target_index = i
                break
        target_day = keys[target_index]
        logging.info(f"target_index {target_index}, target_day {target_day}")
        logging.info(days_out)
        last_diff = -np.inf
        all_contracts = list(puts[target_day].values())
        if optionType == "PUT":
            operand = operator.gt
            diff_comparison = operator.lt
            increment = 1
        elif optionType == "CALL":
            operand = operator.lt
            diff_comparison = operator.gt
            increment = -1
        for i, contracts in enumerate(all_contracts):
            strike_price = contracts[0]["strikePrice"]
            logging.info("distance", round(price - strike_price, 0))
            logging.info("distance", round(price - strike_price, 0) == distance)
            if round(price, 0) - strike_price == distance:
                target_contract = i
                break
            # elif operand(price - strike_price, 0) and operand(last_diff, 0):
            #     logging.info("elif")
            #     if operand(abs(last_diff), price - strike_price):
            #         target_contract = i - 1
            #     else:
            #         target_contract = i
            #     break
            else:
                last_diff = price - strike_price
            # for strike, value in contracts.items():
            # get strike ATM
        target_option = all_contracts[target_contract][0]
        return target_option

    def get_ATM_option(
        self, symbol: str, maxDays: int, optionType: str, today: datetime.datetime
    ) -> dict:
        assert isinstance(today, datetime.datetime)
        price = self.get_last_price(symbol)
        data = self.get_option_chain(symbol)
        puts = data["putExpDateMap"] if optionType == "PUT" else data["callExpDateMap"]
        keys = list(puts.keys())
        days_out = [
            (datetime.datetime.strptime(k.split(":")[0], "%Y-%m-%d") - today).days
            for k in keys
        ]
        last_diff = -np.inf
        for i, day in enumerate(days_out):
            diff = day - maxDays
            if diff == 0:
                target_index = i
                break
            elif diff > 0 and last_diff < 0:
                if abs(days_out[i - 1]) < abs(days_out[i]):
                    target_index = i - 1
                else:
                    target_index = i
                break
        target_day = keys[target_index]
        last_diff = -np.inf
        all_contracts = list(puts[target_day].values())
        for i, contracts in enumerate(all_contracts):
            strike_price = contracts[0]["strikePrice"]
            if price - strike_price == 0:
                target_contract = i
            elif price - strike_price < 0 and last_diff > 0:
                if abs(last_diff) < price - strike_price:
                    target_contract = i - 1
                else:
                    target_contract = i
                break
            else:
                last_diff = price - strike_price
            # for strike, value in contracts.items():
            # get strike ATM
        target_option = all_contracts[target_contract][0]
        return target_option

    def sell_contract(self, symbol: str, maxDays: int, distance: float) -> None:
        target_option = self.get_ITM_option(symbol, maxDays, "PUT", distance)
        logging.info("target_option", target_option)
        midpoint = target_option["ask"] - round(
            ((target_option["ask"] - target_option["bid"]) / 3),
            2,
        )
        num_contracts = math.floor(13000 / (midpoint * 100))
        option_params = {
            "price": round(midpoint, 2),
            "quantity": min(num_contracts, 12),
            "symbol": target_option["symbol"],
            "tradeType": "SELL_TO_OPEN",
        }
        td_order = self.option_order(option_params)
        logging.info("td_order", td_order)
        logging.info(
            f'expected cost {option_params["quantity"] * option_params["price"] * 100}'
        )
        orderId = self.place_order(td_order)
        logging.info("orderId", orderId)

    def sell_option(self, symbol: str, maxDays: int) -> None:
        target_option = self.get_ATM_option(
            symbol, maxDays, "PUT", datetime.datetime.today()
        )
        logging.info("target_option", target_option)
        midpoint = target_option["ask"] - round(
            ((target_option["ask"] - target_option["bid"]) / 3),
            2,
        )
        num_contracts = math.floor(13000 / (midpoint * 100))
        option_params = {
            "price": round(midpoint, 2),
            "quantity": min(num_contracts, 3),
            "symbol": target_option["symbol"],
            "tradeType": "SELL_TO_OPEN",
        }
        td_order = self.option_order(option_params)
        logging.info("td_order", td_order)
        logging.info(
            f'expected cost {option_params["quantity"] * option_params["price"] * 100}'
        )
        orderId = self.place_order(td_order)
        logging.info("orderId", orderId)

    def buy_option(self, symbol: str, maxDays: int) -> None:
        target_option = self.get_ATM_option(
            symbol, maxDays, "PUT", datetime.datetime.now()
        )
        logging.info("target_option", target_option)
        midpoint = target_option["ask"] - round(
            ((target_option["ask"] - target_option["bid"]) / 3),
            2,
        )
        num_contracts = math.floor(3000 / (midpoint * 100))
        option_params = {
            "price": round(midpoint, 2),
            "quantity": min(num_contracts, 5),
            "symbol": target_option["symbol"],
            "tradeType": "BUY_TO_OPEN",
            "tradeDirection": "long",
            "strategy": "custom",
        }
        td_order = self.option_order(option_params)
        logging.info("td_order", td_order)
        orderId = self.place_order(td_order)
        logging.info("orderId", orderId)

    def backtest(self) -> None:
        backtest_df = pd.read_csv("backtest/high.csv")
        dates = backtest_df["date"].unique()
        for d in dates:
            rows = backtest_df[backtest_df["date"] == d]
            symbols = rows["ticker"].unique()
            full_date = d + "/2021"
            start_date = datetime.datetime.strptime(full_date, "%m/%d/%Y")
            startDate = int(convert_to_timestamp(start_date) * 1000)
            logging.info("start_date", start_date.date())
            num_days = 0
            initial_days = 2
            while num_days < 3:
                initial_days += 1
                num_days = trading_days(initial_days, start=start_date.date())
            endDate = int(
                convert_to_timestamp(start_date + datetime.timedelta(days=initial_days))
                * 1000
            )
            params: dict[str, Any] = {
                "periodType": "day",
                # "period": 3,
                "frequencyType": "minute",
                "frequency": 30,
                "startDate": startDate,
                "endDate": endDate,
            }
            os.mkdir(f"backtest_high/{start_date.date()}")
            self.historical_candles(
                symbols, params, outdir=f"backtest_high/{start_date.date()}"
            )

    def market_features(self) -> list[Any]:
        """Returns 4 attributes: VIX, % of SPY 52wkHigh, distance to opex"""
        VIX = self.get_symbol_price("$VIX.X")
        SPY = self.get_symbol_price("SPY")
        vix_price = VIX["lastPrice"]
        high = SPY["52WkHigh"]
        percent_of_high = (high - SPY["lastPrice"]) / high
        # low = SPY['52WkLow']
        spy_df = pd.read_csv("candles/SPY.csv")
        spy_20_day_mean = spy_df["close"].mean()
        percent_moving_avg = (spy_20_day_mean - SPY["lastPrice"]) / spy_20_day_mean
        opex = third_friday()
        current_day = datetime.datetime.now().date()
        distance_to_opex = (opex - current_day).days
        logging.info("percent_moving_avg", percent_moving_avg)
        logging.info("percent_of_high", percent_of_high)
        logging.info(f"opex {opex},distance_to_opex {distance_to_opex}")
        return [percent_of_high, spy_20_day_mean, distance_to_opex, vix_price]

    def stock_features(self, symbol):
        """IV
        options bool
        market cap
        weekly volume/share float
        hourly volume/share float
        daily volume/share float
        sector in play?
        country in play?
        overnight move"""
        df_IV = pd.read_csv("csv_files/IV.csv").replace(regex=r"[\%\,]+", value="")
        try:
            iv = df_IV[df_IV["symbol"] == symbol]["Imp Vol"]
            has_options = True
        except:
            iv = None
            has_options = False
        symbol_price_data = self.get_symbol_price(symbol)
        symbol_fund_data = self.get_fundamentals(symbol)[symbol]
        logging.info(symbol_price_data)
        sharesOutstanding = symbol_fund_data["fundamental"]["sharesOutstanding"]
        marketCapFloat = symbol_fund_data["fundamental"]["marketCapFloat"]
        marketCap = symbol_fund_data["fundamental"]["marketCap"]
        # overnight move

        daily_volume = symbol_price_data["totalVolume"]
        # in_index =
        # earnings_distance
        # IPO distance
        logging.info(symbol_price_data)

    def spy_20day(self) -> None:
        num_days = 24
        end_datetime = datetime.datetime.utcnow()
        if datetime.datetime.now().hour > 13 and datetime.datetime.now().hour <= 24:
            # same day
            previous_close_date = datetime.date.today()
            previous_close_datetime = datetime.datetime.now()
        else:
            # yesterday
            previous_close_date = datetime.date.today() - datetime.timedelta(days=1)
            previous_close_datetime = datetime.datetime.now() - datetime.timedelta(
                hours=datetime.datetime.now().hour + 1
            )
            end_datetime -= datetime.timedelta(hours=end_datetime.hour + 10)
        start = previous_close_date - datetime.timedelta(days=num_days)
        tradingDays = 0
        while tradingDays < 19:
            tradingDays = trading_days(num_days, start)
            num_days += 1
            start = previous_close_date - datetime.timedelta(days=num_days)
        startDate = int(
            convert_to_timestamp(
                previous_close_datetime - datetime.timedelta(days=int(num_days))
            )
            * 1000
        )
        endDate = int(convert_to_timestamp(end_datetime) * 1000)
        params: dict[str, Any] = {
            "periodType": "year",
            "period": 1,
            "frequencyType": "daily",
            "frequency": 1,
            "startDate": startDate,
            "endDate": endDate,
        }
        self.historical_candles(np.array(["SPY"]), params)

    # 1 standard deviation =
    # stock price * volatility * square root of days to expiration/365.

    def get_OOTM_contracts(
        self, expiration, symbols: list[str], putCall: str
    ) -> pd.DataFrame:
        today = datetime.date.today()
        potential_options: dict[str, Any] = {
            "symbol": [],
            "contract": [],
            "putCall": [],
            "current_price": [],
            "strike": [],
            "bid": [],
            "ask": [],
            "last_price": [],
            "totalVolume": [],
            "daysToExpiration": [],
            "inTheMoney": [],
            "volatility": [],
            "delta": [],
            "gamma": [],
            "vega": [],
            "rho": [],
            "openInterest": [],
        }
        for symbol in symbols:
            option_data = self.get_option_chain(symbol)
            symbol_data = self.get_symbol_price(symbol)
            current_price = symbol_data["lastPrice"]
            price_band = current_price * 0.1
            options = (
                option_data["putExpDateMap"]
                if putCall == "PUT"
                else option_data["callExpDateMap"]
            )
            for contracts in options.values():
                for strike, value in contracts.items():
                    expDate = extract_date_from_description(value[0]["description"])
                    date_diff = (expDate - today).days
                    bid = value[0]["bid"]
                    ask = value[0]["ask"]
                    last = value[0]["last"]
                    try:
                        spread = (ask - bid) / bid
                        if (
                            putCall == "PUT"
                            and (
                                date_diff == expiration
                                and value[0]["delta"] > -0.25
                                and value[0]["delta"] < -0.04
                                and spread < 0.1
                            )
                            or putCall == "CALL"
                            and (
                                date_diff == expiration
                                and value[0]["delta"] < 0.25
                                and value[0]["delta"] > 0.04
                                and spread < 0.1
                            )
                        ):
                            potential_options["symbol"].append(symbol)
                            potential_options["contract"].append(value[0]["symbol"])
                            potential_options["putCall"].append(value[0]["putCall"])
                            potential_options["current_price"].append(current_price)
                            potential_options["strike"].append(strike)
                            potential_options["bid"].append(value[0]["bid"])
                            potential_options["ask"].append(value[0]["ask"])
                            potential_options["last_price"].append(value[0]["last"])
                            potential_options["totalVolume"].append(
                                value[0]["totalVolume"]
                            )
                            potential_options["daysToExpiration"].append(
                                value[0]["daysToExpiration"]
                            )
                            potential_options["inTheMoney"].append(
                                value[0]["inTheMoney"]
                            )
                            potential_options["volatility"].append(
                                value[0]["volatility"]
                            )
                            potential_options["delta"].append(value[0]["delta"])
                            potential_options["gamma"].append(value[0]["gamma"])
                            potential_options["vega"].append(value[0]["vega"])
                            potential_options["rho"].append(value[0]["rho"])
                            potential_options["openInterest"].append(
                                value[0]["openInterest"]
                            )
                            break
                    except Exception as e:
                        pass
        df = pd.DataFrame.from_dict(potential_options)
        if df.empty:
            logging.info("No contracts")
        return df

    def option_order(self, params: dict[str, Any]) -> dict[str, Any]:
        price = params["price"]
        quantity = params["quantity"]
        symbol = params["symbol"]
        tradeType = params["tradeType"]
        trade_params = {
            "complexOrderStrategyType": "NONE",
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": f"{price}",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": tradeType,
                    "quantity": quantity,
                    "instrument": {"symbol": f"{symbol}", "assetType": "OPTION"},
                }
            ],
        }
        return trade_params

    def chain_sell_to_close(
        self,
        symbol: str,
        sell_quantities: list[int],
        sell_prices: list[float],
        index: int,
    ) -> list[Any]:
        trade_params = {
            "orderStrategyType": "SINGLE",
            "session": "NORMAL",
            "duration": "GOOD_TILL_CANCEL",
            "orderType": "LIMIT",
            "price": f"{sell_prices[index]}",
            "orderLegCollection": [
                {
                    "instruction": "SELL_TO_CLOSE",
                    "quantity": int(sell_quantities[index]),
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": f"{symbol}",
                    },
                }
            ],
        }
        if index < len(sell_prices) - 1:
            trade_params["orderStrategyType"] = "TRIGGER"
            trade_params["childOrderStrategies"] = self.chain_sell_to_close(
                symbol, sell_quantities, sell_prices, index + 1
            )
        return [trade_params]

    def spread_option_order(self, params: dict[str, Any]) -> dict[str, Any]:
        net_payment = params["net_payment"]
        buy_instruction = params["buy_instruction"]
        buy_quantity = params["buy_quantity"]
        buy_symbol = params["buy_symbol"]
        sell_instruction = params["sell_instruction"]
        sell_quantity = params["sell_quantity"]
        sell_symbol = params["sell_symbol"]
        orderType = params["orderType"]
        trade_params = {
            "orderType": orderType,
            "session": "NORMAL",
            "price": net_payment,
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "complexOrderStrategyType": "VERTICAL",
            "quantity": buy_quantity,
            "orderLegCollection": [
                {
                    "instruction": buy_instruction,
                    "quantity": buy_quantity,
                    "instrument": {"symbol": buy_symbol, "assetType": "OPTION"},
                },
                {
                    "instruction": sell_instruction,
                    "quantity": sell_quantity,
                    "instrument": {"symbol": sell_symbol, "assetType": "OPTION"},
                },
            ],
        }
        return trade_params

    def sequence_option_order(self, params: dict[str, Any]) -> dict[str, Any]:
        bid = params["bid"]
        quantity = params["quantity"]
        symbol = params["symbol"]
        sell_prices = params["sell_prices"]
        sell_quantities = params["sell_quantities"]
        childOrderStrategies = self.chain_sell_to_close(
            symbol, sell_quantities, sell_prices, 0
        )
        trade_params = {
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "price": f"{bid}",
            "orderLegCollection": [
                {
                    "instruction": "BUY_TO_OPEN",
                    "instrument": {"assetType": "OPTION", "symbol": symbol},
                    "quantity": int(quantity),
                }
            ],
            "orderStrategyType": "TRIGGER",
            "childOrderStrategies": childOrderStrategies,
        }
        return trade_params

    def conditional_option_order(self, params: dict[str, Any]) -> dict[str, Any]:
        bid = params["bid"]
        quantity = params["quantity"]
        symbol = params["symbol"]
        sell_prices = params["sell_prices"]
        sell_quantities = params["sell_quantities"]
        childOrderStrategies = []
        for sell_amount, sell_price in zip(sell_quantities, sell_prices):
            childOrderStrategies.append(
                {
                    "orderStrategyType": "SINGLE",
                    "session": "NORMAL",
                    "duration": "GOOD_TILL_CANCEL",
                    "orderType": "LIMIT",
                    "price": f"{sell_price}",
                    "orderLegCollection": [
                        {
                            "instruction": "SELL_TO_CLOSE",
                            "quantity": int(sell_amount),
                            "instrument": {
                                "assetType": "OPTION",
                                "symbol": f"{symbol}",
                            },
                        }
                    ],
                }
            )
        trade_params = {
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "price": f"{bid}",
            "orderLegCollection": [
                {
                    "instruction": "BUY_TO_OPEN",
                    "instrument": {"assetType": "OPTION", "symbol": symbol},
                    "quantity": int(quantity),
                }
            ],
            "orderStrategyType": "TRIGGER",
            "childOrderStrategies": childOrderStrategies,
        }
        return trade_params

    def conditional_OTA_stop(self, params: dict[str, Any]) -> dict[str, Any]:
        """When filled, sets stop loss and price out"""
        symbol = params["symbol"]
        inPrice = params["inPrice"]
        inQuantity = params["inQuantity"]
        stopLossPrice = params["stopLossPrice"]
        stopLossQuantity = params["stopLossQuantity"]
        assetType = params["assetType"]
        buyType = params["buyType"]
        sellType = params["sellType"]
        buy_order = {
            "orderStrategyType": "TRIGGER",
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "price": inPrice,
            "orderLegCollection": [
                {
                    "instruction": buyType,
                    "quantity": inQuantity,
                    "instrument": {"assetType": assetType, "symbol": f"{symbol}"},
                }
            ],
            "childOrderStrategies": [
                {
                    "orderStrategyType": "SINGLE",
                    "session": "NORMAL",
                    "duration": "GOOD_TILL_CANCEL",
                    "orderType": "STOP",
                    "stopPrice": stopLossPrice,
                    "orderLegCollection": [
                        {
                            "instruction": sellType,
                            "quantity": stopLossQuantity,
                            "instrument": {
                                "assetType": assetType,
                                "symbol": f"{symbol}",
                            },
                        }
                    ],
                },
            ],
        }
        return buy_order

    def conditional_OTA(self, params: dict[str, Any]) -> dict[str, Any]:
        """When filled, sets stop loss and price out"""
        symbol = params["symbol"]
        inPrice = params["inPrice"]
        inQuantity = params["inQuantity"]
        profitPrice = params["profitPrice"]
        profitQuantity = params["profitQuantity"]
        assetType = params["assetType"]
        buyType = params["buyType"]
        sellType = params["sellType"]
        buy_order = {
            "orderStrategyType": "TRIGGER",
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "price": inPrice,
            "orderLegCollection": [
                {
                    "instruction": buyType,
                    "quantity": inQuantity,
                    "instrument": {"assetType": assetType, "symbol": f"{symbol}"},
                }
            ],
            "childOrderStrategies": [
                {
                    "orderStrategyType": "SINGLE",
                    "session": "NORMAL",
                    "duration": "GOOD_TILL_CANCEL",
                    "orderType": "LIMIT",
                    "price": profitPrice,
                    "orderLegCollection": [
                        {
                            "instruction": sellType,
                            "quantity": profitQuantity,
                            "instrument": {
                                "assetType": assetType,
                                "symbol": f"{symbol}",
                            },
                        }
                    ],
                }
            ],
        }
        return buy_order

    def single_order(self, params: dict[str, Any]) -> dict[str, Any]:
        order = {
            "complexOrderStrategyType": "NONE",
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": params["bid"],
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": params["orderType"],
                    "quantity": params["quantity"],
                    "instrument": {
                        "symbol": params["symbol"],
                        "assetType": params["assetType"],
                    },
                }
            ],
        }
        return order

    def conditional_OCO(self, params: dict[str, Any]) -> dict[str, Any]:
        """When filled, sets stop loss and price out"""
        symbol = params["symbol"]
        inPrice = params["inPrice"]
        inQuantity = params["inQuantity"]
        stopLossPrice = params["stopLossPrice"]
        stopLossQuantity = params["stopLossQuantity"]
        profitPrice = params["profitPrice"]
        profitQuantity = params["profitQuantity"]
        assetType = params["assetType"]
        buyType = params["buyType"]
        sellType = params["sellType"]
        buy_order = {
            "orderStrategyType": "TRIGGER",
            "session": "NORMAL",
            "duration": "DAY",
            "orderType": "LIMIT",
            "price": inPrice,
            "orderLegCollection": [
                {
                    "instruction": buyType,
                    "quantity": inQuantity,
                    "instrument": {"assetType": assetType, "symbol": f"{symbol}"},
                }
            ],
            "childOrderStrategies": [
                {
                    "orderStrategyType": "OCO",
                    "childOrderStrategies": [
                        {
                            "orderStrategyType": "SINGLE",
                            "session": "NORMAL",
                            "duration": "GOOD_TILL_CANCEL",
                            "orderType": "LIMIT",
                            "price": profitPrice,
                            "orderLegCollection": [
                                {
                                    "instruction": sellType,
                                    "quantity": profitQuantity,
                                    "instrument": {
                                        "assetType": assetType,
                                        "symbol": f"{symbol}",
                                    },
                                }
                            ],
                        },
                        {
                            "orderStrategyType": "SINGLE",
                            "session": "NORMAL",
                            "duration": "GOOD_TILL_CANCEL",
                            "orderType": "STOP",
                            "stopPrice": stopLossPrice,
                            "orderLegCollection": [
                                {
                                    "instruction": sellType,
                                    "quantity": stopLossQuantity,
                                    "instrument": {
                                        "assetType": assetType,
                                        "symbol": f"{symbol}",
                                    },
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        return buy_order

    def get_market_order(self, params: dict[str, Any]) -> dict[str, Any]:
        trade_params = {
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": params["tradeType"],
                    "quantity": params["quantity"],
                    "instrument": {"symbol": params["symbol"], "assetType": "EQUITY"},
                }
            ],
        }
        return trade_params

    def get_equity_order(self, params: dict[str, Any]) -> dict[str, Any]:
        trade_params = {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": params["price"],
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": params["tradeType"],
                    "quantity": params["quantity"],
                    "instrument": {"symbol": params["symbol"], "assetType": "EQUITY"},
                }
            ],
        }
        return trade_params

    def trade_equity(self, params: dict[str, Any]) -> None:
        trade_params = self.get_market_order(params)
        orderId = self.place_order(trade_params)
        logging.info(orderId)
        (
            bidPrice,
            askPrice,
            midpoint,
            margin,
            spread,
        ) = self.get_price_points(params["symbol"])
        inPrice = bidPrice if params["tradeType"] == "SELL_SHORT" else askPrice
        self.db["working_orders"].insert_one(
            {
                "time": time.time(),
                "date": str(datetime.datetime.now().date()),
                "tradeType": params["tradeType"],
                "price": inPrice,
                "symbol": params["symbol"],
                "quantity": params["quantity"],
                "orderId": orderId,
                "filled": False,
                "tradeDirection": params["tradeDirection"],
                "tradeStrategy": params["tradeStrategy"],
                "IV": params["IV"] if "IV" in params else None,
                "user": self.TOKEN_NAME,
            },
        )

    def sell_all_equities(self) -> None:
        positions = self.get_positions()
        for position in positions:
            instrument = position["instrument"]
            assetType = instrument["assetType"]
            if assetType == "EQUITY":
                quantity = (
                    position["shortQuantity"]
                    if position["shortQuantity"] > 0
                    else position["longQuantity"]
                )
                symbol = instrument["symbol"]
                marketValue = position["marketValue"]
                direction = "BUY" if position["shortQuantity"] > 0 else "SELL"
                try:
                    price = self.price_asset(symbol, direction)
                    assetParams: dict[str, Any] = {
                        "symbol": symbol,
                        "quantity": quantity,
                        "price": price,
                    }
                    tradeType = (
                        "BUY_TO_COVER" if position["shortQuantity"] > 0 else "SELL"
                    )
                    assetParams["tradeType"] = tradeType
                    trade_params = self.get_equity_order(assetParams)
                    logging.info(trade_params)
                    orderId = self.place_order(trade_params)
                    logging.info("orderId", orderId)
                except Exception as e:
                    logging.info(e)

    def close_all_equity_shorts(self) -> None:
        positions = self.get_positions()
        for position in positions:
            instrument = position["instrument"]
            assetType = instrument["assetType"]
            if assetType == "EQUITY" and position["shortQuantity"] > 0:
                quantity = position["shortQuantity"]
                symbol = instrument["symbol"]
                marketValue = position["marketValue"]
                direction = "BUY"
                try:
                    price = self.price_asset(symbol, direction)
                    assetParams: dict[str, Any] = {
                        "symbol": symbol,
                        "quantity": quantity,
                        "price": price,
                    }
                    tradeType = "BUY_TO_COVER"
                    assetParams["tradeType"] = tradeType
                    trade_params = self.get_equity_order(assetParams)
                    logging.info(trade_params)
                    orderId = self.place_order(trade_params)
                    logging.info("orderId", orderId)
                except Exception as e:
                    logging.info(e)

    def sell_all_options(self) -> None:
        positions = self.get_positions()
        for position in positions:
            # logging.info(position)
            instrument = position["instrument"]
            assetType = instrument["assetType"]
            if assetType == "OPTION":
                quantity = (
                    position["shortQuantity"]
                    if position["shortQuantity"] > 0
                    else position["longQuantity"]
                )
                symbol = instrument["symbol"]
                marketValue = position["marketValue"]
                direction = "BUY" if position["shortQuantity"] > 0 else "SELL"
                try:
                    price = self.price_asset(symbol, direction)
                    assetParams: dict[str, Any] = {
                        "symbol": symbol,
                        "quantity": quantity,
                        "price": price,
                    }
                    underlying = instrument["underlyingSymbol"]
                    # if underlying == "SOS":
                    today = datetime.date.today()
                    num_days_til_exp = (
                        extract_date_from_description(instrument["description"]) - today
                    ).days
                    logging.info("num_days_til_exp", num_days_til_exp)
                    # if num_days_til_exp < 30 and price > 0.05:
                    tradeType = (
                        "BUY_TO_CLOSE"
                        if position["shortQuantity"] > 0
                        else "SELL_TO_CLOSE"
                    )
                    assetParams["tradeType"] = tradeType
                    trade_params = self.option_order(assetParams)
                    logging.info(trade_params)
                    orderId = self.place_order(trade_params)
                    logging.info("orderId", orderId)
                except Exception as e:
                    logging.info(e)

    def sell_all_positions(self) -> None:
        self.sell_all_options()
        self.sell_all_equities()

    def cancel_symbol_order(self, symbol):
        order_params = {"status": "QUEUED"}
        orders_raw = self.get_orders(order_params)
        for order in orders_raw:
            orderId = order["orderId"]
            order_symbol = order["orderLegCollection"][0]["instrument"]["symbol"]
            if symbol == order_symbol:
                logging.info(orderId)
                content = self.cancel_order(orderId)
                logging.info(content)
                break

    def cancel_all_pending(self) -> None:
        order_params = {
            "status": "WORKING",
        }
        orders_raw: dict = self.get_orders(order_params)
        for order in orders_raw:
            orderId = order["orderId"]
            quantity = order["quantity"]
            equity = order["orderLegCollection"][0]["orderLegType"]
            symbol = order["orderLegCollection"][0]["instrument"]["symbol"]
            logging.info(orderId)
            content = self.cancel_order(orderId)
            logging.info(content)


def get_client(
    secrets_path: str, API_KEY: str, REDIRECT_URI: str, TOKEN_NAME: str
) -> Any:
    "Returns an OAuth client, using the given path as a secrets store"

    import os
    import pickle

    # Load old token from secrets directory
    token_path = os.path.join(os.path.expanduser(secrets_path), TOKEN_NAME)
    token = None
    try:
        with open(token_path, "rb") as f:
            try:
                token = pickle.load(f)
            except:
                token = json.load(f)
    except FileNotFoundError:
        pass
    # On failure, fetch a new token using OAuth and Selenium. Unfortunately TD
    # only supports the webapp workflow, so we have to open up a browser.
    if token is None:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        oauth = OAuth2Session(API_KEY, redirect_uri=REDIRECT_URI)
        authorization_url, state = oauth.authorization_url(
            "https://auth.tdameritrade.com/auth"
        )

        # Open a Chrome browser to take the credentials
        chrome_options = Options()
        #         user_data_dir = os.path.join(secrets_path, 'chrome')
        #         chrome_options.add_argument("user-data-dir={}".format(user_data_dir))
        with webdriver.Chrome(
            "/Users/morgan" + "/Downloads/chromedriver", options=chrome_options
        ) as driver:
            driver.get(authorization_url)

            # Wait to catch the redirect
            import time

            callback_url = ""
            while not callback_url.startswith(REDIRECT_URI):
                callback_url = driver.current_url
                time.sleep(1)

            token = oauth.fetch_token(
                "https://api.tdameritrade.com/v1/oauth2/token",
                authorization_response=callback_url,
                access_type="offline",
                client_id=API_KEY,
                include_client_id=True,
            )

    # Record the token
    def update_token(t: Any) -> None:
        with open(token_path, "wb") as f:
            pickle.dump(t, f)

    update_token(token)

    # Return a new session configured to refresh credentials
    return OAuth2Session(
        API_KEY,
        token=token,
        auto_refresh_url="https://api.tdameritrade.com/v1/oauth2/token",
        auto_refresh_kwargs={"client_id": API_KEY},
        token_updater=update_token,
    )
