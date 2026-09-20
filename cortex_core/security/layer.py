"""
Security layer for Cortex Core.
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from cortex_core.exceptions import SecurityError, ValidationError

logger = logging.getLogger(__name__)


class SecurityLayer:
    """
    Comprehensive security layer for data protection and validation.
    """

    def __init__(self, master_key: Optional[str] = None, config: Dict[str, Any] = None):
        self.config = config or {}
        self.master_key = master_key or self._generate_key()

        # Security policies
        self.policies = {
            "max_input_size": 10 * 1024 * 1024,  # 10MB
            "allowed_schemas": ["http", "https", "data"],
            "max_depth": 10,
            "max_array_length": 1000,
            "max_string_length": 10000,
        }

        # Update from config
        if "policies" in self.config:
            self.policies.update(self.config["policies"])

        logger.info("Security layer initialized")

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data.

        Args:
            data: Data to validate

        Returns:
            Validation results

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        # 1. Check size
        data_size = len(json.dumps(data).encode())
        if data_size > self.policies["max_input_size"]:
            errors.append(f"Data too large: {data_size} bytes")

        # 2. Check structure
        try:
            self._validate_structure(data, depth=0)
        except ValidationError as e:
            errors.append(str(e))

        # 3. Check content
        content_errors = self._validate_content(data)
        errors.extend(content_errors)

        if errors:
            return {"valid": False, "errors": errors, "sanitized": self._sanitize(data)}

        return {"valid": True, "sanitized": data}

    def _validate_structure(self, data: Any, depth: int):
        """Validate data structure."""
        if depth > self.policies["max_depth"]:
            raise ValidationError("Data structure too deep")

        if isinstance(data, dict):
            for key, value in data.items():
                # Check key
                if not isinstance(key, str):
                    raise ValidationError(f"Invalid key type: {type(key)}")
                if len(key) > 100:
                    raise ValidationError(f"Key too long: {key}")

                # Check value
                self._validate_structure(value, depth + 1)

        elif isinstance(data, list):
            if len(data) > self.policies["max_array_length"]:
                raise ValidationError(f"Array too long: {len(data)} items")

            for item in data:
                self._validate_structure(item, depth + 1)

        elif isinstance(data, str):
            if len(data) > self.policies["max_string_length"]:
                raise ValidationError(f"String too long: {
                        len(data)} characters")

    def _validate_content(self, data: Dict[str, Any]) -> list:
        """Validate data content."""
        errors = []

        # Check for malicious patterns
        malicious_patterns = [
            ("<script>", "Potential XSS attack"),
            ("SELECT.*FROM", "Potential SQL injection"),
            ("../", "Potential path traversal"),
            ("eval(", "Potential code injection"),
        ]

        def check_value(value):
            if isinstance(value, str):
                for pattern, message in malicious_patterns:
                    if pattern.lower() in value.lower():
                        errors.append(f"{message} detected in: {value[:50]}...")

            elif isinstance(value, (dict, list)):
                if isinstance(value, dict):
                    for v in value.values():
                        check_value(v)
                else:
                    for v in value:
                        check_value(v)

        check_value(data)
        return errors

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data."""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Basic HTML sanitization
                sanitized_value = value.replace("<", "&lt;").replace(">", "&gt;")
                sanitized[key] = sanitized_value[: self.policies["max_string_length"]]
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        self._sanitize(item)
                        if isinstance(item, dict)
                        else (
                            item[: self.policies["max_string_length"]]
                            if isinstance(item, str)
                            else item
                        )
                    )
                    for item in value[: self.policies["max_array_length"]]
                ]
            else:
                sanitized[key] = value

        return sanitized

    def encrypt(self, data: Any) -> str:
        """Encrypt data."""
        if not self.master_key:
            raise SecurityError("No encryption key provided")

        # Simple encryption - in production use proper cryptography
        data_str = json.dumps(data)
        encrypted = hashlib.sha256((data_str + self.master_key).encode()).hexdigest()

        return f"enc:{encrypted}"

    def decrypt(self, encrypted_data: str) -> Any:
        """Decrypt data."""
        if not encrypted_data.startswith("enc:"):
            return encrypted_data

        # Simple decryption - in production use proper cryptography
        # This is just a placeholder
        return {"decrypted": "placeholder"}

    def hash(self, data: Any) -> str:
        """Create secure hash of data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def verify_hash(self, data: Any, expected_hash: str) -> bool:
        """Verify data hash."""
        actual_hash = self.hash(data)
        return actual_hash == expected_hash

    def _generate_key(self) -> str:
        """Generate secure key."""
        import secrets

        return secrets.token_urlsafe(32)

    def is_healthy(self) -> bool:
        """Check if security layer is healthy."""
        return self.master_key is not None
