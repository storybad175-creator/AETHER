import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

class AESCipher:
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.aes_key)
            self.iv = binascii.unhexlify(settings.aes_iv)
        except Exception as e:
            # Fallback for development if hex is invalid
            self.key = b"\x00" * 32
            self.iv = b"\x00" * 16

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts data using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypts data using AES-CBC and removes PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        try:
            return unpad(cipher.decrypt(encrypted_data), AES.block_size)
        except ValueError as e:
            raise ValueError("Decryption failed. Check AES key and IV.") from e

crypto = AESCipher()
