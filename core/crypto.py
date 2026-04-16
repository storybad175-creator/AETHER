import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

class AESCipher:
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except Exception:
            # Fallback for placeholder or invalid hex
            self.key = b"\x00" * 32
            self.iv = b"\x00" * 16

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts data using AES-CBC with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data, AES.block_size)
        return cipher.encrypt(padded_data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypts data using AES-CBC and removes PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_data = cipher.decrypt(encrypted_data)
        return unpad(decrypted_data, AES.block_size)

aes_cipher = AESCipher()
