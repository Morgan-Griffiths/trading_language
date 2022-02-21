from typing import Any
from src.common_types import (
    Time,
    type_mapping,
    symbol_types,
    variable_names,
    Name,
    Number,
)
from dataclasses import dataclass
from more_itertools import peekable


@dataclass
class Token:
    token_type: str
    lexeme: str
    column: int
    line: int

    def __str__(self):
        return f"type: {self.token_type}, value: {self.lexeme}"


def peek(token: str, place: int):
    if place + 1 < len(token):
        return token[place + 1]
    raise StopIteration()


def scan_token(token: str, keyword: str):
    if token in type_mapping:
        token_type = type_mapping[token]
    elif token in symbol_types:
        token_type = symbol_types[token]
    elif token in variable_names:
        token_type = variable_names[token]
    elif (
        token[0].isdigit() or len(token) > 1 and token[0] == "-" and token[1].isdigit()
    ):
        if token.find(":") > -1:
            token_type = Time()
        else:
            token_type = Number()
    elif keyword == "strategy":
        token_type = Name()
    else:
        raise KeyError(f"Unknown key {token}")
    return token_type


def tokenize_strings(line, strings: Any, keyword: str) -> list[Token]:
    column = 0
    if isinstance(strings, list):
        tokens: list = []
        for lexeme in strings:
            if isinstance(lexeme, list):
                tokens.append(tokenize_strings(line, lexeme, keyword))
            else:
                try:
                    token_type = scan_token(lexeme, keyword)
                except:
                    printable_str = " ".join(strings)
                    raise ValueError(
                        f"Bad token, line {line}, column {column}, token {lexeme} \n\
                                {printable_str}\n\
                                {column*'-'}^{(column+len(lexeme))*'-'}^"
                    )
                tokens.append(Token(token_type, lexeme, column, line))
                column += len(lexeme)
    else:
        token_type = scan_token(strings, keyword)
        tokens = [Token(token_type, strings, column, line)]
    return tokens
