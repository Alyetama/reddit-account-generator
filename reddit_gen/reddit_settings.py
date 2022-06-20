#!/usr/bin/env python
# coding: utf-8

import json
import time
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from reddit_gen.default_settings import ResetSettings, DefaultSettings


class MyException(Exception):
    pass


class RedditSettings:

    def __init__(self, driver):
        self.driver = driver
        self.settings = {}
        self.labels = {}

    @staticmethod
    def sgetattr(e, attribute):
        return e.get_attribute(attribute)

    def options_element(self, parent_element):
        child_element = parent_element.find_element(By.TAG_NAME, 'select')
        selected_opt = \
            [x for x in child_element.find_elements(By.TAG_NAME, 'option')
             if self.sgetattr(x, 'selected')][0]
        return child_element, selected_opt

    def available_interface_languages(self):
        interface_language_opts = []
        for e in self.settings['lang']['element'].find_elements(
                By.TAG_NAME, 'option'):
            interface_language_opts.append(e.text)
        return interface_language_opts

    def dict_u(self, element, value_attr_string, **args):
        value = self.sgetattr(element, value_attr_string)
        try:
            label_ = self.labels[self.sgetattr(element, 'id')]['text']
        except KeyError:
            label_ = ''
        if not value:
            value = False
        else:
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                if isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        pass
        try:
            key = args.pop('key')
        except KeyError:
            key = None
        if not key:
            key = self.sgetattr(element, 'id')
            if not key:
                key = self.sgetattr(element, 'name')
        setting_d = {
            key: {
                'value': value,
                'label': label_,
                'element': element
            }
        }
        self.settings.update(setting_d)
        return setting_d

    def build_settings(self):
        self.driver.get('https://old.reddit.com/prefs/')
        labels_ = self.driver.find_elements(By.TAG_NAME, 'label')

        for label in labels_:
            for_ = self.sgetattr(label, 'for')
            self.labels.update({for_: {'text': label.text, 'element': label}})

        self.dict_u(self.driver.find_element(By.ID, 'lang'), 'value')

        media = self.driver.find_element(By.CLASS_NAME, 'preferences-media')
        for e in media.find_elements(By.TAG_NAME, 'input'):
            if self.sgetattr(e, 'id') in ['video_autoplay', 'no_profanity']:
                if not self.sgetattr(e, 'checked'):
                    self.dict_u(e, 'checked')
                if self.sgetattr(e, 'disabled'):
                    self.dict_u(e, 'checked')

        for item in ['video_autoplay', 'no_profanity']:
            self.dict_u(self.driver.find_element(By.ID, item), 'checked')

        trs = self.driver.find_elements(By.TAG_NAME, 'tr')
        t_elements = []

        for tr in trs:
            try:
                th = tr.find_element(By.TAG_NAME, 'th')
                t_elements.append((tr, th))
            except NoSuchElementException:
                continue

        t_elements = [(tr, th) for tr, th in t_elements if th.text != '']

        for tr, th in t_elements:
            if th.text in ['personalization options', 'media']:
                continue
            current_options = tr.find_element(By.CLASS_NAME, 'prefright')
            for e in current_options.find_elements(By.TAG_NAME, 'input'):
                if self.sgetattr(e, 'id'):
                    self.dict_u(e, 'checked')
                else:
                    self.dict_u(e, 'value')
            if th.text in ['link options', 'comment options']:
                child, opt = self.options_element(current_options)
                self.dict_u(opt, 'value', key=self.sgetattr(child, 'name'))

        for e in self.driver.find_elements(By.TAG_NAME, 'select'):
            if e.get_attribute('name') == 'numsites':
                for child_e in e.find_elements(By.TAG_NAME, 'option'):
                    if child_e.get_attribute('selected'):
                        self.settings.update({
                            'numsites': {
                                'value': child_e.text,
                                'label': 'display [n] links at once',
                                'element': child_e
                            }
                        })
            elif e.get_attribute('name') == 'default_comment_sort':
                for child_e in e.find_elements(By.TAG_NAME, 'option'):
                    if child_e.get_attribute('selected'):
                        self.settings.update({
                            'default_comment_sort': {
                                'value': child_e.text,
                                'label': 'sort comments by',
                                'element': child_e
                            }
                        })

        return self.settings

    def disable_tracking(self):
        self.driver.get('https://old.reddit.com/personalization')
        elements = [
            e for e in self.driver.find_elements(By.XPATH, '//*[@id]')
            if self.sgetattr(e, 'id')
        ]
        ads = [
            'activity_relevant_ads', '3rd_party',
            '3rd_party_data_personalized_ads'
        ]
        for e in elements:
            if self.sgetattr(e, 'id') in ads:
                if self.sgetattr(e, 'checked'):
                    e.click()
        self.driver.find_element(By.CLASS_NAME,
                                 'PersonalizationPage__btn').click()

    @staticmethod
    def create_settings_file(settings_):
        lines = []
        for k, v in settings_.items():
            if k == 'numsites':
                label = '  # [10, 25, 50, 100]'
            elif k == 'num_comments':
                label = '  # 1-500'
            elif k in ['min_link_score', 'min_comment_score']:
                label = f'  # leave blank to show all'
            elif v['label']:
                label = f'  # {v["label"]}'
            else:
                label = ''
            value = v['value']
            if not isinstance(value, (bool, type(None))):
                try:
                    value = int(value)
                except ValueError:
                    value = f'"{value}"'
            lines.append(f'{k.replace("-", "_")} = {value}{label}')
        lines = '\n    '.join([line.lstrip() for line in lines])

        with open(f'{Path(__file__).parent}/default_settings.py', 'w') as f:
            f.write('class ResetSettings:\n    ')
            f.write('reset = False\n\n')
            f.write('class default_settings:\n    ')
            f.writelines(lines)
            f.write('\n')

    def change_settings(self):
        mysettings = self.build_settings()
        if not Path(f'{Path(__file__).parent}/default_settings.py').exists():
            self.create_settings_file(mysettings)
            if ResetSettings.reset:
                self.create_settings_file(mysettings)

        if DefaultSettings.no_profanity and not DefaultSettings.over_18:
            DefaultSettings.over_18 = False
        if DefaultSettings.label_nsfw and not DefaultSettings.no_profanity:
            DefaultSettings.no_profanity = False
        settings_items = list(set(DefaultSettings.__dict__) & set(mysettings))

        for item in settings_items:
            value = dict(DefaultSettings.__dict__)[item]
            element = mysettings[item]['element']
            try:

                if item in ['numsites', 'default_comment_sort']:
                    raise MyException
                int(str(value))
                element.clear()
                element.send_keys(value)
            except ValueError:
                if isinstance(value, bool):
                    if value is not mysettings[item]['value']:
                        element.click()
            except MyException:
                for e in self.driver.find_elements(By.TAG_NAME, 'select'):
                    if e.get_attribute('name') == item:
                        for child_e in e.find_elements(By.TAG_NAME, 'option'):
                            if child_e.get_attribute('selected'):
                                self.driver.execute_script(
                                    'arguments[0].setAttribute("selected",'
                                    'arguments[1])', child_e, '')
                            if child_e.text == str(value):
                                self.driver.execute_script(
                                    'arguments[0].setAttribute("selected",'
                                    'arguments[1])', child_e, 'selected')
        time.sleep(1)
        self.driver.find_element(By.CLASS_NAME, 'save-preferences').click()
        time.sleep(2)
