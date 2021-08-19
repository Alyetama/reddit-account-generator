import json
import requests


def shadowban(username):
    while True:
        r = requests.get(f'http://www.reddit.com/user/{username}/about/.json')
        if r.status_code == 429:
            continue
        else:
            response = r.status_code
            break
    if response == 404:
        shadowbanned = True
    else:
        shadowbanned = False
    return shadowbanned


def main():
    with open('reddit_accounts.json', 'r+') as j:
        accounts = json.load(j)
        for n, account in enumerate(accounts):
            username = account['username']
            shadowbanned = shadowban(username)
            if shadowbanned:
                accounts[n].update({'shadowbanned': True})
            else:
                accounts[n].update({'shadowbanned': False})
        j.seek(0, 0)
        json.dump(accounts, j, indent=4)


if __name__ == '__main__':
    main()
