#!/usr/bin/env python
# coding: utf-8

import argparse

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
    parser.add_argument('-D',
                        '--debug',
                        help='Debug mode (logs all exceptions)',
                        action='store_true')
    return parser.parse_args()


def main():
    load_dotenv()
    args = _opts()
    generate(disabled_headless=args.disabled_headless,
             solve_manually=args.solve_manually,
             ip_rotated=args.ip_rotated,
             debug=args.debug,
             experimental_use_vpn=False)


if __name__ == '__main__':
    main()
