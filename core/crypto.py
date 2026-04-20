import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

class AESCipher:
    """
    AES-CBC encryption and decryption using PKCS7 padding.
    Key and IV are sourced from the application settings.
    """
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except binascii.Error:
            # Fallback for testing or if keys are not hex
            self.key = settings.AES_KEY.encode('utf-8').ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode('utf-8').ljust(16, b'\0')[:16]

    def encrypt(self, raw: bytes) -> bytes:
        """Encrypts raw bytes using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(raw, AES.block_size))

    def decrypt(self, enc: bytes) -> bytes:
        """Decrypts encrypted bytes using AES-CBC and removes PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(enc), AES.block_size)

# Singleton instance
cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
