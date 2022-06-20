#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from reddit_gen.generator import generate


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
    parser.add_argument('-D',
                        '--debug',
                        help='Debug mode',
                        action='store_true')
    return parser.parse_args()


def main():
    load_dotenv()
    args = _opts()
    if args.show_local_database_path:
        local_db = f'{Path.home()}/.reddit_accounts.json'
        if Path(local_db).exists():
            print(local_db)
        else:
            print('Could not find a local database! Run the program at least '
                  'once with the flag `--use-json` to generate it.')
        sys.exit(0)

    generate(disable_headless=args.disable_headless,
             solve_manually=args.solve_manually,
             ip_rotated=args.ip_rotated,
             use_json=args.use_json,
             debug=args.debug,
             experimental_use_vpn=False)


if __name__ == '__main__':
    main()
