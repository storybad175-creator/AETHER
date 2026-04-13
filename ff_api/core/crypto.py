import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from ff_api.config.settings import settings

class AESCipher:
    def __init__(self):
        # We expect hex strings from settings
        try:
            self.key = bytes.fromhex(settings.AES_KEY)
            self.iv = bytes.fromhex(settings.AES_IV)
        except ValueError:
            # Fallback to dummy for tests or if not provided
            self.key = b"0123456789abcdef0123456789abcdef"
            self.iv = b"0123456789abcdef"

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        return ct_bytes

    def decrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        pt = unpad(cipher.decrypt(data), AES.block_size)
        return pt

cipher = AESCipher()

def aes_encrypt(data: bytes) -> bytes:
    return cipher.encrypt(data)

def aes_decrypt(data: bytes) -> bytes:
    return cipher.decrypt(data)
