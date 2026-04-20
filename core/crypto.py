import binascii
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

logger = logging.getLogger(__name__)

class AESCipher:
    """
    AES-CBC encryption and decryption using PKCS7 padding.
    Key and IV are sourced from the application settings.

    HOW TO OBTAIN AES KEYS:
    1. Extract Free Fire APK (OB53).
    2. Analyze libil2cpp.so or libunity.so using Ghidra/IDA.
    3. Search for AES-CBC initialization constants.
    4. Update AES_KEY (32-byte hex) and AES_IV (16-byte hex) in .env.
    """
    def __init__(self):
        try:
            # Sourced from .env via settings.py
            # Placeholder values in settings.py will trigger fallback or fail if invalid hex
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except (binascii.Error, ValueError) as e:
            logger.warning(f"Invalid AES Hex keys in .env: {e}. Using fallback for development.")
            # Fallback for development/testing only
            self.key = settings.AES_KEY.encode('utf-8').ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode('utf-8').ljust(16, b'\0')[:16]

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(raw, AES.block_size))

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        try:
            return unpad(cipher.decrypt(enc), AES.block_size)
        except ValueError as e:
            # This usually indicates a wrong key/IV or corrupted data
            raise ValueError(f"Decryption failed (padding error). Check AES_KEY and AES_IV. Error: {e}")

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
