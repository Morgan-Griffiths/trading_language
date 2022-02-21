import json
import os
from trade.utils import third_friday, trading_days, actual_trading_days
import datetime
import numpy as np
import calendar

CAL = {month: index for index, month in enumerate(calendar.month_abbr) if month}

default_tabs = [
    "0 3 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/main.py -f data",
    "0 5 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/main.py -f update_fundamentals",
    "0 13 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/main.py -f clear_history",
    "0 1 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/main.py -f dl_spy",
    "15 13 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/main.py -f clear_unfilled",
    "30 13 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/database/positioning_migration.py",
    "50 5 * * 1-5 cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9 /Users/morgan/Code/TDameritrade/stream.py",
]


class crontab(object):
    def __init__(self, minute, hour, day, month, dow):
        self.minute = minute
        self.hour = hour
        self.day = day
        self.month = month
        self.dow = dow
        self.trigger = (
            "cd /Users/morgan/Code/TDameritrade; ~/anaconda3/envs/market/bin/python3.9"
        )
        self.func_name = "<func goes here>"

    def PST(self):
        self.hour = str(int(self.hour) - 3)

    def __str__(self):
        return (
            str(self.minute)
            + " "
            + str(self.hour)
            + " "
            + str(self.day)
            + " "
            + str(self.month)
            + " "
            + str(self.dow)
            + " "
            + self.trigger
            + " "
            + self.func_name
        )


def return_trading_day_distance(target: datetime.date, start: int):
    new_start = start
    start_date = target - datetime.timedelta(days=new_start)
    distence_to_opex = trading_days(target.day, start_date)
    while distence_to_opex < start:
        new_start += 1
        start_date = target - datetime.timedelta(days=new_start)
        distence_to_opex = trading_days(target.day, start_date)
    print("distence_to_opex", distence_to_opex)
    return new_start


def partition_big_days(opex, start_day):
    print("start_day", start_day)
    print("opex", opex)
    remainder = start_day % 2
    if start_day > 20:
        if remainder == 1:
            half = start_day - remainder
            inter_start = opex - datetime.timedelta(days=remainder)
            inter_start = inter_start - datetime.timedelta(days=half // 2)
            start_date = inter_start - datetime.timedelta(days=half // 2)
        else:
            half = start_day // 2
            inter_start = opex - datetime.timedelta(days=half // 2)
            start_date = inter_start - datetime.timedelta(days=half // 2)
    else:
        start_date = opex - datetime.timedelta(days=start_day)
    print("start_date", start_date)
    return start_date


def decrement_month(year, month) -> int:
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1
    return calendar.monthrange(year, month)[1], year, month


def subtract_days(target_date: datetime.date, num_days: int) -> datetime.date:
    """Current date is of the form YYYY-MM-DD"""
    y, m, d = str(target_date).split("-")
    y, m, d = int(y), int(m), int(d)
    result = d - num_days
    if result < 1:
        # roll over into the next month
        while result < 1:
            days, y, m = decrement_month(y, m)
            result += days
    return datetime.date(y, m, result)


def covert_opexdays_to_DOM(opex, days: list) -> list:
    if isinstance(days[0], str) and days[0].find("-") > -1:
        start_day, end_day = days[0].split("-")
        start_day = int(start_day)
        end_day = int(end_day)
        # trading_distance: int = np.busday_count(
        #     opex - datetime.timedelta(days=start_day), opex
        # )
        # print("trading_distance", trading_distance)
        # while trading_distance < start_day:
        #     start_day += 1
        #     trading_distance: int = np.busday_count(
        #         opex - datetime.timedelta(days=start_day), opex
        #     )
        #     print("trading_distance", trading_distance)
        calendar_days = [
            subtract_days(opex, day)
            for day in range(end_day - 1, start_day + 1)
            if np.is_busday(subtract_days(opex, day))
        ]
    elif days[0] != "*":
        calendar_days = [
            opex - datetime.timedelta(days=int(day))
            for day in days
            if np.is_busday(opex - datetime.timedelta(days=int(day)))
        ]
    else:
        calendar_days = ["*"]
    calendar_days.sort()
    return calendar_days


def schedule_parser(opex, days: list, times: list, function: str):
    days.sort()
    actual_days: list = covert_opexdays_to_DOM(opex, days)
    crontabs = []
    for time in times:
        for i, date in enumerate(actual_days):
            if date == "*":
                minute = str(time.split(":")[1])
                hour = str(time.split(":")[0])
                crontime = crontab(minute, hour, "*", "*", "1-5")
                crontime.func_name = function
                crontime.PST()
                crontabs.append(crontime)
            else:
                day = date.day
                month = date.month
                if i > 0 and actual_days[i - 1].day == day - 1:
                    prev_cron = crontabs[-1]
                    prev_cron.day = prev_cron.day.split("-")[0] + f"-{day}"
                    crontabs[-1] = prev_cron
                else:
                    minute = str(time.split(":")[1])
                    hour = str(time.split(":")[0])
                    crontime = crontab(minute, hour, str(day), month, "*")
                    crontime.func_name = function
                    crontime.PST()
                    crontabs.append(crontime)
    return crontabs


def load_trades() -> list:
    folder = os.path.join(os.getcwd(), "trade/position_descriptions")
    trade_descriptions = []
    for trade in os.listdir(folder):
        if trade.split(".")[-1] == "json":
            file_path = os.path.join(folder, trade)
            print(file_path)
            with open(file_path, "rb") as json_file:
                trade_description = json.load(json_file)
                trade_descriptions.append((trade_description, file_path))
    return trade_descriptions


def parse_trade(trade: tuple) -> list:
    opex = third_friday()
    trade_description, program_path = trade
    trade_doors = ["open", "close"]
    tabs = []
    for door in trade_doors:
        if f"{door}_position" in trade_description:
            position = trade_description[f"{door}_position"]
            tabs.extend(
                schedule_parser(
                    opex,
                    position["days"],
                    position["times"],
                    f"trade_interpreter.py -f {program_path} -t {door}",
                )
            )
    return tabs


def write_crontabs(crontabs: list) -> None:
    folder = os.path.join(os.getcwd(), "trade/position_descriptions")
    final_tabs = [str(cron) for cron in crontabs]
    crontab_str = "\n".join(final_tabs) + "\n\r"
    with open(f"{folder}/cron.txt", "w") as handle:
        handle.write(crontab_str)


def generate_crontabs():
    global default_tabs
    crontabs = []
    trade_descriptions = load_trades()
    for trade in trade_descriptions:
        crontabs.extend(parse_trade(trade))
    crontabs.extend(default_tabs)
    write_crontabs(crontabs)
    os.system(f"crontab trade/position_descriptions/cron.txt")


if __name__ == "__main__":
    generate_crontabs()
