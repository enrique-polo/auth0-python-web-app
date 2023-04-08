import json
from cryptography.fernet import Fernet
import os


class LocalCache:
    def get(self, key):
        cache: dict = self.load_dict()
        return cache.get(key, None)

    def set(self, key, value, expires=None):
        cache = self.load_dict()
        cache[key] = value
        self.save_dict(cache)

    def delete(self, key):
        cache = self.load_dict()
        cache.pop(key)
        self.save_dict(cache)

    def load_dict(self):
        if os.path.isfile('./cache.bin'):
            fernet = Fernet(self.get_fernet_key())
            with open('./cache.bin', 'rb') as enc_file:
                encrypted = enc_file.read()
            decrypted = fernet.decrypt(encrypted)
            cache = json.loads(decrypted)
        else:
            cache = {}
        return cache

    def save_dict(self, cache: dict):
        json_object = json.dumps(cache).encode('utf-8')
        fernet = Fernet(self.get_fernet_key())
        encrypted = fernet.encrypt(json_object)
        with open('./cache.bin', 'wb') as encrypted_file:
            encrypted_file.write(encrypted)

    def get_fernet_key(self):
        if os.path.isfile('./cache.key'):
            with open('./cache.key', 'rb') as filekey:
                key = filekey.read()
        else:
            key = Fernet.generate_key()
            with open('./cache.key', 'wb') as filekey:
                filekey.write(key)
        return key
