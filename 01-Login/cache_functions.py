import json
from cryptography.fernet import Fernet
import os


class LocalCache(dict):
    def __init__(self) -> None:
        super().__init__()
        self.cache = self.__load_cache()

    def get(self, key, default = None):
        return self.cache.get(key, default)

    def set(self, key, value, expires=None):
        self.cache[key] = value
        self.__save_cache()

    def delete(self, key):
        self.cache.pop(key)
        self.__save_cache()

    def __load_cache(self):
        if os.path.isfile('./cache.bin'):
            fernet = Fernet(self.__get_fernet_key())
            with open('./cache.bin', 'rb') as enc_file:
                encrypted = enc_file.read()
            decrypted = fernet.decrypt(encrypted)
            cache = json.loads(decrypted)
        else:
            cache = {}
        return cache

    def __save_cache(self):
        json_object = json.dumps(self.cache).encode('utf-8')
        fernet = Fernet(self.__get_fernet_key())
        encrypted = fernet.encrypt(json_object)
        with open('./cache.bin', 'wb') as encrypted_file:
            encrypted_file.write(encrypted)

    def __get_fernet_key(self):
        if os.path.isfile('./cache.key'):
            with open('./cache.key', 'rb') as filekey:
                key = filekey.read()
        else:
            key = Fernet.generate_key()
            with open('./cache.key', 'wb') as filekey:
                filekey.write(key)
        return key
