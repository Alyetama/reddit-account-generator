#!/usr/bin/env python
# coding: utf-8

import email
import imaplib
import json
import os
import random
import re
import secrets
import shutil
import signal
import string
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import factory
import pymongo
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from twocaptcha import TwoCaptcha  # noqa

from reddit_gen.experimental import vpn_driver
from reddit_gen.handlers import keyboard_interrupt_handler, alarm_handler
from reddit_gen.reddit_settings import RedditSettings
from reddit_gen.utils import check_shadowban, custom_theme, mongodb_client


def _gen_username():
    while True:
        g_username = factory.build(dict,
                                   user=factory.Faker('user_name'))['user']
        rand_int = random.randint(0, 100)
        g_username = f'{g_username}_{rand_int}'
        if len(g_username) < 20:
            return g_username


def _gen_pass():
    punctuation = [
        x for x in list(string.punctuation) if x not in ['"', "'", '\\']
    ]
    punc = ''.join(random.sample(punctuation, 4))
    token = list(secrets.token_urlsafe(12) + punc)
    token = ''.join(random.sample(token, len(token)))
    return token


def _signup_info():
    _username = _gen_username()
    if os.getenv('CATCH_ALL_DOMAIN'):
        _email = f'{_username}@{os.environ["CATCH_ALL_DOMAIN"]}'
    else:
        e_address = os.environ['EMAIL_ADDRESS'].split('@')
        _email = f'{e_address[0]}+{_username}@{e_address[1]}'
    _passwd = _gen_pass()
    logger.opt(colors=True).info(
        f'Your account\'s email address: <u><y>{_email}</y></u>')
    logger.opt(colors=True).info(f'Username: <y>{_username}</y>')
    return _email, _username, _passwd


def _get_verf_url():
    if 'gmail' in os.environ['EMAIL_ADDRESS']:
        os.environ['IMAP_SERVER'] = 'imap.gmail.com'
    mail = imaplib.IMAP4_SSL(os.environ['IMAP_SERVER'])
    mail.login(os.environ['EMAIL_ADDRESS'], os.environ['EMAIL_PASSWD'])
    mail.select('inbox')

    mail_ids = sum([x.split() for x in mail.search(None, 'ALL')[1]], [])
    _, data = mail.fetch(mail_ids[-1], '(RFC822)')

    msg = email.message_from_bytes(data[0][1])  # noqa
    d = {
        'from': msg['from'],
        'subject': msg['subject'],
        'body': msg.get_payload(decode=True)
    }

    soup = BeautifulSoup(d['body'], 'html.parser')
    for link in soup.find_all('a', href=True):
        if '/verification/' in link['href']:
            return link['href']


def check_driver_path():
    driver_path = shutil.which('chromedriver')
    if not driver_path:
        if os.getenv('CHROME_DRIVER_PATH'):
            driver_path = os.environ['CHROME_DRIVER_PATH']
        else:
            print('Cannot find chromedriver! Add the chrome driver path '
                  'manually to the `.env` file.')
    return driver_path


def _cooldown_func(time_left, solve_manually=False):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(30)
    try:
        logger.warning('You don\'t need to respond if not applicable. '
                       'The program will automatically fallback to cooldown.')
        if not solve_manually:
            ans = input('Have you changed your IP address? (y/n) ')
            if ans.lower() != 'y':
                signal.alarm(0)
                logger.warning(
                    'You need to wait 10 minutes between new accounts...')
                logger.warning('DO NOT close this.  The program will continue '
                               'when the cooldown period has passed.')
                for _ in tqdm(range(time_left + 5)):
                    time.sleep(1)
            else:
                signal.alarm(0)
    except TimeoutError:
        logger.info('Started cooldown period.')
        for _ in tqdm(range(time_left - 25)):
            time.sleep(1)


def load_driver(driver_path,
                disable_headless=True,
                experimental_use_vpn=False,
                solve_manually=False,
                binary_location=None):
    options = webdriver.ChromeOptions()
    options.binary_location = binary_location
    if not disable_headless and not solve_manually:
        options.add_argument('headless')

    if experimental_use_vpn:
        del options
        try:
            driver = vpn_driver(driver_path, disable_headless=disable_headless)
        except Exception as e:
            logger.exception(e)
            driver.quit()
            sys.exit(1)
    else:
        service = Service(driver_path)
        driver = webdriver.Chrome(options=options, service=service)
    return driver


def generate(driver,
             disable_headless=False,
             solve_manually=False,
             ip_rotated=False,
             use_json=False,
             debug=False,
             experimental_use_vpn=False,
             env_file=None):
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    load_dotenv(env_file)

    if not os.getenv('MONGODB_CONNECTION_STRING') and not use_json:
        logger.warning(
            'The environment variable `MONGODB_CONNECTION_STRING` is not '
            'set. Defaulting to a local JSON database.')
        use_json = True

    local_db = f'{Path.home()}/.reddit_accounts.json'
    if use_json and not Path(local_db).exists():
        with open(local_db, 'w') as j:
            json.dump([], j)

    console = Console(theme=custom_theme())

    timestamp = datetime.now()

    driver_path = check_driver_path()
    if not driver_path:
        sys.exit(1)

    if use_json:
        with open(local_db) as j:
            data = json.load(j)
    else:
        col = mongodb_client(os.environ['MONGODB_CONNECTION_STRING'])['reddit']
        data = list(col.find({}))

    console.rule('Starting...', style='OK')

    driver.set_page_load_timeout(30)
    driver.get('https://www.reddit.com/account/register/')
    email_addr, username, passwd = _signup_info()

    elements = {
        'regEmail': email_addr,
        'regUsername': username,
        'regPassword': passwd
    }

    for k, v in elements.items():
        el = WebDriverWait(driver,
                           20).until(ec.presence_of_element_located(
                               (By.ID, k)))
        if k == 'regEmail':
            try:
                el.click()
            except ElementNotInteractableException:
                pass
            ActionChains(driver).send_keys(v).send_keys(Keys.RETURN).perform()
        else:
            el.send_keys(v)
        if k == 'regEmail':
            time.sleep(2)
    time.sleep(3)

    now = time.time()
    if use_json:
        if data:
            max_ts = datetime.strptime(data[-1]['created_on'],
                                       '%Y-%m-%d %H:%M:%S.%f')
        else:
            max_ts = datetime.today() - timedelta(days=1)
    else:
        max_ts = list(col.find({}).sort([('created_on', pymongo.ASCENDING)
                                         ]))[-1]['created_on']
    then = time.mktime(max_ts.timetuple())

    if (now - then) < 600:
        time_left = 600 - int(now - then)
        if not ip_rotated:
            _cooldown_func(time_left, solve_manually=solve_manually)

    if not solve_manually:
        API_KEY = os.getenv('TWO_CAPTCHA_KEY')
        if not API_KEY:
            logger.error(
                'Did not find an API key for 2Captcha in the .env file... '
                'Pass `--solve-manually` to solve the captcha manually.')
            sys.exit(1)
        solver = TwoCaptcha(API_KEY)
        logger.debug('Solving captcha...')
        result = solver.recaptcha(
            sitekey='6LeTnxkTAAAAAN9QEuDZRpn90WwKk_R1TRW_g-JC',
            url='https://www.reddit.com/account/register/')
        logger.debug('Solved!')
        driver.execute_script(
            '''var element=document.getElementById("g-recaptcha-response");
            element.style.display="";''')
        driver.execute_script(
            'document.getElementById("g-recaptcha-response").innerHTML = '
            'arguments[0]', result['code'])
        driver.execute_script(
            '''var element=document.getElementById("g-recaptcha-response");
            element.style.display="none";''')
    else:
        input('HIT ENTER TO CONTINUE...')

    signup_button = WebDriverWait(driver, 20).until(
        ec.presence_of_element_located((By.CLASS_NAME, 'SignupButton')))
    try:
        signup_button.click()

        es = driver.find_element(By.CLASS_NAME, 'AnimatedForm__bottomNav')
        es = es.find_elements(By.TAG_NAME, 'span')
    except Exception:  # noqa (debug)
        es = []
    try:
        for e in es:
            if e.get_attribute('class') == 'AnimatedForm__submitStatusMessage':
                try:
                    signup_button.click()
                except ElementNotInteractableException:
                    break
                time.sleep(3)
                try:
                    cooldown = int(re.findall(r'\d+', e.text)[0])
                    if 'minutes' in e.text:
                        cooldown *= 60
                    for _ in tqdm(range(cooldown + 10)):
                        time.sleep(1)
                except IndexError:
                    pass
        time.sleep(5)
    except Exception as e:  # noqa (debug)
        if debug:
            logger.exception(e)
    time.sleep(10)

    try:
        verf_url = _get_verf_url()
        driver.get(verf_url)
        try:
            time.sleep(3)
            driver.find_element(By.CLASS_NAME, 'verify-button').click()
        except Exception as e:
            logger.warning('Could not click on the verify button! '
                           'Trying a different method...')
            if debug:
                logger.exception(e)
    except Exception as e:
        if debug:
            logger.exception(e)
        logger.error('Could not verify your email. Verify it manually...')
    elements.update({'created_on': timestamp})
    elements = {k.replace('reg', '').lower(): v for k, v in elements.items()}

    logger.debug('Checking account info...')
    account_not_exists, verified = check_shadowban(username)
    if not account_not_exists:
        logger.debug('Passed!')
        elements.update({'shadowbanned': False})
    else:
        logger.error(
            'Something went wrong! The account did not pass the check!')
        raise SystemExit(1)
    if verified:
        elements.update({'verified': True})
        logger.info('Account verified!')
    else:
        elements.update({'verified': False})

    if data:
        max_id = max([x['_id'] for x in data])
    else:
        max_id = -1

    elements_ = {'_id': max_id + 1}
    elements_.update(elements)

    if use_json:
        backup_copy = f'{Path(local_db).parent}/{Path(local_db).stem}_copy.json'
        shutil.copy2(local_db, backup_copy)
        with open(local_db, 'w') as j:
            data.append(elements_)
            json.dump(data, j, indent=4)
        os.remove(backup_copy)
    else:
        col.insert_one(elements_)

    try:
        driver.set_page_load_timeout(10)
        driver.get('https://old.reddit.com/personalization')
        rs = RedditSettings(driver)
        rs.disable_tracking()
        rs.change_settings()
    except Exception as e:  # noqa (debug)
        if debug:
            logger.exception(e)
        logger.error('Could not change default settings.')

    driver.quit()
    console.rule('Done!', style='OK')
