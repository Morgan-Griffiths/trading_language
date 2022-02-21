def add_aggs(aggs: list[str], reverse=True, axis=None) -> str:
    agg_str = ""
    if aggs:
        aggs = reversed(aggs) if reverse else aggs
        for agg in aggs:
            if agg != "None":
                assert agg in ["mean", "abs", "max", "min"]
                agg_str += "." + agg
                if axis and agg != "abs":
                    agg_str += f"(axis={axis})"
                else:
                    agg_str += "()"
    return agg_str


class PandasBuilder:
    def __init__(self) -> None:
        self.df_name = None
        self.initial_selection = None
        self.column_select: list = []
        self.final_column_select: str = ""
        self.final_boolean_op = ""
        self.values = None
        self.equals = None

    def set_name(self, name):
        self.df_name = name
        return self

    def add_initial_column_select(self, column, value):
        expr = f"{self.df_name}[{self.df_name}[{column}]=={value}]"
        self.initial_selection = expr
        return self

    def add_column_select_symbol_isin(self):
        assert self.df_name is not None
        expr = "({df}['symbol'].isin(symbols))"
        expr = expr.format(df=self.df_name)
        self.column_select.append(expr)
        return self

    def add_column_select_amount_comparison(
        self, op: str, amount: str, columns=[], aggs=[], agg_reversed=True, axis=None
    ):
        """option param aggs. operations to act on the columns before comparison"""
        if len(columns) > 1:
            columns = [columns]
        expr = "({df}{columns}{agg} {op} {amount})"
        agg_str = add_aggs(aggs, agg_reversed, axis)
        expr = expr.format(
            df=self.df_name, op=op, columns=columns, agg=agg_str, amount=amount
        )
        if self.column_select:
            self.column_select.append(" & ")
        self.column_select.append(expr)
        return self

    def add_final_column_select(
        self, columns: list, aggs=[], agg_reversed=False, axis=None
    ):
        assert isinstance(columns, list)
        if len(columns) > 1:
            columns = [columns]
        expr = "{columns}{agg}"
        agg_str = add_aggs(aggs, agg_reversed, axis)
        expr = expr.format(columns=columns, agg=agg_str)
        self.final_column_select = expr
        return self

    def add_final_boolean_op(self, op, amount):
        self.final_boolean_op = f" {op} {amount}"
        return self

    def add_values(self):
        self.values = True
        return self

    def add_equals(self, value):
        self.equals = value
        return self

    def build(self):
        # if self.initial_selection:
        #     result = self.initial_selection
        # else:
        #     result = f"{self.df_name}"
        result = f"{self.df_name}[{''.join(self.column_select)}]"
        if self.final_column_select:
            result += str(self.final_column_select)
        if self.values:
            result += ".values"
        if self.final_boolean_op:
            result += self.final_boolean_op
        if self.equals:
            result += f"={self.equals}"
        return result.strip()
