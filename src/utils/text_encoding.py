"""
Utility functions for text encoding and AI model interaction
"""

import base64


def encode_text_to_base64(input_text: str, encoding: str = "utf-8") -> str:
    """
    Encode input text to base64 format.

    Args:
        input_text (str): The text string to encode
        encoding (str): Text encoding to use (default: 'utf-8')

    Returns:
        str: Base64 encoded string

    Example:
        >>> encode_text_to_base64("Hello, World!")
        'SGVsbG8sIFdvcmxkIQ=='

        >>> encode_text_to_base64("Kor'tana AI Assistant")
        'S29yJ3RhbmEgQUkgQXNzaXN0YW50'
    """
    try:
        # Convert string to bytes using specified encoding
        text_bytes = input_text.encode(encoding)

        # Encode bytes to base64
        base64_bytes = base64.b64encode(text_bytes)

        # Convert base64 bytes back to string
        base64_string = base64_bytes.decode("ascii")

        return base64_string

    except Exception as e:
        raise ValueError(f"Failed to encode text to base64: {str(e)}") from e


def decode_base64_to_text(base64_string: str, encoding: str = "utf-8") -> str:
    """
    Decode base64 string back to original text.

    Args:
        base64_string (str): Base64 encoded string to decode
        encoding (str): Text encoding to use (default: 'utf-8')

    Returns:
        str: Decoded text string

    Example:
        >>> decode_base64_to_text('SGVsbG8sIFdvcmxkIQ==')
        'Hello, World!'
    """
    try:
        # Convert base64 string to bytes
        base64_bytes = base64_string.encode("ascii")

        # Decode base64 to original bytes
        text_bytes = base64.b64decode(base64_bytes)

        # Convert bytes back to string using specified encoding
        original_text = text_bytes.decode(encoding)

        return original_text

    except Exception as e:
        raise ValueError(f"Failed to decode base64 to text: {str(e)}") from e


def encode_file_to_base64(file_path: str) -> str:
    """
    Encode file content to base64 format.

    Args:
        file_path (str): Path to the file to encode

    Returns:
        str: Base64 encoded file content

    Example:
        >>> encode_file_to_base64("./data/sample.txt")
        'VGhpcyBpcyBhIHNhbXBsZSBmaWxlIGNvbnRlbnQ='
    """
    try:
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            base64_bytes = base64.b64encode(file_bytes)
            return base64_bytes.decode("ascii")

    except Exception as e:
        raise ValueError(f"Failed to encode file to base64: {str(e)}") from e


# Example usage and testing
if __name__ == "__main__":
    # Test basic text encoding
    test_text = "Hello, Kor'tana! This is a test message for base64 encoding."
    encoded = encode_text_to_base64(test_text)
    decoded = decode_base64_to_text(encoded)

    print(f"Original text: {test_text}")
    print(f"Base64 encoded: {encoded}")
    print(f"Decoded back: {decoded}")
    print(f"Encoding successful: {test_text == decoded}")

    # Test with special characters and Unicode
    unicode_text = "🤖 Kor'tana AI: Wisdom, Compassion, Truth 🌟"
    unicode_encoded = encode_text_to_base64(unicode_text)
    unicode_decoded = decode_base64_to_text(unicode_encoded)

    print("\nUnicode test:")
    print(f"Original: {unicode_text}")
    print(f"Encoded: {unicode_encoded}")
    print(f"Decoded: {unicode_decoded}")
    print(f"Unicode encoding successful: {unicode_text == unicode_decoded}")
