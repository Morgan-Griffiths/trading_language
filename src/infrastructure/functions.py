import datetime

from src.infrastructure.lazy_evaluator import LazyFunction
from src.common_types import SYMBOLS
from trade.utils import third_friday, trading_days, spy_sigma
from src.utils import parse_date, parse_datetime


# These functions should link to getting the exact value.
# 2021-11-18 15:56:50.420042
opex = LazyFunction("OPEX", lambda context: third_friday())
today = LazyFunction("TODAY", lambda context: datetime.datetime.now())
today_date = LazyFunction("TODAY_DATE", lambda context: datetime.datetime.now().date())
distance_to_opex = LazyFunction(
    "DISTANCE_TO_OPEX",
    lambda context: parse_date(context.get_value("OPEX"))
    - parse_date(context.get_value("TODAY_DATE")),
)
previous_opex = LazyFunction(
    "PREVIOUS_OPEX",
    lambda context: third_friday(
        parse_datetime(context.get_value("TODAY")).date() - datetime.timedelta(days=35)
    )
    - (third_friday() - parse_date(context.get_value("TODAY_DATE"))),
)
days_until_opex = LazyFunction(
    "DAYS_UNTIL_OPEX",
    lambda context: trading_days(
        (
            parse_date(context.get_value("OPEX"))
            - parse_date(context.get_value("TODAY_DATE"))
        ).days
    ),
)
atm_option = LazyFunction(
    "atm_option",
    lambda context: context.api.get_ATM_option(
        "SPY",
        context.get_value("DAYS_UNTIL_OPEX"),
        "CALL",
        parse_datetime(context.get_value("TODAY")),
    ),
)
spy_sig = LazyFunction(
    "SPY_SIGMA",
    lambda context: spy_sigma(
        context.get_value("SPY"),
        context.get_value("atm_option")["volatility"] / 100,
        context.get_value("DAYS_UNTIL_OPEX"),
    ),
)
positions = LazyFunction("positions", lambda context: context.api.get_positions())
net_position = LazyFunction(
    "NET_POSITION",
    lambda context: sum(
        [position["marketValue"] for position in context.get_value("positions")]
    ),
)
spy_20_day_mean = LazyFunction(
    "SPY_20_DAY_MEAN", lambda context: context.fetch.spy_20_day()
)
bankroll = LazyFunction(
    "BANKROLL",
    lambda context: context.api.get_bankroll(),
)

symbol_functions = []
for sym in SYMBOLS:
    symbol_functions.append(
        LazyFunction(sym, lambda context: context.api.get_last_price(sym))
    )

function_list: list = [
    opex,
    today,
    today_date,
    distance_to_opex,
    previous_opex,
    days_until_opex,
    atm_option,
    spy_sig,
    positions,
    net_position,
    spy_20_day_mean,
    bankroll,
]
function_list.extend(symbol_functions)
