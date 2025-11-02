"""
Calculator Service Error Types

Define all exception types that may be raised by the calculator service.
Error types required by the specification:
- TIMEOUT: Computation timeout
- PARSE_ERROR: Expression parsing error
- MISSING_PARAM: Missing required parameter
- COMPUTE_ERROR: Computation error (e.g., division by zero)
"""


class CalculatorError(Exception):
    """
    Base class for calculator errors
    
    Args:
        message: Error message
        mode: Computation mode (optional, for debugging)
    """
    def __init__(self, message: str, mode: str = None):
        self.message = message
        self.mode = mode
        self.error_type = "CALCULATOR_ERROR"
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class ParseError(CalculatorError):
    """
    Expression parsing error
    
    Raised when an expression cannot be parsed by SymPy.
    Usually due to syntax errors or illegal functions.
    """
    def __init__(self, message: str, mode: str = None):
        super().__init__(f"PARSE_ERROR: {message}", mode)
        self.error_type = "PARSE_ERROR"


class MissingParameterError(CalculatorError):
    """
    Missing required parameter error
    
    Raised when a computation mode requires a parameter that is not provided.
    For example: differentiate/integrate/solve require the 'var' parameter.
    """
    def __init__(self, message: str, mode: str = None):
        super().__init__(f"MISSING_PARAM: {message}", mode)
        self.error_type = "MISSING_PARAM"


class ComputationError(CalculatorError):
    """
    Computation error
    
    Raised when an error occurs during computation (e.g., division by zero, invalid operation).
    """
    def __init__(self, message: str, mode: str = None):
        super().__init__(f"COMPUTE_ERROR: {message}", mode)
        self.error_type = "COMPUTE_ERROR"


class TimeoutError(CalculatorError):
    """
    Computation timeout error
    
    Raised when computation exceeds 3 seconds.
    """
    def __init__(self, message: str = "Computation timed out after 3 seconds", mode: str = None):
        super().__init__(f"TIMEOUT: {message}", mode)
        self.error_type = "TIMEOUT"