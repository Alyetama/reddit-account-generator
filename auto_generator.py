#!/usr/bin/env python
# coding: utf-8

import email
import imaplib
import os
import random
import re
import secrets
import shutil
import signal
import string
import sys
import time
from datetime import datetime
from pathlib import Path

import dotenv
import factory
import pymongo
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from twocaptcha import TwoCaptcha

import reddit_settings
from check_shadowban import userinfo
from helpers import console, cprint
from vpn_driver import vpn_driver


def keyboard_interrupt_handler(sig, _):
    logger.warning(f'KeyboardInterrupt (id: {sig}) has been caught...')
    logger.info('Terminating the session gracefully...')
    sys.exit(1)


def alarm_handler(signum, frame):
    raise TimeoutError('No response...')


def mongodb_client():
    client = pymongo.MongoClient(os.environ['MONGODB_CONNECTION_STRING'])
    db = client['reddit']
    return db


def gen_username():
    while True:
        g_username = factory.build(dict,
                                   user=factory.Faker('user_name'))['user']
        rand_int = random.randint(0, 100)
        g_username = f'{g_username}_{rand_int}'
        if len(g_username) < 20:
            return g_username


def gen_pass():
    punctuation = [
        x for x in list(string.punctuation) if x not in ['"', "'", '\\']
    ]
    punc = ''.join(random.sample(punctuation, 4))
    token = list(secrets.token_urlsafe(12) + punc)
    token = ''.join(random.sample(token, len(token)))
    return token


def signup_info():
    _username = gen_username()
    _email = f'{_username}@{os.environ["CATCH_ALL_DOMAIN"]}'
    _passwd = gen_pass()
    cprint(f'Your account\'s email address: [u][#8be9fd]{_email}', style='OK')
    cprint(f'Username: [#8be9fd]{_username}', style='OK')
    return _email, _username, _passwd


def get_verf_url():
    mail = imaplib.IMAP4_SSL(os.environ['IMAP_SERVER'])
    mail.login(os.environ['EMAIL_ADDRESS'], os.environ['EMAIL_PASSWD'])
    mail.select('inbox')

    mail_ids = sum([x.split() for x in mail.search(None, 'ALL')[1]], [])
    _, data = mail.fetch(mail_ids[-1], '(RFC822)')

    msg = email.message_from_bytes(data[0][1])
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


def cooldown_func(time_left):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(30)
    try:
        logger.warning('You don\'t need to respond if not applicable. '
                       'The program will automatically resume in 30 seconds.')
        if '--solve' not in sys.argv:
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
        for _ in tqdm(range(time_left - 25)):
            time.sleep(1)


def main():
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    driver_path = check_driver_path()
    if not driver_path:
        sys.exit(1)

    col = mongodb_client()['reddit']
    data = list(col.find({}))

    console.rule('Starting...', style='OK')
    options = webdriver.ChromeOptions()
    args_ = ['--disable-headless', '--solve']

    if not any([True for x in args_ if x in sys.argv]):
        options.add_argument('headless')

    if '--vpn' in sys.argv:
        del options
        driver = vpn_driver(headless=False)
    else:
        service = Service(driver_path)
        driver = webdriver.Chrome(options=options, service=service)

    driver.set_page_load_timeout(30)
    driver.get('https://www.reddit.com/account/register/')
    dotenv.load_dotenv(f'{Path(__file__).parent}/.env')
    email_addr, username, passwd = signup_info()

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
            el.click()
            ActionChains(driver).send_keys(v).send_keys(Keys.RETURN).perform()
        else:
            el.send_keys(v)
    time.sleep(3)

    now = time.time()
    max_ts = [
        x for x in data
        if x['created_on'] == max([y['created_on'] for y in data])
    ][0]['created_on']
    then = time.mktime(max_ts.timetuple())

    if (now - then) < 600:
        time_left = 600 - int(now - then)
        if not '--changed-ip' in sys.argv:
            cooldown_func(time_left)

    timestamp = datetime.now()

    if '--solve-manually' not in sys.argv:
        API_KEY = os.getenv('2CAPTCHA_KEY')
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
    except Exception:
        pass
    try:
        for e in es:
            if e.get_attribute('class') == 'AnimatedForm__submitStatusMessage':
                try:
                    signup_button.click()
                except ElementNotInteractableException:
                    break
                time.sleep(3)
                try:
                    cooldown = int(re.findall('[0-9]+', e.text)[0])
                    if 'minutes' in e.text:
                        cooldown = cooldown * 60
                    for _ in tqdm(range(cooldown + 10)):
                        time.sleep(1)
                except IndexError:
                    pass
        time.sleep(5)
    except Exception:
        pass
    time.sleep(10)

    try:
        verf_url = get_verf_url()
        driver.get(verf_url)
        try:
            time.sleep(3)
            driver.find_element(By.CLASS_NAME, 'verify-button').click()
        except:
            logger.warning('Could not click on the verify button!')
    except Exception as e:
        logger.exception(e)
        logger.error('Could not verify your email. Verify it manually...')
    elements.update({'created_on': timestamp})
    elements = {k.replace('reg', '').lower(): v for k, v in elements.items()}

    logger.debug('Checking account info...')
    account_not_exists, verified = userinfo(username)
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

    max_id = max([x['_id'] for x in data])
    elements_ = {'_id': max_id + 1}
    elements_.update(elements)

    col.insert_one(elements_)

    try:
        driver.set_page_load_timeout(10)
        driver.get('https://old.reddit.com/personalization')
        reddit_settings.disable_tracking(driver)
        reddit_settings.change_settings(driver)
    except Exception:
        logger.error('Could not change default settings.')

    driver.quit()
    console.rule('Done!', style='OK')


if __name__ == '__main__':
    main()
