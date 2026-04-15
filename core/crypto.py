import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import settings

class AESCipher:
    def __init__(self):
        # Keys and IVs are expected to be hex-encoded in settings
        try:
            self.key = bytes.fromhex(settings.AES_KEY)
            self.iv = bytes.fromhex(settings.AES_IV)
        except ValueError:
            # Fallback for placeholder strings in .env.example
            self.key = b"\x00" * 32
            self.iv = b"\x00" * 16

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data, AES.block_size)
        return cipher.encrypt(padded_data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_data = cipher.decrypt(encrypted_data)
        return unpad(decrypted_data, AES.block_size)

cipher = AESCipher()
