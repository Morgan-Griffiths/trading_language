from src.compiler.tokenizer import Token


def is_member(value: Token, classes: list):
    return any([isinstance(value.token_type, cls) for cls in classes])
