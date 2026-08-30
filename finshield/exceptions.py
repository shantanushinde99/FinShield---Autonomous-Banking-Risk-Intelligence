class FinShieldError(Exception):
    """Base exception for all FinShield errors."""
    pass

class CustomerNotFoundError(FinShieldError):
    """Raised when a customer cannot be found."""
    def __init__(self, customer_id: str):
        super().__init__(f"Customer with ID {customer_id} not found.")
        self.customer_id = customer_id

class DataValidationError(FinShieldError):
    """Raised when data fails validation rules."""
    pass

class DatabaseConnectionError(FinShieldError):
    """Raised when the database connection fails."""
    pass
