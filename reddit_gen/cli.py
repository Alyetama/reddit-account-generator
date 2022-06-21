#!/usr/bin/env python
# coding: utf-8

import argparse
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from reddit_gen.handlers import keyboard_interrupt_handler
from reddit_gen.generator import check_driver_path, generate, load_driver


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
                        type=int)
    parser.add_argument('-D',
                        '--debug',
                        help='Debug mode',
                        action='store_true')
    parser.add_argument('--experimental-use-vpn', action='store_true')
    return parser.parse_args()


def main():
    load_dotenv()
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    args = _opts()
    if args.show_local_database_path:
        local_db = f'{Path.home()}/.reddit_accounts.json'
        if Path(local_db).exists():
            print(local_db)
        else:
            logger.error(
                'Could not find a local database! Run the program at '
                'least once with the flag `--use-json` to generate it.')
        sys.exit(0)

    if args.experimental_use_vpn and not args.disable_headless:
        logger.error('Cannot use `--experimental-use-vpn` in headless mode!')
        sys.exit(1)

    driver_path = check_driver_path()
    driver = load_driver(driver_path,
                         disable_headless=args.disable_headless,
                         experimental_use_vpn=args.experimental_use_vpn,
                         solve_manually=args.solve_manually)

    for _ in range(args.create_n_accounts):
        try:
            generate(driver=driver,
                     disable_headless=args.disable_headless,
                     solve_manually=args.solve_manually,
                     ip_rotated=args.ip_rotated,
                     use_json=args.use_json,
                     debug=args.debug,
                     experimental_use_vpn=args.experimental_use_vpn)
        except Exception as e:
            logger.exception(e)
            driver.quit()
            logger.debug('Terminated the driver successfully.')


if __name__ == '__main__':
    main()
