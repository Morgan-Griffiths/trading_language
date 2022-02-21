from src.interpreter.interpreter import Interpreter
import datetime


def test_lazy_eval_functions1(interpreter: Interpreter):
    res = interpreter.context.get_value("OPEX")
    print(res)


def test_lazy_eval_functions2(interpreter: Interpreter):
    res = interpreter.context.get_value("TODAY")
    print(res)


def test_lazy_eval_functions3(interpreter: Interpreter):
    res = interpreter.context.get_value("DISTANCE_TO_OPEX")
    print(res)


def test_lazy_eval_functions4(interpreter: Interpreter):
    res = interpreter.context.get_value("PREVIOUS_OPEX")
    print(res)


def test_lazy_eval_functions5(interpreter: Interpreter):
    res = interpreter.context.get_value("DAYS_UNTIL_OPEX")
    print(res)


def test_lazy_eval_functions6(interpreter: Interpreter):
    res = interpreter.context.get_value("atm_option")
    assert res["putCall"] == "CALL"


def test_lazy_eval_functions7(interpreter: Interpreter):
    print(interpreter.context.function_mapping["SPY"])
    res = interpreter.context.get_value("SPY_SIGMA")
    print(res)


def test_lazy_eval_functions8(interpreter: Interpreter):
    res = interpreter.context.get_value("DAYS_UNTIL_OPEX")
    print(res)


def test_lazy_eval_functions9(interpreter: Interpreter):
    res = interpreter.context.get_value("NET_POSITION")
    print(res)


def test_lazy_eval_functions10(interpreter: Interpreter):
    res = interpreter.context.get_value("SPY_20_DAY_MEAN")
    print(res)


def test_strike_expr(interpreter: Interpreter):
    expr = ["-", "^DAYS_UNTIL_OPEX", 3]
    res = interpreter.lazy_s_parser(expr)
    print(res)
    assert res is not None


def test_strike_expr1(interpreter: Interpreter):
    expr = ["*", "^SPY", 0.006]
    res = interpreter.lazy_s_parser(expr)
    print(res)
    assert res is not None


def test_strike_expr2(interpreter: Interpreter):
    expr = [["*", "^SPY", 0.006], ["-", "^DAYS_UNTIL_OPEX", 3]]
    res = interpreter.lazy_s_parser(expr)
    print(res)
    assert res is not None


def test_strike_expr3(interpreter: Interpreter):
    expr = [
        "round",
        ["-", "^SPY", ["*", ["*", "^SPY", 0.006], ["-", "^DAYS_UNTIL_OPEX", 3]]],
    ]
    res = interpreter.lazy_s_parser(expr)
    print(res)
    assert res is not None


def test_symbol_filter(interpreter: Interpreter):
    expr = [
        "filter_csv",
        "stock_fundamentals",
        ["list", "None"],
        ["list", "Volume"],
        "@symbols",
        ">",
        2000000.0,
    ]
    interpreter.variables["symbols"] = ["TSLA"]
    res = interpreter.lazy_s_parser(expr)
    print(res)
    assert res is not None
