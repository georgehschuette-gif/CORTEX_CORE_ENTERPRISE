"""
JWT token management for authentication.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt


class JWTManager:
    """
    JSON Web Token manager for authentication.
    """

    def __init__(
        self, secret_key: str = None, algorithm: str = "HS256", expiry_hours: int = 24
    ):
        """
        Initialize JWT manager.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm
            expiry_hours: Token expiry time in hours
        """
        self.secret_key = secret_key or "default-secret-key-change-in-production"
        self.algorithm = algorithm
        self.expiry_hours = expiry_hours

    def create_token(self, payload: Dict[str, Any]) -> str:
        """
        Create a JWT token.

        Args:
            payload: Token payload

        Returns:
            JWT token string
        """
        # Add standard claims
        now = datetime.utcnow()
        payload.update(
            {
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=self.expiry_hours)).timestamp()),
                "iss": "cortex-core",
            }
        )

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check expiry
            if payload.get("exp"):
                now = int(time.time())
                if now > payload["exp"]:
                    raise jwt.ExpiredSignatureError("Token has expired")

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidSignatureError:
            raise jwt.InvalidTokenError("Invalid token signature")
        except Exception as e:
            raise jwt.InvalidTokenError(f"Invalid token: {e}")

    def refresh_token(self, token: str) -> str:
        """
        Refresh a JWT token.

        Args:
            token: Current JWT token

        Returns:
            New JWT token with extended expiry
        """
        # Decode current token
        payload = self.decode_token(token)

        # Remove expiry claims (will be set again)
        payload.pop("exp", None)
        payload.pop("iat", None)

        # Create new token
        return self.create_token(payload)

    def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            True if valid, False otherwise
        """
        try:
            self.decode_token(token)
            return True
        except jwt.InvalidTokenError:
            return False

    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get information about a token.

        Args:
            token: JWT token string

        Returns:
            Token information
        """
        payload = self.decode_token(token)

        now = int(time.time())
        expired = now > payload.get("exp", 0)

        return {
            "valid": not expired,
            "expired": expired,
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
            "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
            "issuer": payload.get("iss"),
            "subject": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "roles": payload.get("roles", []),
        }
