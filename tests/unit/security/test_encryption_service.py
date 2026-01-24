"""
Comprehensive unit tests for EncryptionService.

Tests encryption, decryption, hashing, and token generation with extensive
edge cases and error scenarios.
"""

import pytest
from cryptography.fernet import InvalidToken

from src.kortana.modules.security.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Comprehensive tests for encryption service."""

    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        service = EncryptionService(master_key="test_key_123")
        
        original_data = "sensitive_information"
        encrypted = service.encrypt(original_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original_data
        assert encrypted != original_data

    def test_encrypt_decrypt_bytes(self):
        """Test encryption and decryption with bytes input."""
        service = EncryptionService(master_key="test_key_123")
        
        original_data = b"binary_sensitive_data"
        encrypted = service.encrypt(original_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original_data.decode()

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        service = EncryptionService(master_key="test_key_123")
        
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == ""

    def test_encrypt_special_characters(self):
        """Test encryption with special characters."""
        service = EncryptionService(master_key="test_key_123")
        
        special_data = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        encrypted = service.encrypt(special_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == special_data

    def test_encrypt_unicode(self):
        """Test encryption with unicode characters."""
        service = EncryptionService(master_key="test_key_123")
        
        unicode_data = "Hello 世界 🌍 Привет"
        encrypted = service.encrypt(unicode_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == unicode_data

    def test_encrypt_large_data(self):
        """Test encryption of large data."""
        service = EncryptionService(master_key="test_key_123")
        
        large_data = "x" * 10000  # 10KB of data
        encrypted = service.encrypt(large_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == large_data

    def test_decrypt_invalid_data(self):
        """Test decryption with invalid data."""
        service = EncryptionService(master_key="test_key_123")
        
        with pytest.raises(Exception):  # Will raise InvalidToken or similar
            service.decrypt("invalid_base64_data")

    def test_different_keys_produce_different_ciphertexts(self):
        """Test that different keys produce different ciphertexts."""
        service1 = EncryptionService(master_key="key1")
        service2 = EncryptionService(master_key="key2")
        
        data = "test_data"
        encrypted1 = service1.encrypt(data)
        encrypted2 = service2.encrypt(data)
        
        assert encrypted1 != encrypted2

    def test_same_key_produces_different_ciphertexts(self):
        """Test that same key produces different ciphertexts for same data (due to IV)."""
        service = EncryptionService(master_key="test_key")
        
        data = "test_data"
        encrypted1 = service.encrypt(data)
        encrypted2 = service.encrypt(data)
        
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert service.decrypt(encrypted1) == data
        assert service.decrypt(encrypted2) == data

    def test_hash_data_sha256(self):
        """Test SHA256 hashing."""
        data = "test_data"
        hash1 = EncryptionService.hash_data(data, algorithm="sha256")
        hash2 = EncryptionService.hash_data(data, algorithm="sha256")
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_hash_data_sha512(self):
        """Test SHA512 hashing."""
        data = "test_data"
        hash_value = EncryptionService.hash_data(data, algorithm="sha512")
        
        assert len(hash_value) == 128  # SHA512 produces 128 hex characters

    def test_hash_data_md5(self):
        """Test MD5 hashing."""
        data = "test_data"
        hash_value = EncryptionService.hash_data(data, algorithm="md5")
        
        assert len(hash_value) == 32  # MD5 produces 32 hex characters

    def test_hash_data_invalid_algorithm(self):
        """Test hashing with invalid algorithm."""
        data = "test_data"
        
        with pytest.raises(ValueError) as exc_info:
            EncryptionService.hash_data(data, algorithm="invalid")
        
        assert "Unsupported algorithm" in str(exc_info.value)

    def test_hash_empty_string(self):
        """Test hashing empty string."""
        hash_value = EncryptionService.hash_data("", algorithm="sha256")
        
        # SHA256 of empty string is a known value
        assert hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_different_data_produces_different_hashes(self):
        """Test that different data produces different hashes."""
        hash1 = EncryptionService.hash_data("data1", algorithm="sha256")
        hash2 = EncryptionService.hash_data("data2", algorithm="sha256")
        
        assert hash1 != hash2

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = EncryptionService.generate_secure_token(32)
        token2 = EncryptionService.generate_secure_token(32)
        
        assert token1 != token2
        assert len(token1) == 64  # 32 bytes = 64 hex characters
        assert len(token2) == 64

    def test_generate_secure_token_different_lengths(self):
        """Test token generation with different lengths."""
        token_16 = EncryptionService.generate_secure_token(16)
        token_32 = EncryptionService.generate_secure_token(32)
        token_64 = EncryptionService.generate_secure_token(64)
        
        assert len(token_16) == 32  # 16 bytes = 32 hex chars
        assert len(token_32) == 64  # 32 bytes = 64 hex chars
        assert len(token_64) == 128  # 64 bytes = 128 hex chars

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        service = EncryptionService(master_key="test_key_123")
        
        original_dict = {
            "api_key": "secret123",
            "password": "mypassword",
            "token": "abc123xyz",
        }
        
        encrypted_dict = service.encrypt_dict(original_dict)
        decrypted_dict = service.decrypt_dict(encrypted_dict)
        
        assert decrypted_dict == original_dict
        # Ensure values are actually encrypted
        assert encrypted_dict["api_key"] != original_dict["api_key"]

    def test_encrypt_decrypt_dict_empty(self):
        """Test encryption of empty dictionary."""
        service = EncryptionService(master_key="test_key_123")
        
        original_dict = {}
        encrypted_dict = service.encrypt_dict(original_dict)
        decrypted_dict = service.decrypt_dict(encrypted_dict)
        
        assert decrypted_dict == original_dict

    def test_encrypt_decrypt_dict_with_complex_values(self):
        """Test dictionary encryption with complex values."""
        service = EncryptionService(master_key="test_key_123")
        
        original_dict = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
            "boolean": True,
        }
        
        encrypted_dict = service.encrypt_dict(original_dict)
        decrypted_dict = service.decrypt_dict(encrypted_dict)
        
        assert decrypted_dict == original_dict

    def test_no_master_key_generates_random_key(self):
        """Test that no master key generates a random key."""
        service1 = EncryptionService()
        service2 = EncryptionService()
        
        data = "test"
        encrypted1 = service1.encrypt(data)
        encrypted2 = service2.encrypt(data)
        
        # Different services with auto-generated keys should produce different results
        assert encrypted1 != encrypted2
        
        # Each should be able to decrypt its own data
        assert service1.decrypt(encrypted1) == data
        assert service2.decrypt(encrypted2) == data

    def test_derive_key_consistency(self):
        """Test that deriving key from same password produces same key."""
        service1 = EncryptionService(master_key="password123")
        service2 = EncryptionService(master_key="password123")
        
        data = "test_data"
        encrypted1 = service1.encrypt(data)
        
        # Service2 should be able to decrypt data from service1
        decrypted = service2.decrypt(encrypted1)
        assert decrypted == data

    def test_cross_service_decryption_fails_with_different_keys(self):
        """Test that decryption fails when using different keys."""
        service1 = EncryptionService(master_key="key1")
        service2 = EncryptionService(master_key="key2")
        
        data = "test_data"
        encrypted = service1.encrypt(data)
        
        # Service2 with different key should not be able to decrypt
        with pytest.raises(Exception):
            service2.decrypt(encrypted)
