import re


def normalize_class_name(name: str) -> str:
    underscored = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", underscored).lower()
