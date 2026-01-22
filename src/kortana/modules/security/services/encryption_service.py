"""
Advanced encryption service for Kor'tana.
Provides encryption/decryption utilities for sensitive data.
"""

import base64
import hashlib
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, master_key: str | None = None):
        """
        Initialize encryption service.

        Args:
            master_key: Master encryption key. If None, generates a new key.
        """
        if master_key:
            self._key = self._derive_key(master_key)
        else:
            self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)

    @staticmethod
    def _derive_key(password: str, salt: bytes | None = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation. If None, uses fixed salt.

        Returns:
            Derived encryption key
        """
        if salt is None:
            # Use a fixed salt for consistency (in production, store salt securely)
            salt = b"kortana_security_salt_v1"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str | bytes) -> str:
        """
        Encrypt data.

        Args:
            data: Data to encrypt (string or bytes)

        Returns:
            Base64-encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode()

        encrypted = self._cipher.encrypt(data)
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted data as string
        """
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self._cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

    @staticmethod
    def hash_data(data: str, algorithm: str = "sha256") -> str:
        """
        Generate hash of data.

        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha512, md5)

        Returns:
            Hexadecimal hash string
        """
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate cryptographically secure random token.

        Args:
            length: Token length in bytes

        Returns:
            Hexadecimal token string
        """
        return os.urandom(length).hex()

    def encrypt_dict(self, data: dict[str, Any]) -> dict[str, str]:
        """
        Encrypt dictionary values.

        Args:
            data: Dictionary with string values to encrypt

        Returns:
            Dictionary with encrypted values
        """
        import json

        return {key: self.encrypt(json.dumps(value)) for key, value in data.items()}

    def decrypt_dict(self, encrypted_data: dict[str, str]) -> dict[str, Any]:
        """
        Decrypt dictionary values.

        Args:
            encrypted_data: Dictionary with encrypted values

        Returns:
            Dictionary with decrypted values
        """
        import json

        return {
            key: json.loads(self.decrypt(value)) for key, value in encrypted_data.items()
        }
