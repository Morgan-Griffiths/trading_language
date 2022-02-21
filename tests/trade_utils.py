from src.utils import add_to_dict


def update_variables_and_verify_outcome(
    interpreter, trade, door, outcome: bool, passFilter: bool
):
    print("update_variables_and_verify_outcome", door, trade[door])
    interpreter.record_local_values(trade["position_description"])
    direction = "open" if door == "open_position" else "close"
    interpreter.variables["tradeDirection"] = direction
    interpreter.variables["strategy"] = trade["strategy"]
    if "when" in trade[door]:
        condition_filter = trade[door]["when"]
        operand = list(condition_filter.keys())[0]
        conditions = condition_filter[operand]
        values = return_variable_values(interpreter, conditions)
        print("values", values)
        assign_variables(interpreter, values, outcome)
        print("variables", interpreter.variables)
        check_evaluation(interpreter, operand, outcome, conditions)
        print("post eval")
        if passFilter and "symbol_filter" in trade[door]:
            interpreter.load_symbol_pool(trade)
            print("post load_symbol_pool")
            set_symbol_filter_values(interpreter, trade[door]["symbol_filter"], outcome)
            print("post set_symbol_filter_values")


def testing_parser(interpreter, values, expr):
    if isinstance(expr, list):
        assert isinstance(expr[1], str)
        print("expr", expr)
        right_value = interpreter.lazy_s_parser(expr[2])
        print("right_value", right_value)
        add_to_dict(values, expr[0], expr[1], right_value)
    return values


def check_evaluation(interpreter, operand, outcome, conditions):
    evaluation = [interpreter.lazy_s_parser(condition) for condition in conditions]
    print("evaluation", evaluation)
    if operand == "or":
        assert any(evaluation) == outcome
    elif operand == "and":
        assert all(evaluation) == outcome


def assign_variables(interpreter, values, outcome):
    position = -2 if outcome == True else -1
    for k, v in values.items():
        if k[0] == "^":
            interpreter.context.update_value(k[1:], v[position])
        elif k[0] == "@":
            interpreter.variables[k[1:]] = v[position]
        else:
            raise ValueError("Left should be var or context")


def return_variable_values(interpreter, conditions):
    values = {}
    for condition in conditions:
        testing_parser(interpreter, values, condition)
    return values


def set_symbol_filter_values(interpreter, conditions, passFail):
    interpreter.load_portfolio()
    interpreter.parse_filter(conditions)
    print(
        "number of symbols",
        len(interpreter.variables["symbols"]),
    )
    if (
        len(interpreter.variables["symbols"]) == 0
        and passFail == True
        or len(interpreter.variables["symbols"]) > 0
        and passFail == False
    ):
        print("set_symbol_filter_values conditions, passFail", conditions, passFail)
        interpreter.variables["symbols"] = ["TSLA"]
        for condition in conditions:
            interpreter.update_csv_values(condition, passFail)
