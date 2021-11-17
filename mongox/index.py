import enum
import typing

import pymongo


class Order(int, enum.Enum):
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING


class IndexType(str, enum.Enum):
    GEO2D = pymongo.GEO2D
    GEOSPHERE = pymongo.GEOSPHERE
    HASHED = pymongo.HASHED
    TEXT = pymongo.TEXT


class Index(pymongo.IndexModel):
    """
    MongoDB Index
    """

    def __init__(
        self,
        key: str = None,
        keys: typing.List[
            typing.Union[typing.Tuple[str, Order], typing.Tuple[str, IndexType]]
        ] = None,
        name: str = None,
        background: bool = False,
        unique: bool = False,
        sparse: bool = False,
        **kwargs: typing.Any,
    ) -> None:
        keys = [(key, Order.ASCENDING)] if key else keys or []
        self.name = name or "_".join([key[0] for key in keys])
        self.unique = unique

        kwargs["name"] = self.name
        kwargs["background"] = background
        kwargs["sparse"] = sparse
        kwargs["unique"] = unique
        return super().__init__(keys, **kwargs)
