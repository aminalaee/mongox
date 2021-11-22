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
        self.key = key if isinstance(key, str) else key.alias
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
        compiled_dicts: typing.Dict[typing.Any, dict] = collections.defaultdict(dict)
        compiled_lists: typing.Dict[typing.Any, list] = collections.defaultdict(list)

        for expr in expressions:
            for key, value in expr.compile().items():
                # Logical operators need a {"$or": [...]} query
                if key in ["$and", "$or"]:
                    list_value = value.get(key, value.get("$eq"))
                    assert isinstance(list_value, (list, tuple))
                    values = [
                        v.compile() if isinstance(v, QueryExpression) else v
                        for v in list_value
                    ]
                    compiled_lists[key] = values
                else:
                    compiled_dicts[key].update(value)

        return {**compiled_dicts, **compiled_lists}

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
        self.key = key if isinstance(key, str) else key.alias
        self.direction = direction

    def compile(self) -> typing.Tuple[str, Order]:
        """
        compile SortExpression to a Tuple[str, direction] as MongoDB expects.
        """

        return (self.key, self.direction)
