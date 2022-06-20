#!/usr/bin/env python
# coding: utf-8

import sys

from loguru import logger


def keyboard_interrupt_handler(sig, _):
    logger.warning(f'KeyboardInterrupt (id: {sig}) has been caught...')
    logger.info('Terminating the session gracefully...')
    sys.exit(1)


def alarm_handler(sig, _):  # noqa
    raise TimeoutError('No response...')
