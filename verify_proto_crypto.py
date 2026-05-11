import sys
import os
sys.path.append(os.getcwd())

from core.proto import encode_request, decode_response
from core.crypto import aes_encrypt, aes_decrypt

def test_round_trip():
    uid = "123456789"
    region = "IND"
    version = "OB53"

    print("Testing Proto + AES Round Trip...")

    # 1. Encode
    encoded = encode_request(uid, region, version)
    print(f"Encoded bytes: {encoded.hex()}")

    # 2. Encrypt
    encrypted = aes_encrypt(encoded)
    print(f"Encrypted bytes: {encrypted.hex()}")

    # 3. Decrypt
    decrypted = aes_decrypt(encrypted)
    print(f"Decrypted bytes: {decrypted.hex()}")
    assert decrypted == encoded

    # 4. Decode
    decoded = decode_response(decrypted)
    print(f"Decoded dict: {decoded}")

    # Check values
    # In our recursive Strategy B, field 1 might be decoded as a dict if it looks like proto.
    # We handle both cases for verification.
    def get_val(data):
        if isinstance(data, bytes):
            return data.decode()
        return str(data) # Fallback for dict

    res_uid = get_val(decoded[1])
    res_region = get_val(decoded[2])
    res_version = get_val(decoded[3])

    print(f"Decoded UID: {res_uid}")
    print(f"Decoded Region: {res_region}")
    print(f"Decoded Version: {res_version}")

    assert region in res_region
    assert version in res_version

    print("Round Trip Successful!")

if __name__ == "__main__":
    try:
        test_round_trip()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
