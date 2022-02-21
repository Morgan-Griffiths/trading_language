from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class LazyFunction:
    keyword: str
    evaluate: Callable


def resolve_dependencies(context, key):
    func = context.func_lookup(key)
    value = func.evaluate(context)
    context.update_value(func.keyword, value)
    return value
