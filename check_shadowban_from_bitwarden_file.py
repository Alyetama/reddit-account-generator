import http.client
import json

from loguru import logger


def userinfo(username, verbose=False):
    while True:
        conn = http.client.HTTPSConnection('reddit.com')
        conn.request("GET",
                     f'https://www.reddit.com/user/{username}/about/.json')
        r = conn.getresponse()
        res = r.read().decode()
        if verbose:
            logger.debug(res)
        if r.status == 429:
            continue
        else:
            response = r.status
            if response == 404:
                notfound = True
                return notfound, None
            else:
                notfound = False
                data = json.loads(res)
                try:
                    verified = data['data']['has_verified_email']
                except KeyError:
                    return notfound, None
                return notfound, verified


def main(bw_export_file, verbose=False):
    with open(bw_export_file) as j:
        d = json.load(j)

    reddit_accts = [x for x in d['items'] if 'reddit' in x['name']]
    usernames = [x['login']['username'] for x in reddit_accts]

    for user in usernames:
        if userinfo(user, verbose)[0]:
            logger.info(f'Shadowbanned/deleted: {user}')


if __name__ == '__main__':
    main('<file>')
