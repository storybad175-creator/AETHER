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
            # Fallback for when real keys aren't provided in .env
            self.key = b"\x00" * 32
            self.iv = b"\x00" * 16

    def encrypt(self, data: bytes) -> bytes:
        """AES-CBC encrypt with PKCS7 padding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data, AES.block_size)
        return cipher.encrypt(padded_data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """AES-CBC decrypt with PKCS7 unpadding."""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_data = cipher.decrypt(encrypted_data)
        return unpad(decrypted_data, AES.block_size)

cipher = AESCipher()
