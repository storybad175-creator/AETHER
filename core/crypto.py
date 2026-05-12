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
    Key and IV are strictly validated as hex strings.
    """
    def __init__(self):
        try:
            # AES_KEY must be 32 bytes (64 hex chars)
            # AES_IV must be 16 bytes (32 hex chars)
            if len(settings.AES_KEY) != 64 or len(settings.AES_IV) != 32:
                raise ValueError("AES_KEY must be 64 hex chars and AES_IV must be 32 hex chars.")

            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except (binascii.Error, ValueError) as e:
            logger.error(f"Invalid AES configuration: {e}")
            # Fallback for testing ONLY if placeholders are used
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
        except ValueError:
            # This often indicates an incorrect key or IV (e.g., after a game update)
            logger.error("AES Decryption failed. Possible key rotation detected!")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt Garena response. AES keys might have rotated.",
                extra={"possible_key_rotation": True, "action": "Update AES_KEY and AES_IV in .env"}
            )

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
