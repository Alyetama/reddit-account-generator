#!/usr/bin/env python
# coding: utf-8

import http.client
import json
import os
import time
from datetime import datetime

import pymongo
from loguru import logger
from rich.theme import Theme
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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


def is_banned_from_subreddit(subreddit: str, verbose: bool = False):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    service = Service()

    db = mongodb_client()
    col = db['reddit']
    accounts = [(x['username'], x['password']) for x in list(col.find({}))]

    subreddit_ban = {}

    for username, passwd in tqdm(accounts, desc='Subreddit ban check'):
        driver = webdriver.Chrome(options=options, service=service)
        driver.get('https://old.reddit.com')

        for e in driver.find_elements(By.TAG_NAME, 'input'):
            if e.get_attribute('name') == 'user':
                time.sleep(0.5)
                e.send_keys(username)
            elif e.get_attribute('name') == 'passwd':
                e.send_keys(passwd)
                time.sleep(0.5)
                driver.find_element(By.CLASS_NAME, 'submit').click()
                break
        time.sleep(1)
        driver.get(f'https:/old.reddit.com/r/{subreddit}/submit')
        time.sleep(1)
        try:
            content = driver.find_element(By.CLASS_NAME, 'content').text
        except NoSuchElementException:
            logger.warning(
                f'Failed to check whether {username} is banned from {subreddit}!'
            )
            continue
        if 'forbidden' in content:
            subreddit_ban = True
            ban_print = f'\033[40m\033[31m{subreddit_ban}\033[39m\033[49m'
        else:
            subreddit_ban = False
            ban_print = f'\033[40m\033[32m{subreddit_ban}\033[39m\033[49m'
        if verbose:
            print(f'`\033[34m{username}\033[39m` is banned from '
                  f'\033[35m{subreddit}\033[39m: {ban_print}')
        driver.quit()

        col.update_one({'username': username},
                       {'$set': {
                           'subreddit_ban': {
                               subreddit: subreddit_ban
                           }
                       }})
    return subreddit_ban


def update_account_metadata():
    db = mongodb_client()
    col = db['reddit']
    data = list(col.find({}).sort([('created_on', pymongo.ASCENDING)]))

    for account in tqdm(data):
        is_aged = _check_account_age(account)
        notfound, verified = check_shadowban(account['username'])

        entry = {
            '$set': {
                'is_aged': is_aged,
                'shadowbanned': notfound,
                'verified': verified
            }
        }
        col.update_one({'_id': account['_id']}, entry)
