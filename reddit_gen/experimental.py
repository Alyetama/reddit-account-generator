#!/usr/bin/env python
# coding: utf-8

import time
import tempfile

import requests
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def vpn_driver(driver_path, disable_headless=True):
    ext_id = 'bihmplhobchoageeokmgbdihknkjbknd'

    with tempfile.NamedTemporaryFile(delete=False, suffix='.crx') as tmp:
        tmp.write(requests.get('https://ttm.sh/wLY.crx').content)
        tmp.seek(0)

    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    if not disable_headless:
        options.add_argument('headless')
    options.add_extension(tmp.name)
    driver = webdriver.Chrome(options=options, service=service)
    driver.get('https://www.whatismyip.com/')
    time.sleep(0.5)
    print(f'Extension_id: {ext_id}')
    try:
        driver.get(f'chrome-extension://{ext_id}/panel/index.html')

        if len(driver.window_handles) != 1:
            curr = driver.current_window_handle
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if handle != curr:
                    driver.close()
            driver.switch_to.window(curr)

        driver.find_element(By.ID, 'ConnectionButton').click()
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    time.sleep(10)

    res = requests.get('https://am.i.mullvad.net/ip')
    my_ip = res.content.decode('utf8').rstrip()
    driver.set_page_load_timeout(30)
    driver.get('https://am.i.mullvad.net/ip')
    vpn_ip = driver.find_element(By.TAG_NAME, 'body').text
    assert my_ip != vpn_ip
    return driver
