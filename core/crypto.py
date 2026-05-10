import binascii
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AESCipher:
    """
    AES-CBC encryption and decryption using PKCS7 padding.
    Key and IV are strictly sourced from the application settings hex strings.
    """
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)

            if len(self.key) != 32:
                raise ValueError(f"AES_KEY must be 32 bytes (64 hex chars), got {len(self.key)}")
            if len(self.iv) != 16:
                raise ValueError(f"AES_IV must be 16 bytes (32 hex chars), got {len(self.iv)}")

        except (binascii.Error, ValueError) as e:
            logger.error(f"Invalid AES configuration: {e}")
            # We don't raise here to allow the app to start, but encrypt/decrypt will fail
            self.key = None
            self.iv = None

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        if not self.key or not self.iv:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "AES encryption keys not properly configured in .env")

        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(raw, AES.block_size))

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        if not self.key or not self.iv:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "AES decryption keys not properly configured in .env")

        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            return unpad(cipher.decrypt(enc), AES.block_size)
        except (ValueError, KeyError) as e:
            # unpad raises ValueError if padding is incorrect
            logger.error(f"AES decryption failed: {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt Garena response. Possible AES key rotation.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
