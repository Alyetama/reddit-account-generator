import concurrent.futures
import copy
import http.client
import json

from cryptography.fernet import Fernet
import keyring

from encrypted_json import encrypted_json
from helpers import print_diff, data_path


def userinfo(username):
    while True:
        conn = http.client.HTTPSConnection('reddit.com')
        conn.request("GET", f'https://www.reddit.com/user/{username}/about/.json')
        r = conn.getresponse()
        if r.status == 429:
            continue
        else:
            response = r.status
            if response == 404:
                notfound = True
                return notfound, None
            else:
                notfound = False
                data = json.loads(r.read().decode("utf-8"))
                try:
                    verified = data['data']['has_verified_email']
                except KeyError:
                    return notfound, None
                return notfound, verified


def main():
    def check(n, account):
        username = account['username']
        shadowbanned, verified = userinfo(username)
        if verified is not None:
            account.update({'shadowbanned': shadowbanned, 'verified': verified})
        else:
            account.update({'shadowbanned': shadowbanned})

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
    try:
        main()
    except http.client.HTTPException:
        raise ConnectionError('The programm encountered an error! Try again.')
