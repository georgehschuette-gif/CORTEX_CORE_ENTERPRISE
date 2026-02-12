"""
Custom exceptions for Cortex Core.
"""


class CortexError(Exception):
    """Base exception for all Cortex Core errors."""
    pass


class ConfigurationError(CortexError):
    """Configuration-related errors."""
    pass


class SecurityError(CortexError):
    """Security-related errors."""
    pass


class ValidationError(CortexError):
    """Data validation errors."""
    pass


class ProcessingError(CortexError):
    """Intelligence processing errors."""
    pass


class DistributedError(CortexError):
    """Distributed system errors."""
    pass


class CircuitBreakerOpen(CortexError):
    """Circuit breaker is open."""
    pass


class AuthenticationError(SecurityError):
    """Authentication failures."""
    pass


class AuthorizationError(SecurityError):
    """Authorization failures."""
    pass


class EncryptionError(SecurityError):
    """Encryption/decryption failures."""
    pass


class DatabaseError(CortexError):
    """Database operation errors."""
    pass


class ModelError(CortexError):
    """Model-related errors."""
    pass


class MemoryError(CortexError):
    """Memory system errors."""
    pass
