import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def vpn_driver(headless=False):
    service = Service('/opt/homebrew/bin/chromedriver')
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')
    ext_id = 'Touch_VPN.crx'
    options.add_extension(f'{ext_id}.crx')
    driver = webdriver.Chrome(options=options, service=service)
    driver.get('https://www.whatismyip.com/')
    time.sleep(0.5)
    driver.get(f'chrome-extension://{ext_id}/panel/index.html')

    if len(driver.window_handles) != 1:
        curr = driver.current_window_handle
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if handle != curr:
                driver.close()
        driver.switch_to.window(curr)

    driver.find_element(By.ID, 'ConnectionButton').click()
    time.sleep(10)

    res = requests.get('https://am.i.mullvad.net/ip')
    my_ip = res.content.decode('utf8').rstrip()
    driver.set_page_load_timeout(30)
    driver.get('https://am.i.mullvad.net/ip')
    vpn_ip = driver.find_element(By.TAG_NAME, 'body').text
    assert my_ip != vpn_ip
    return driver
