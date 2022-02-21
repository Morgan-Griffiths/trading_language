from typing import Callable
from src.common_types import (
    Conditional,
    Range,
    Symbol,
    Value,
    Variable,
    Number,
    value_mapping,
)
from src.compiler.utils import is_member
from src.symbol_filters.functions import function_list as sff
from src.compiler.dict_parser import DictParser
from src.compiler.parser import Parser
import os
import json
from more_itertools import peekable
import logging

logging.basicConfig(level=logging.ERROR, filename="logs/compiler_activity.log")
logger = logging.getLogger("Compiler")


class Compiler:
    def __init__(self) -> None:
        self.symbol_filter_functions = sff
        self.parser = Parser()
        self.keyword_grammar: dict[str, Callable] = {
            "tradeType": self.parser.parse_value_expr,
            "positionType": self.parser.parse_value_expr,
            "assetType": self.parser.parse_value_expr,
            "entry_point": self.parser.parse_value_expr,
            "scheduled_close": self.parser.parse_s_expr,
            "stop": self.parser.parse_s_expr,
            "per_trade": self.parser.parse_s_expr,
            "max_bet": self.parser.parse_s_expr,
            "put_call": self.parser.parse_value_expr,
            "strike": self.parser.parse_s_expr,
            "expiration": self.parser.parse_s_expr,
            "contractType": self.parser.parse_value_expr,
        }

    def parse_symbol_pool(self, symbol_pool) -> list:
        if isinstance(symbol_pool, list):
            if symbol_pool[0].lexeme != "positioning":
                res = ["load_symbols"]
                res.extend(item.lexeme.upper() for item in symbol_pool)
            else:
                res = [item.lexeme for item in symbol_pool]
        else:
            res = ["load_symbols", symbol_pool.lexeme.upper()]
        return res

    def description_parser(self, tokens: peekable, keyword: str):
        func = self.keyword_grammar[keyword]
        return func(tokens)

    def parse_description_values(self, result):
        for k, v in result.items():
            if isinstance(v, list):
                tokens = v
            elif isinstance(v, dict):
                result[k] = self.parse_description_values(v)
                continue
            else:
                tokens = [v]
            result[k] = self.description_parser(peekable(tokens), k)
        return result

    def parse_at(self, tokens_list: list):
        tokens = peekable(tokens_list)
        tokens = [token.lexeme for token in tokens]
        return tokens

    def parse_on(self, tokens_list: list):
        tokens = peekable(tokens_list)
        if tokens.peek().lexeme == "market":
            res = ["*"]
        elif is_member(tokens.peek(), [Range]):
            day_token = next(tokens)
            res = []
            while bool(tokens):
                assert is_member(tokens.peek(), [Number])
                res.append(tokens.peek().lexeme)
                next(tokens)
        else:
            raise ValueError(f"Unknown day token {tokens.peek()}")
        return res

    def parse_when(self, conditions: list, direction: str) -> dict:
        boolean = "and" if direction == "open" else "or"
        parsed = []
        for condition in conditions:
            parsed.append(self.parser.parse_s_expr(peekable(condition)))
        result = {boolean: parsed}
        return result

    def parse_symbol_filter(self, conditions: list):
        parsed_conditions = []
        for condition in conditions:
            pcondition = peekable(condition)
            for func in self.symbol_filter_functions:
                if func.token_match(pcondition):
                    parsed_conditions.append(func.compile(pcondition))
                    break
        return parsed_conditions

    def parse_positions(self, position, direction):
        func_mapping = {
            "days": self.parse_on,
            "times": self.parse_at,
            "when": self.parse_when,
            "symbol_filter": self.parse_symbol_filter,
        }
        new_position = {}
        for keyword in ["days", "times", "when", "symbol_filter"]:
            if keyword in position:
                logger.info("keyword", keyword)
                logger.info(position[keyword])
                if keyword == "when":
                    new_position[keyword] = func_mapping[keyword](
                        position[keyword], direction
                    )
                else:
                    new_position[keyword] = func_mapping[keyword](position[keyword])
        return new_position

    def compile(self, text):
        dict_parser = DictParser(text)
        parsed_trade: dict = dict_parser.parse()
        parsed_trade["strategy"] = parsed_trade["strategy"][0].lexeme
        parsed_trade["symbol_pool"] = self.parse_symbol_pool(
            parsed_trade["symbol_pool"]
        )
        parsed_trade["position_description"] = self.parse_description_values(
            parsed_trade["position_description"]
        )
        if "open_position" in parsed_trade:
            parsed_trade["open_position"] = self.parse_positions(
                parsed_trade["open_position"], "open"
            )
        if "close_position" in parsed_trade:
            parsed_trade["close_position"] = self.parse_positions(
                parsed_trade["close_position"], "close"
            )
        return parsed_trade

    def compile_folder(self, input_folder, output_folder):
        for file_path in os.listdir(input_folder):
            if file_path != ".DS_Store":
                with open(os.path.join(input_folder, file_path), "r") as f:
                    input_trade = f.read()
                    output_trade = self.compile(input_trade)
                    with open(
                        os.path.join(output_folder, output_trade["strategy"]) + ".json",
                        "w",
                    ) as f:
                        f.write(json.dumps(output_trade))
