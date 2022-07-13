#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import signal
import sys
from pathlib import Path
from platform import platform

from dotenv import load_dotenv
from loguru import logger
from selenium.common.exceptions import WebDriverException

from reddit_gen.handlers import keyboard_interrupt_handler
from reddit_gen.generator import check_driver_path, generate, load_driver
from reddit_gen.utils import update_account_metadata


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
    parser.add_argument('-e',
                        '--env-file',
                        help='Path to the .env file. Defaults to .env in the '
                        'current directory')
    parser.add_argument('-D',
                        '--debug',
                        help='Debug mode',
                        action='store_true')
    parser.add_argument('-U',
                        '--update-database',
                        help='Update accounts metadata (MongoDB-only)',
                        action='store_true')
    parser.add_argument('--experimental-use-vpn', action='store_true')
    return parser.parse_args()


def main():
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    args = _opts()

    if not args.env_file:
        args.env_file = f'{Path.cwd()}/.env'
    load_dotenv(args.env_file)

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
                     env_file=args.env_file)
        except Exception as e:
            logger.exception(e)
            driver.quit()
            logger.debug('Terminated the driver successfully.')


if __name__ == '__main__':
    load_dotenv()
    main()
