class QueryException(Exception):
    pass


class NoMatchFound(QueryException):
    pass


class MultipleMatchesFound(QueryException):
    pass


class InvalidKeyException(QueryException):
    pass


class InvalidObjectIdException(QueryException):
    pass


class InvalidFieldTypeException(QueryException):
    pass
