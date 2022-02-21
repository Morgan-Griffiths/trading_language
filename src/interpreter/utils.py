import datetime
from trade.utils import shape_price
from src.utils import parse_date, parse_datetime


def compute_entry_point(price_data, entry_point, trade_type):
    # EQUITIES are bidPrice OPTIONS are bid
    bid = "bidPrice" if "bidPrice" in price_data else "bid"
    ask = "askPrice" if "askPrice" in price_data else "ask"
    if entry_point == "MARKET":
        inPrice = (
            price_data[bid]
            if (trade_type == "SELL" or trade_type == "SELL_TO_OPEN")
            else price_data[ask]
        )
    elif entry_point == "MIDPOINT":
        inPrice = round(((price_data[bid] + price_data[ask]) / 2), 2)
    elif entry_point == "2/3rds":
        if trade_type == "SELL":
            inPrice = round(
                price_data[ask] - (((price_data[ask] - price_data[bid]) / 3) * 2),
                2,
            )
        else:
            inPrice = round(
                price_data[bid] + (((price_data[ask] - price_data[bid]) / 3) * 2),
                2,
            )
    else:
        raise ValueError(f"Entry point not valid {entry_point}")
    return inPrice


def return_option_spread_params(
    symbol, context, variables, spread: dict, quantity=None
):
    print("spread", spread)
    sell_logic = spread["sell"]
    sell_strike = round(sell_logic["strike"], 0)
    sell_expiration = sell_logic["expiration"]
    if isinstance(sell_expiration, datetime.datetime):
        sell_expiration = sell_expiration.date()
    sell_putCall = sell_logic["contractType"]
    sell_option_exp_delta = parse_date(sell_expiration) - parse_date(
        context.get_value("TODAY_DATE")
    )
    sell_option = context.api.get_specific_option(
        symbol,
        sell_putCall,
        sell_expiration,
        sell_strike,
        sell_option_exp_delta,
    )[0]
    buy_logic = spread["buy"]
    buy_strike = round(buy_logic["strike"], 0)
    buy_expiration = buy_logic["expiration"]
    if isinstance(buy_expiration, datetime.datetime):
        buy_expiration = buy_expiration.date()
    buy_putCall = buy_logic["contractType"]
    buy_option_exp_delta = parse_date(buy_expiration) - parse_date(
        context.get_value("TODAY_DATE")
    )
    buy_option = context.api.get_specific_option(
        symbol,
        buy_putCall,
        buy_expiration,
        buy_strike,
        buy_option_exp_delta,
    )[0]
    sell_price = compute_entry_point(sell_option, variables["entry_point"], "SELL")
    buy_price = compute_entry_point(buy_option, variables["entry_point"], "BUY")
    net_payment = shape_price(sell_price - buy_price)
    if not quantity:
        quantity = int(variables["per_trade"] / (abs(net_payment) * 10))
    print("here", variables["tradeDirection"])
    if variables["tradeDirection"] == "open":
        buy_instruction = "BUY_TO_OPEN"
        sell_instruction = "SELL_TO_OPEN"
    else:
        buy_instruction = "BUY_TO_CLOSE"
        sell_instruction = "SELL_TO_CLOSE"
    if net_payment > 0:
        orderType = "NET_CREDIT"
    else:
        orderType = "NET_DEBIT"
    spread_params = {
        "net_payment": net_payment,
        "symbol": symbol,
        "orderType": orderType,
        "buy_price": buy_price,
        "buy_quantity": quantity,
        "buy_symbol": buy_option["symbol"],
        "buy_instruction": buy_instruction,
        "sell_price": sell_price,
        "sell_quantity": quantity,
        "sell_symbol": sell_option["symbol"],
        "sell_instruction": sell_instruction,
    }
    return spread_params


def close_spread(order, legs):
    buy_data = order["buy_symbol"].split("_")[-1]
    buy_putCall = "PUT" if buy_data.find("P") > 0 else "CALL"
    buy_strike = buy_data.split(buy_putCall[0])[-1]
    buy_expiration = legs["buy"]["expiration"]
    sell_data = order["sell_symbol"].split("_")[-1]
    sell_putCall = "PUT" if sell_data.find("P") > 0 else "CALL"
    sell_strike = sell_data.split(sell_putCall[0])[-1]
    sell_expiration = legs["buy"]["expiration"]
    spread = {
        "sell": {
            "strike": int(buy_strike),
            "expiration": buy_expiration,
            "contractType": buy_putCall,
        },
        "buy": {
            "strike": int(sell_strike),
            "expiration": sell_expiration,
            "contractType": sell_putCall,
        },
    }
    return spread
