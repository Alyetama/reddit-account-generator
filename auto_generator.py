#!/usr/bin/env python
# coding: utf-8

import json
import os
import imaplib
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
import imap_tools
import keyring
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
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
from encrypted_json import encrypted_json
from helpers import console, cprint
from vpn_driver import vpn_driver


def return_time():
    time_string = str(datetime.now())
    unix_time = time.time()
    return time_string, unix_time


def handler(signum, frame):
    raise Exception('No response.')


def str_to_unix(ts: str):
    return time.mktime(
        datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f').timetuple())


def signup_info(email_address):
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

    def gen_alias(parent_email, genned_username):
        alias = parent_email.split('@')
        alias = f'{alias[0]}+{genned_username}@{alias[-1]}'
        return alias

    username_ = gen_username()
    email_ = gen_alias(email_address, username_)
    passwd_ = gen_pass()
    cprint(f'Your account\'s email address: [u][#8be9fd]{email_}', style='OK')
    cprint(f'Username: [#8be9fd]{username_}', style='OK')
    cprint(
        f'Password and other data will be exported to:\n[u][#8be9fd]{fpath}',
        style='OK')
    return email_, username_, passwd_


def verify_account(addr, driver):
    mail_p = keyring.get_password('gmail', 'reddit')
    mail_p = os.environ['EMAIL_PASS']
    if not mail_p:
        cprint('Did not find a password for your email in your keyring...',
               style='critical')
        mail_p = input('Email password: ')
        keyring.set_password('gmail', 'reddit', mail_p)
    keys = {
        'subject': 'Verify your Reddit email address',
        'date': datetime.today().date(),
        'seen': False,
        'to': addr
    }

    while True:
        with imap_tools.MailBox('imap.gmail.com').login(addr,
                                                        mail_p) as mailbox:
            for msg in mailbox.fetch(imap_tools.AND(**keys)):
                if msg.to[0] == addr:
                    content = msg.html
                    soup = BeautifulSoup(content, 'lxml')
                    for link in soup.find_all('a', href=True):
                        if '/verification/' in link['href']:
                            verf_link = link['href']
                            break
                    driver.get(verf_link)
                    mailbox.flag(msg.uid, imap_tools.MailMessageFlags.SEEN,
                                 True)
                    return verf_link
                else:
                    continue
        time.sleep(3)


def main():
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
    email_account = os.getenv('EMAIL')
    email, username, passwd = signup_info(email_account)
    elements = {
        'regEmail': email,
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

    timestamp, now = return_time()
    if Path(fpath).exists():
        data = encrypted_json(data_path=fpath)
        then = str_to_unix(data[-1]['created_on'])
        if (now - then) < 600:
            time_left = 600 - int(now - then)
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(30)
            try:
                cprint(
                    'You don\'t need to respond if not applicable.  The program will automatically resume in 30 seconds.',
                    style='warning')
                if '--solve' not in sys.argv:
                    ans = input('Have you changed your IP address? (y/n) ')
                    if ans.lower() != 'y':
                        signal.alarm(0)
                        cprint(
                            'You need to wait 10 minutes between new accounts...',
                            style='warning')
                        cprint(
                            'DO NOT close this.  The program will continue when the '
                            'cooldown period has passed.',
                            style='critical')
                        for _ in tqdm(range(time_left + 5)):
                            time.sleep(1)
                    else:
                        signal.alarm(0)
            except Exception:
                for _ in tqdm(range(time_left - 25)):
                    time.sleep(1)
    else:
        data = encrypted_json(data_path=fpath)

    timestamp, _ = return_time()

    if '--solve' not in sys.argv:
        API_KEY = keyring.get_password('2captcha', 'API_KEY')
        if not API_KEY:
            cprint('Did not find an API key for 2Captcha in your keyring...',
                   style='critical')
            api_key = input('2Captch API Key: ')
            keyring.set_password('2captcha', 'API_KEY', api_key)
        solver = TwoCaptcha(API_KEY)
        cprint('Solving captcha...', style='info')
        result = solver.recaptcha(
            sitekey='6LeTnxkTAAAAAN9QEuDZRpn90WwKk_R1TRW_g-JC',
            url='https://www.reddit.com/account/register/')
        cprint('Solved!', style='info')
        driver.execute_script(
            '''var element=document.getElementById("g-recaptcha-response");
            element.style.display="";''')
        driver.execute_script(
            """
          document.getElementById("g-recaptcha-response").innerHTML = arguments[0]
        """, result['code'])
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
        verified = verify_account(email, driver)
        try:
            time.sleep(3)
            driver.find_element(By.CLASS_NAME, 'verify-button').click()
        except:
            pass
    except Exception as e:
        print(e)
        cprint('Could not verify your email. Verify it manually...', style='critical')
    elements.update({'created_on': timestamp})
    elements = {k.replace('reg', '').lower(): v for k, v in elements.items()}

    cprint('Checking account info...', style='info')
    account_not_exists, verified = userinfo(username)
    if not account_not_exists:
        cprint('Passed!', style='OK')
        elements.update({'shadowbanned': False})
    else:
        cprint(
            'Something went wrong! The account did [b]not[/b] pass the '
            'check!',
            style='critical')
        raise SystemExit(1)
    if verified:
        elements.update({'verified': True})
        cprint('Account verified!', style='OK')
    else:
        elements.update({'verified': False})

    elements_ = {'index': data[-1]['index'] + 1}
    elements_.update(elements)

    key = keyring.get_password('secrets', 'reddit')
    fernet = Fernet(key)

    if not Path(fpath).exists():
        Path(fpath).touch()
        elements_ = [elements_]  # noqa
    else:
        with open(fpath, 'r+b') as j:
            d = encrypted_json(data_path=fpath)
            d.append(elements_)
            j.seek(0, 0)
            encrypted = fernet.encrypt(
                bytes(json.dumps(d, indent=4), encoding='utf-8'))
            j.seek(0, 0)
            j.write(encrypted)

    try:
        driver.set_page_load_timeout(10)
        driver.get('https://old.reddit.com/personalization')
        reddit_settings.disable_tracking(driver)
        reddit_settings.change_settings(driver)
    except Exception:
        cprint('Could not change default settings.', style='critical')
        pass

    driver.quit()
    console.rule('Done!', style='OK')


if __name__ == '__main__':
    parent = Path(__file__).parent
    try:
        fpath = f'{parent}/reddit_accounts.json'
    except NameError:
        fpath = 'reddit_accounts.json'
    driver_path = shutil.which('chromedriver')
    if not driver_path:
        if Path(f'{parent}/.chrome_driver_path').exists():
            with open(f'{parent}/.chrome_driver_path') as f:
                driver_path = f.readlines()[0]
        else:
            ans_path = input('Cannot find chromedriver!  '
                             'Enter your chromedriver path manually: ')
            with open(f'{parent}/.chrome_driver_path', 'w') as f:
                f.write(ans_path + '\n')
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(0)
