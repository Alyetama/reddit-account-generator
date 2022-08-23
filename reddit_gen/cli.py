#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import signal
import sys
from getpass import getpass
from pathlib import Path
from platform import platform

from dotenv import load_dotenv
from loguru import logger
from reddit_gen.generator import check_driver_path, generate, load_driver
from reddit_gen.handlers import keyboard_interrupt_handler
from reddit_gen.utils import is_banned_from_subreddit, update_account_metadata
from selenium.common.exceptions import WebDriverException


def _opts() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--disable-headless',
                        help='Disable headless mode',
                        action='store_true')
    parser.add_argument('-s',
                        '--solve-manually',
                        help='Solve the captcha manually',
                        action='store_true')
    parser.add_argument('-i',
                        '--ip-rotated',
                        help='The public IP address was changed by the user '
                        'since the last created account (to bypass the '
                        'cooldown)',
                        action='store_true')
    parser.add_argument('-j',
                        '--use-json',
                        help='Read from the local JSON database (pass if '
                        'you\'re not using MongoDB). A new local database '
                        'will be created if not found',
                        action='store_true')
    parser.add_argument(
        '-p',
        '--show-local-database-path',
        help='Prints the path to the local database, if exists',
        action='store_true')
    parser.add_argument('-n',
                        '--create-n-accounts',
                        help='Number of accounts to create (default: 1)',
                        type=int,
                        default=1)
    parser.add_argument('-c',
                        '--config-file',
                        help='Path to the config file. Defaults to '
                        f'{Path(Path.home() / ".redditgen.env")}')
    parser.add_argument('-D',
                        '--debug',
                        help='Debug mode',
                        action='store_true')
    parser.add_argument('-U',
                        '--update-database',
                        help='Update accounts metadata (MongoDB-only)',
                        action='store_true')
    parser.add_argument('--configure',
                        action='store_true',
                        help='Configure your environment')
    parser.add_argument('--experimental-use-vpn',
                        action='store_true',
                        help='Experimental feature (unstable)')
    parser.add_argument('--check-subreddit-ban',
                        help='Check if your accounts are banned from a '
                        'specific subreddit (MongoDB-only)',
                        type=str)
    parser.add_argument('-v',
                        '--verbose',
                        help='Print more logs',
                        action='store_true')
    return parser.parse_args()


def configure(rc_file):
    cfg = ''
    email_address = input('Email address (required):\n> ')
    cfg += f'EMAIL_ADDRESS={email_address}\n'
    email_passwd = getpass('Email password (required):\n> ')
    cfg += f'EMAIL_PASSWD={email_passwd}\n'
    if '@gmail' in email_address:
        cfg += 'IMAP_SERVER=imap.gmail.com\n'
    else:
        imap_server = input(
            'IMAP Server of your email provider (required):\n> ')
        cfg += f'IMAP_SERVER={imap_server}\n'
    two_captcha_key = getpass(
        'TWO_CAPTCHA_KEY (optional; leave empty to skip):\n> ')
    if two_captcha_key:
        cfg += f'TWO_CAPTCHA_KEY={two_captcha_key}\n'
        mongodb_connection_string = getpass(
            'MONGODB_CONNECTION_STRING (optional; leave empty to skip):\n> ')
    if mongodb_connection_string:
        cfg += f'MONGODB_CONNECTION_STRING={mongodb_connection_string}\n'

    with open(rc_file, 'w') as f:
        f.write(cfg)
    logger.info(f'Configuration file location: {rc_file}')


def main():
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    args = _opts()
    rc_file = Path(Path.home() / '.redditgen.env')

    if args.configure:
        configure(rc_file)
        sys.exit(0)

    if not args.config_file:
        args.config_file = rc_file

    if not rc_file.exists():
        logger.warning('You have no configured your environment yet!')
        configure(rc_file)

    load_dotenv(rc_file)

    if args.show_local_database_path:
        local_db = f'{Path.home()}/.reddit_accounts.json'
        if Path(local_db).exists():
            print(local_db)
        else:
            logger.error(
                'Could not find a local database! Run the program at '
                'least once with the flag `--use-json` to generate it.')
        sys.exit(0)

    if args.update_database:
        update_account_metadata()
        sys.exit(0)

    if args.check_subreddit_ban:
        args.check_subreddit_ban = args.check_subreddit_ban.lstrip('r/')
        is_banned_from_subreddit(subreddit=args.check_subreddit_ban,
                                 verbose=args.verbose)
        sys.exit(0)

    if args.experimental_use_vpn and not args.disable_headless:
        logger.error('Cannot use `--experimental-use-vpn` in headless mode!')
        sys.exit(1)

    driver_path = check_driver_path()
    try:
        driver = load_driver(driver_path,
                             disable_headless=args.disable_headless,
                             experimental_use_vpn=args.experimental_use_vpn,
                             solve_manually=args.solve_manually)
    except WebDriverException:
        if 'macOS' in platform() and not os.getenv('CHROME_BINARY_LOCATION'):
            if Path('/Applications/Chrome.app').exists():
                os.environ[
                    'CHROME_BINARY_LOCATION'] = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            elif Path('/Applications/Chromium.app').exists():
                os.environ[
                    'CHROME_BINARY_LOCATION'] = '/Applications/Chromium.app/Contents/MacOS/Chromium'

        if not os.getenv('CHROME_BINARY_LOCATION'):
            logger.error(
                'Could not find a chrome browser binary! Pass it manually or '
                'set the environment variable `CHROME_BINARY_LOCATION`')
            os.environ['CHROME_BINARY_LOCATION'] = input(
                'Chrome browser binary: ')
            if not Path(os.environ['CHROME_BINARY_LOCATION']).exists():
                raise FileNotFoundError(f'Could not find {chrome_binary}!')

        driver = load_driver(
            driver_path,
            disable_headless=args.disable_headless,
            experimental_use_vpn=args.experimental_use_vpn,
            solve_manually=args.solve_manually,
            binary_location=os.environ['CHROME_BINARY_LOCATION'])

    for _ in range(args.create_n_accounts):
        try:
            generate(driver=driver,
                     disable_headless=args.disable_headless,
                     solve_manually=args.solve_manually,
                     ip_rotated=args.ip_rotated,
                     use_json=args.use_json,
                     debug=args.debug,
                     experimental_use_vpn=args.experimental_use_vpn,
                     env_file=args.config_file)
        except Exception as e:
            logger.exception(e)
            driver.quit()
            logger.debug('Terminated the driver successfully.')


if __name__ == '__main__':
    load_dotenv()
    main()
