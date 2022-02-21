from typing import Any, Iterable
from more_itertools import peekable
from dataclasses import dataclass
import re
from src.common_types import keyword_mapping
from src.compiler.tokenizer import tokenize_strings

indentation_regex = re.compile(r"^\s*")
tokenize_regex = re.compile(r"[()]|(?<=')[^']+(?=')|[^,()\s^']+")


def indentation(line):
    m = re.match(indentation_regex, line)
    return len(m.group())


@dataclass
class DictParser:
    source: str

    def parse(self) -> dict:
        # split on newline and remove empty lines
        lines = (line for line in self.source.lower().split("\n") if line.strip())
        return self.parse_level(peekable(lines), min_indent=0)

    def parse_level(self, line_iter: peekable, min_indent: int, keyword="") -> Any:
        indent = indentation(line_iter.peek())
        result: dict = {}
        l: list = []
        if indent < min_indent:
            return result
        while line_iter and indentation(line_iter.peek()) == indent:
            line = next(line_iter)
            if re.findall(r":", line):
                items = [item.strip() for item in line.split(":", 1)]
                if not items[1]:
                    result[keyword_mapping[items[0]]] = self.parse_level(
                        line_iter, indent + 1, items[0]
                    )
                else:
                    if len(items[1:][0].split(" ")) > 1:
                        strings = re.findall(tokenize_regex, items[1:][0])
                        result[keyword_mapping[items[0]]] = tokenize_strings(
                            line, strings, items[0]
                        )
                    else:
                        strings = items[1:][0]
                        result[keyword_mapping[items[0]]] = tokenize_strings(
                            line, strings, items[0]
                        )
            else:
                # multiline list. remove ands and ors
                if re.findall(r"\sand", line):
                    line = re.sub(r"\sand", "", line)
                elif re.findall(r"\sor\n", line):
                    line = re.sub(r"\sor", "", line)
                l.append(re.findall(tokenize_regex, line))
                if not line_iter or indentation(line_iter.peek()) != indent:
                    return tokenize_strings(line, l, keyword)
        if line_iter and indentation(line_iter.peek()) > indent:
            raise ValueError("Improper Indentation")
        return result
