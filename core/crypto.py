import binascii
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

logger = logging.getLogger(__name__)

class AESCipher:
    """
    AES-CBC encryption and decryption using PKCS7 padding.
    Key and IV are community-extracted constants from APK analysis.

    EXTRACTION GUIDE:
    1. Decompile Free Fire APK (using JADX or apktool).
    2. Search for 'MajorLogin' or 'X-Garena-OB' to find the networking layer.
    3. Look for AES/CBC/PKCS7Padding initialization in libil2cpp.so or libunity.so.
    4. Community sources (GitHub, Discord) usually maintain the latest Hex keys for each OB update.
    """
    def __init__(self):
        try:
            # Keys must be 32 bytes (AES-256) or 16 bytes (AES-128). Garena typically uses 256.
            # IV must be 16 bytes.
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except binascii.Error as e:
            logger.error(f"Failed to unhexlify AES_KEY or AES_IV: {e}")
            # Fallback for development/testing only
            self.key = settings.AES_KEY.encode('utf-8').ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode('utf-8').ljust(16, b'\0')[:16]
            logger.warning("Using fallback UTF-8 encoded keys. Decryption may fail on real payloads.")

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(raw, AES.block_size))

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            decrypted = cipher.decrypt(enc)
            return unpad(decrypted, AES.block_size)
        except (ValueError, KeyError) as e:
            # Usually happens if the key/IV is wrong or payload is corrupted
            logger.error(f"AES decryption or unpadding failed: {e}")
            raise ValueError("Decryption failed. Check AES_KEY and AES_IV in .env.")

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    """Public helper for AES encryption."""
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    """Public helper for AES decryption."""
    return cipher.decrypt(data)
