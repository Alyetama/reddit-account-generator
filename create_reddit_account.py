import http.client
import json
import os
import random
import secrets
import string
import time
import traceback
from datetime import datetime
from pathlib import Path

import dotenv
import factory
from notifypy import Notify
from rich.console import Console
from rich.theme import Theme
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


def custom_theme():
    my_theme = Theme({
        'critical': '#ff5555 bold',
        'warning': '#f1fa8c',
        'info': '#8be9fd',
        'OK': '#50fa7b'
    })

    return my_theme


def return_time(ts):
    ts_str = str(ts)
    t = ''.join(ts_str.split(' ')[1:]).split(':')
    t = [int(float(x)) for x in t]
    total = sum([x * y for x, y in zip([3600, 60, 1], t)])

    return ts_str, total


def validate_email(api_key, email):
    conn = http.client.HTTPSConnection("mailsac.com")
    headers = {'Mailsac-Key': api_key}
    conn.request('GET', f'/api/validations/addresses/{email}', headers=headers)
    res = conn.getresponse()
    data = res.read()

    return data.decode('utf-8')


def create_email_address(api_key):
    username = factory.build(dict, user=factory.Faker('user_name'))['user']
    rand_int = random.randint(0, 1000)
    email = f'{username}_{rand_int}@mailsac.com'

    conn = http.client.HTTPSConnection('mailsac.com')
    payload = '{\'info\':\'string\',\'forward\':\'\',\'enablews\':false,' \
              '\'webhook\':\'\',\'webhookSlack\':\'\',' \
              '\'webhookSlackToFrom\':true} '
    headers = {'content-type': 'application/json', 'Mailsac-Key': api_key}
    conn.request('POST', f'/api/addresses/{email}', payload, headers)

    validate = validate_email(api_key, email)
    validate = json.loads(validate)
    assert validate['isValidFormat']

    return email


def get_messages(api_key, email):
    conn = http.client.HTTPSConnection("mailsac.com")
    headers = {'Mailsac-Key': api_key}
    conn.request('GET', f'/api/addresses/{email}/messages', headers=headers)
    res = conn.getresponse()
    data = res.read()
    res_dict = json.loads(data.decode("utf-8"))

    return res_dict


def signup_info():
    def gen_username():
        g_username = factory.build(
            dict, user=factory.Faker('user_name'))['user']
        rand_int = random.randint(0, 100)
        return f'{g_username}_{rand_int}'

    def gen_pass():
        punctuation = [
            x for x in list(string.punctuation) if x not in ['"', "'", '\\']
        ]
        punc = ''.join(random.sample(punctuation, 4))
        token = list(secrets.token_urlsafe(12) + punc)
        token = ''.join(random.sample(token, len(token)))

        return token

    email = create_email_address(secret)
    username = gen_username()
    passwd = gen_pass()
    cprint(f'Your disposable email address: [u][#8be9fd]{email}', style='OK')
    cprint(f'Username: [#8be9fd]{username}', style='OK')
    cprint(f'Password and other data were exported to [u][#8be9fd]{fpath}',
           style='OK')

    return email, username, passwd


def verify_email(email):
    latest_msg = get_messages(secret, email)[0]
    verif_link = latest_msg['links'][2]
    cprint(f'Verification link: {verif_link}', style='info')

    return verif_link


def main():
    console.rule('Starting...', style='OK')
    driver.get('https://www.reddit.com/account/register/')
    email, username, passwd = signup_info()
    elements = {
        'regEmail': email,
        'regUsername': username,
        'regPassword': passwd
    }
    for k, v in elements.items():
        el = WebDriverWait(driver,
                           20).until(EC.presence_of_element_located(
                               (By.ID, k)))
        if k == 'regEmail':
            el.click()
            ActionChains(driver).send_keys(v).send_keys(Keys.RETURN).perform()
        else:
            el.send_keys(v)

    time.sleep(3)

    timestamp, now = return_time(datetime.now())
    if Path(fpath).exists():
        with open(fpath) as j:
            data = json.load(j)
        _, then = return_time(data[-1]['created_on'])
        if (now - then) / 60 < 10:
            cprint('You need to wait 10 minutes between new accounts...',
                   style='warning')
            cprint(
                'DO NOT close this.  The program will continue when the '
                'cooldown period has passed.',
                style='critical')
            ip_changed = console.input(
                '[#f1fa8c]Have you switched your IP in the past 10 mins ('
                'e.g., using a VPN) (y/n)? '
            )
            if ip_changed.lower() != 'y':
                cprint(
                    'Then wait... You will be notified when everything is '
                    'ready!',
                    style='warning')
                notification = Notify()
                notification.title = 'Reddit Accounts Generator'
                notification.message = 'Time to solve some captchas!'
                time_left = 600 - int(now - then)
                for _ in tqdm(range(time_left)):
                    time.sleep(1)
                try:
                    notification.send()
                except Exception:
                    pass

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'g-recaptcha'))).click()
    print()
    ans = console.input('[#f1fa8c]Solved reCAPTCHA (y/n)? ')

    if ans.lower() == 'y':
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'SignupButton'))).click()
        except Exception:
            pass
        time.sleep(3)
        verification_link = verify_email(email)
        driver.get(verification_link)
        time.sleep(5)
        cprint('Verified!', style='OK')
        elements.update({'verified': True})
        elements.update({'created_on': timestamp})
        elements = {
            k.replace('reg', '').lower(): v
            for k, v in elements.items()
        }

        if Path(fpath).exists():
            with open(fpath, 'r+') as j:
                d = json.load(j)
                d.append(elements)
                j.truncate(0)
                j.seek(0)
                json.dump(d, j, indent=4)
        else:
            with open(fpath, 'w') as j:
                json.dump([elements], j, indent=4)

        console.rule('Done!', style='OK')

    else:
        console.rule('Terminating...', style='critical')


if __name__ == '__main__':
    parent = f'{Path(__file__).parent}'
    fpath = f'{parent}/reddit_accounts.json'
    if not Path(f'{parent}/.env').exists():
        raise Exception('Create an ".env" file first!')
    dotenv.load_dotenv(f'{parent}/.env')
    secret = os.getenv('SECRET')

    theme = custom_theme()
    errconsole = Console(theme=theme, stderr=True)
    console = Console(theme=theme)
    cprint = console.print

    try:
        driver = webdriver.Chrome()
    except WebDriverException:
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        os.environ['WDM_LOCAL'] = '1'
        os.environ['keep_alive'] = '1'
        driver = webdriver.Chrome(ChromeDriverManager().install())
        
    try:
        main()
    except (WebDriverException, NoSuchWindowException):
        cprint('Window closed by user! Terminating...', style='critical')
    except Exception as e:
        tb = traceback.format_exception(None, e, e.__traceback__)
        for line in tb:
            errconsole.print(line, style='critical')
