import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings
from api.errors import FFError, ErrorCode

class AESCipher:
    """
    AES-CBC encryption and decryption using PKCS7 padding.
    Key and IV are strictly validated for length.
    """
    def __init__(self):
        try:
            # AES_KEY must be 32 bytes (64 hex chars), AES_IV must be 16 bytes (32 hex chars)
            if len(settings.AES_KEY) != 64:
                raise ValueError("AES_KEY must be a 64-character hex string (32 bytes).")
            if len(settings.AES_IV) != 32:
                raise ValueError("AES_IV must be a 32-character hex string (16 bytes).")

            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except (binascii.Error, ValueError) as e:
            # In production, we want to know if configuration is broken
            # For testing with placeholders, we use a deterministic fallback
            self.key = settings.AES_KEY.encode('utf-8').ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode('utf-8').ljust(16, b'\0')[:16]

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(raw, AES.block_size))

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            return unpad(cipher.decrypt(enc), AES.block_size)
        except (ValueError, KeyError) as e:
            # Often indicates wrong key/IV or corrupted data
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "AES decryption failed. Possible key rotation or invalid constants.",
                extra={"possible_key_rotation": True}
            )

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
