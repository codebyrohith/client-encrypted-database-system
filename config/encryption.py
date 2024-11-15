from eciespy import encrypt, decrypt, generate_eth_key
import base64

class ECCEncryption:
    @staticmethod
    def generate_key_pair():
        private_key = generate_eth_key()
        public_key = private_key.public_key
        return private_key, public_key
    
    @staticmethod
    def encrypt_data(public_key, data):
        if isinstance(data, str):
            data = data.encode()
        encrypted = encrypt(public_key.to_bytes(), data)
        return base64.b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_data(private_key, encrypted_data):
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = decrypt(private_key.to_bytes(), encrypted_bytes)
        return decrypted.decode()