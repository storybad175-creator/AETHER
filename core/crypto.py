import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

class AESCipher:
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except binascii.Error:
            # Fallback for development if keys are not proper hex
            self.key = settings.AES_KEY.encode().ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode().ljust(16, b'\0')[:16]

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, encrypted_data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        try:
            return unpad(cipher.decrypt(encrypted_data), AES.block_size)
        except ValueError as e:
            raise ValueError("Decryption failed. Possible key rotation or invalid data.") from e

cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
