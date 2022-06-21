#!/usr/bin/env python
# coding: utf-8

import http.client
import json
import os
from datetime import datetime

import pymongo
from rich.theme import Theme
from tqdm import tqdm


def mongodb_client():
    client = pymongo.MongoClient(os.environ['MONGODB_CONNECTION_STRING'])
    db = client['reddit']
    return db


def custom_theme():
    my_theme = Theme({
        'critical': '#ff5555 bold',
        'warning': '#f1fa8c',
        'info': '#8be9fd',
        'OK': '#50fa7b'
    })
    return my_theme


def check_shadowban(username):
    while True:
        conn = http.client.HTTPSConnection('reddit.com')
        conn.request('GET',
                     f'https://www.reddit.com/user/{username}/about/.json')
        r = conn.getresponse()
        if r.status == 429:
            continue
        else:
            response = r.status
            if response == 404:
                notfound = True
                return notfound, False
            else:
                notfound = False
                data = json.loads(r.read().decode("utf-8"))
                try:
                    verified = data['data']['has_verified_email']
                except KeyError:
                    return notfound, False
                return notfound, verified


def _check_account_age(account):
    now = datetime.now()
    account_age = (now - account['created_on']).days
    if account_age > 30:
        return True
    else:
        return False


def update_account_metadata():
    db = mongodb_client()
    col = db['reddit']
    data = list(col.find({}).sort([('created_on', pymongo.ASCENDING)]))

    for account in tqdm(data):
        is_aged = _check_account_age(account)
        notfound, verified = check_shadowban(account['username'])

        col.update_one({'_id': account['_id']}, {
            '$set': {
                'is_aged': is_aged,
                'shadowbanned': notfound,
                'verified': verified
            }
        })
