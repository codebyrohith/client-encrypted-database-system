from ecies import encrypt, decrypt
from ecies.utils import generate_key
import base64

class ECCEncryption:
    @staticmethod
    def generate_key_pair():
        private_key = generate_key()
        public_key = private_key.public_key.format(True)
        return private_key, public_key

    @staticmethod
    def encrypt_data(public_key, data):
        encrypted = encrypt(public_key, data.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt_data(private_key, encrypted_data):
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        decrypted = decrypt(private_key.secret, encrypted_data_bytes)
        return decrypted.decode('utf-8')
