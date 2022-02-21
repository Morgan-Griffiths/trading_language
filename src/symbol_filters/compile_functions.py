from more_itertools import peekable
from src.compiler.tokenizer import Token
from src.common_types import (
    CSV,
    Aggregator,
    Column,
    Database,
    Group,
    Number,
    Range,
    Separator,
    Symbol,
    Field,
    column_mapping,
    csv_mapping,
)
from src.compiler.utils import is_member
from src.compiler.parser import Parser


class SymbolFilterCompiler:
    def __init__(self) -> None:
        self.parser = Parser()

    def agg_column_parser(self, tokens: peekable):
        aggs, columns = self.agg_parser(tokens, [], [])
        op = next(tokens).lexeme
        right = self.parser.parse_s_expr(tokens)
        return aggs, columns, op, right

    def agg_parser(self, tokens, aggs=[], columns=[]):
        if is_member(tokens.peek(), [Aggregator]):
            print("agg", aggs, tokens.peek().lexeme)
            aggs.append(tokens.peek().lexeme)
            next(tokens)
            assert is_member(
                tokens.peek(), [Group]
            ), f"Expected type Group found {tokens.peek().lexeme}"
            return self.agg_parser(tokens, aggs, columns)
        elif is_member(tokens.peek(), [Range]):
            # positioning
            next(tokens)
            assert is_member(
                tokens.peek(), [Group]
            ), f"Expected type Group found {tokens.peek().lexeme}"
            next(tokens)
            start = int(tokens.peek().lexeme)
            assert is_member(
                tokens.peek(), [Number]
            ), f"Expected type Number found {tokens.peek().lexeme}"
            next(tokens)
            assert is_member(
                tokens.peek(), [Separator]
            ), f"Expected type Separator found {tokens.peek().lexeme}"
            next(tokens)
            end = int(tokens.peek().lexeme)
            assert is_member(
                tokens.peek(), [Number]
            ), f"Expected type number found {tokens.peek().lexeme}"
            assert start < end, "Start must be before end"
            assert start >= -1, "Start must be -1 or greater"
            assert end <= 32, "End must be 32 or less"
            columns = [f"scaled_direction_day_{i}" for i in range(start, end + 1)]
            next(tokens)
            while is_member(tokens.peek(), [Group]):
                next(tokens)
            return aggs, columns
        elif is_member(tokens.peek(), [Column]):
            columns = self.return_columns(tokens)
            while is_member(tokens.peek(), [Group]):
                next(tokens)
            return aggs, columns
        elif is_member(tokens.peek(), [Group, CSV]):
            next(tokens)
            return self.agg_parser(tokens, aggs, columns)
        else:
            raise ValueError(f"{tokens.peek().lexeme}, improper syntax")

    def return_columns(self, tokens: peekable) -> list:
        columns = []
        while is_member(tokens.peek(), [Column]):
            columns.append(column_mapping[tokens.peek().lexeme])
            next(tokens)
        return columns

    def compile_column_filter(self, tokens: peekable) -> list:
        assert is_member(tokens.peek(), [Column])
        op, left, right = self.parser.parse_s_expr(tokens)
        column = column_mapping[left]
        csv = csv_mapping[column]
        return [
            "filter_csv",
            f"{csv}",
            ["list", "None"],
            ["list", column],
            "@symbols",
            f"{op}",
            right,
        ]

    def compile_agg_column_filter(self, tokens: peekable) -> list:
        assert is_member(tokens.peek(), [Aggregator])
        aggs, columns, op, right = self.agg_column_parser(tokens)
        print("aggs, columns, op, right", aggs, columns, op, right)
        csv = csv_mapping[columns[0]]
        return [
            "filter_csv",
            f"{csv}",
            ["list"] + aggs,
            ["list"] + columns,
            "@symbols",
            f"{op}",
            right,
        ]

    def compile_in_portfolio(self, tokens: peekable):
        assert tokens.peek().lexeme == "not" or tokens.peek().lexeme == "in"
        inclusive = True if tokens.peek().lexeme == "in" else False
        return ["in_portfolio", "@symbols", inclusive]

    def compile_order_filter(self, tokens: peekable):
        assert is_member(tokens.peek(), [Database])
        next(tokens)
        assert is_member(tokens.peek(), [Field])
        field = next(tokens).lexeme
        value = next(tokens).lexeme
        return ["filter_orders", "@symbols", field, value]

    def compile_given_filter(self, tokens: peekable):
        assert tokens.peek().lexeme == "given"
        next(tokens)
        op, column, value = self.parser.parse_s_expr(tokens)
        conditions = ["list", ["list", column, op, value]]
        while is_member(tokens.peek(), [Column]):
            op, column, value = self.parser.parse_s_expr(tokens)
            conditions.append(["list", column, op, value])
        assert is_member(
            tokens.peek(), [Aggregator]
        ), f"Expected Agg encountered {tokens.peek().lexeme}"
        pandas_operations, select_columns, op, amount = self.agg_column_parser(tokens)
        column = column_mapping[column]
        csv = csv_mapping[column]
        return [
            "filter_given",
            f"{csv}",
            conditions,
            ["list"] + list(reversed(pandas_operations)),
            ["list"] + select_columns,
            "@symbols",
            f"{op}",
            amount,
        ]

    def compile_symbol_price(self, tokens: peekable):
        assert tokens.peek().lexeme == "symbol_price"
        op, left, right = self.parser.parse_s_expr(tokens)
        return ["filter_price", "@symbols", op, right]
