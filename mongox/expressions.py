import collections
import typing

from mongox.index import Order

if typing.TYPE_CHECKING:  # pragma: no cover
    from mongox.fields import ModelField


class QueryExpression:
    """
    Dataclass holding Query crtieria
    """

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
        # Using defaultdict to allow {key: {}} for queries
        compiled_expressions: typing.Dict[typing.Any, dict] = collections.defaultdict(
            dict
        )
        for expr in expressions:
            for key, value in expr.compile().items():
                compiled_expressions[key].update(value)
        return compiled_expressions

    @classmethod
    def unpack(self, d: typing.Dict[str, typing.Any]) -> "typing.List[QueryExpression]":
        """
        Unpack dictionary to a list of QueryExpression.

        For now works only for the following queries:
            d = {"name": "value"}
            d = {"year": {"$gt": 1990}}
            d = {"year": {"$gt": 1990, "$lt": 2000}}
        """

        expressions: typing.List[QueryExpression] = []

        for key, value in d.items():
            if isinstance(value, dict):
                for op, v in value.items():
                    expr = QueryExpression(key=key, operator=op, value=v)
                    expressions.append(expr)
            else:
                expr = QueryExpression(key=key, operator="$eq", value=value)
                expressions.append(expr)

        return expressions


class SortExpression:
    """
    Dataclass holding Sort criteria
    """

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
