import json
import os

from cryptography.fernet import Fernet
import keyring
from rich.console import Console


def encrypted_json(data_path, print_data=False):
    key = keyring.get_password('secrets', 'reddit')
    if not key:
        key = Fernet.generate_key()
        keyring.set_password('secrets', 'reddit', key)
    fernet = Fernet(key)

    with open(data_path, 'r+b') as f:
        try:
            data = json.load(f)
            encrypted = fernet.encrypt(
                bytes(json.dumps(data, indent=4), encoding='utf-8'))
            f.seek(0, 0)
            f.write(encrypted)
        except json.decoder.JSONDecodeError:
            f.seek(0, 0)
            encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            decrypted = json.loads(decrypted)
            if print_data:
                Console().print(json.dumps(decrypted, indent=4))
            else:
                return decrypted


if __name__ == '__main__':
    encrypted_json(data_path='reddit_accounts.json', print_data=True)
