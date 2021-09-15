import concurrent.futures
import copy
import json
import requests

from cryptography.fernet import Fernet
import keyring

from encrypted_json import encrypted_json
from helpers import print_diff, data_path


def userinfo(username):
    while True:
        r = requests.get(f'https://www.reddit.com/user/{username}/about/.json')
        if r.status_code == 429:
            continue
        else:
            response = r.status_code
            if response == 404:
                notfound = True
            else:
                notfound = False
            return notfound


def main():
    def check(n, account):
        username = account['username']
        shadowbanned = userinfo(username)
        if shadowbanned:
            accounts[n].update({'shadowbanned': True})
        else:
            accounts[n].update({'shadowbanned': False})

    accounts = encrypted_json(data_path)
    accounts_before_check = copy.deepcopy(accounts)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [
            executor.submit(check, n, account)
            for n, account in enumerate(accounts)
        ]
        for future in concurrent.futures.as_completed(results):
            future.result()
    with open(data_path, 'r+b') as j:
        key = keyring.get_password('secrets', 'reddit')
        fernet = Fernet(key)
        encrypted = fernet.encrypt(
            bytes(json.dumps(accounts, indent=4), encoding='utf-8'))
        j.seek(0, 0)
        j.write(encrypted)

    print_diff(accounts_before_check, accounts)


if __name__ == '__main__':
    main()
