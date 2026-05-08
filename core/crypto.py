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
    Key and IV are sourced from the application settings.
    """
    def __init__(self):
        try:
            # Garena uses 32-byte (256-bit) keys and 16-byte IVs
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)

            if len(self.key) != 32:
                logger.warning(f"AES_KEY length is {len(self.key)} bytes. Expected 32 bytes.")
            if len(self.iv) != 16:
                logger.warning(f"AES_IV length is {len(self.iv)} bytes. Expected 16 bytes.")

        except (binascii.Error, ValueError) as e:
            logger.error(f"Failed to initialize AESCipher: {e}")
            # Fallback for testing with placeholders
            self.key = settings.AES_KEY.encode('utf-8').ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode('utf-8').ljust(16, b'\0')[:16]

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            return cipher.encrypt(pad(raw, AES.block_size))
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise FFError(ErrorCode.DECODE_ERROR, "Failed to encrypt request payload.")

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            decrypted = cipher.decrypt(enc)
            return unpad(decrypted, AES.block_size)
        except (ValueError, KeyError) as e:
            # unpad raises ValueError if padding is incorrect
            logger.error(f"Decryption/Unpadding failed: {e}")
            logger.warning("!!! AES KEY ROTATION DETECTED OR INVALID KEYS !!!")
            logger.warning("Please update AES_KEY and AES_IV in your .env file.")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Decryption failed. This often indicates an AES key rotation by Garena.",
                extra={
                    "possible_key_rotation": True,
                    "action": "Update AES_KEY and AES_IV in .env"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected decryption error: {e}")
            raise FFError(ErrorCode.DECODE_ERROR, f"Decryption failed: {str(e)}")

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
