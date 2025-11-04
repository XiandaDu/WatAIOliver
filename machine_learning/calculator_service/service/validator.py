import re
from typing import Tuple

VALID_EXPRESSION_PATTERN = re.compile(
    r"^[a-zA-Z0-9\+\-\*\/\(\)\[\]\{\}\.\,\s\=\>\<\!\~\%\:]+$"
)


def validate_expression(expr: str) -> Tuple[bool, str]:
    # Length check
    if len(expr) > 500:
        return False, "Expression is too long (max 500 characters)"

    # System attribute check (check before character check for better error messages)
    if "__" in expr or "import" in expr:
        return False, "Expression contains illegal system attribute access"

    # Character check
    if not VALID_EXPRESSION_PATTERN.match(expr):
        return False, "Expression contains illegal characters"

    return True, ""
