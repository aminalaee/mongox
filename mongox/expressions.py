import typing

from mongox.index import Order

if typing.TYPE_CHECKING:  # pragma: no cover
    from mongox.fields import ModelField


class QueryExpression:
    def __init__(
        self, key: typing.Union[str, "ModelField"], operator: str, value: typing.Any
    ) -> None:
        if not isinstance(key, str):
            key = key.alias
        self.key = key
        self.operator = operator
        self.value = value

    def compile(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        """
        Compile QueryExpression to a Dict as MongoDB expects.
        """
        return {self.key: {self.operator: self.value}}

    @classmethod
    def compile_many(
        cls, expressions: typing.List["QueryExpression"]
    ) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        compiled_expressions = {}
        for expr in expressions:
            compiled_expressions.update(expr.compile())
        return compiled_expressions

    @classmethod
    def unpack(self, d: typing.Dict[str, typing.Any]) -> "QueryExpression":
        """
        Unpack dictionary to QueryExpression.

        For now works only for the following queries:
            d = {"name": "value"}
            d = {"year": {"$gt": 1990}}
        """

        key = list(d.keys())[0]
        value = list(d.values())[0]

        if isinstance(value, dict):
            operator = list(value.keys())[0]
            v = list(value.values())[0]
            return QueryExpression(key, operator, v)
        else:
            return QueryExpression(key, "$eq", value)


class SortExpression:
    def __init__(self, key: typing.Union[str, "ModelField"], direction: Order) -> None:
        if not isinstance(key, str):
            key = key.alias
        self.key = key
        self.direction = direction

    def compile(self) -> typing.Tuple[str, Order]:
        """
        compile SortExpression to a Tuple[str, direction] as MongoDB expects.
        """

        return (self.key, self.direction)
