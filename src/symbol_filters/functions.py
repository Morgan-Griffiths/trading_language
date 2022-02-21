from dataclasses import dataclass
import re
from typing import Any, Callable, Literal, Protocol, Set
from more_itertools.more import peekable
import src.symbol_filters.forward_functions as ff
import src.symbol_filters.backward_functions as bf
from src.symbol_filters.compile_functions import SymbolFilterCompiler
from src.common_types import column_names, aggregator_names, database_names, query_names
from src.tokens import Token, Tokens


class TokenMatcher(Protocol):
    def matches(self, token_stream: peekable) -> bool:
        ...


class TokenMatcherLiteral:
    token: str = ""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, token_stream: Token) -> bool:
        return token_stream.peek().lexeme == self.token


class TokenMatcherMultiple:
    tokens: Set[str] = set()

    def __init__(self, tokens) -> None:
        self.tokens = set(tokens)

    def __call__(self, token_stream: Token) -> bool:
        return token_stream.peek().lexeme in self.tokens


@dataclass
class ReversibleFunction:
    token_match: TokenMatcher
    compile: Callable[[list[str]], Any]
    forward: Callable[[Any], list]
    backward: Callable[[bool], None]


sfc: SymbolFilterCompiler = SymbolFilterCompiler()

column_filter = ReversibleFunction(
    token_match=TokenMatcherMultiple(column_names),
    compile=sfc.compile_column_filter,
    forward=ff.filter_by_column,
    backward=bf.inverted_column_filter,
)
column_agg_filter = ReversibleFunction(
    token_match=TokenMatcherMultiple(aggregator_names),
    compile=sfc.compile_agg_column_filter,
    forward=ff.filter_by_column,
    backward=bf.inverted_column_filter,
)
order_filter = ReversibleFunction(
    token_match=TokenMatcherMultiple(database_names),
    compile=sfc.compile_order_filter,
    forward=ff.filter_orders,
    backward=bf.inverted_orders_filter,
)
given_filter = ReversibleFunction(
    token_match=TokenMatcherLiteral(Tokens.GIVEN),
    compile=sfc.compile_given_filter,
    forward=ff.filter_given,
    backward=bf.inverted_given_filter,
)
portfolio_filter = ReversibleFunction(
    token_match=TokenMatcherMultiple([Tokens.NOT, Tokens.IN]),
    compile=sfc.compile_in_portfolio,
    forward=ff.symbol_in_portfolio,
    backward=bf.inverted_in_portfolio,
)

functions = {
    "filter_csv": column_filter,
    "column_agg_filter": column_agg_filter,
    "order_filter": order_filter,
    "given_filter": given_filter,
    "in_portfolio": portfolio_filter,
}
function_list = [
    column_filter,
    column_agg_filter,
    order_filter,
    given_filter,
    portfolio_filter,
]
