from src.compiler.tokenizer import tokenize_strings
import src.symbol_filters.functions as ff
from more_itertools import peekable


def test_matching_single():
    column = "given"
    column_token = tokenize_strings("", column, "")
    assert ff.given_filter.token_match(peekable(column_token)) == True


def test_matching_multi():
    column = ["volume", "average volume"]
    column_token = tokenize_strings("", column, "")
    assert ff.column_filter.token_match(peekable(column_token)) == True
