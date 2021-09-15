import json
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

try:
    from default_settings import default_settings  # noqa
except ModuleNotFoundError:
    pass

settings = {}


class MyException(Exception):
    pass


def sgetattr(e, attribute):
    return e.get_attribute(attribute)


def options_element(parent_element):
    child_element = parent_element.find_element(By.TAG_NAME, 'select')
    selected_opt = \
        [x for x in child_element.find_elements(By.TAG_NAME, 'option')
         if sgetattr(x, 'selected')][0]
    return child_element, selected_opt


def available_interface_languages():
    interface_language_opts = []
    for e in settings['lang']['element'].find_elements(By.TAG_NAME, 'option'):
        interface_language_opts.append(e.text)
    return interface_language_opts


def build_settings(driver):
    def dict_u(element, value_attr_string, **args):
        value = sgetattr(element, value_attr_string)
        try:
            label_ = labels[sgetattr(element, 'id')]['text']
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
            key = sgetattr(element, 'id')
            if not key:
                key = sgetattr(element, 'name')
        setting_d = {key: {
            'value': value,
            'label': label_,
            'element': element}}
        settings.update(setting_d)
        return setting_d

    labels = {}

    driver.get('https://old.reddit.com/prefs/')
    labels_ = driver.find_elements(By.TAG_NAME, 'label')

    for label in labels_:
        for_ = sgetattr(label, 'for')
        labels.update({for_: {'text': label.text,
                              'element': label}})

    dict_u(driver.find_element(By.ID, 'lang'), 'value')

    media = driver.find_element(By.CLASS_NAME, 'preferences-media')
    for e in media.find_elements(By.TAG_NAME, 'input'):
        if sgetattr(e, 'id') in ['video_autoplay', 'no_profanity']:
            if not sgetattr(e, 'checked'):
                dict_u(e, 'checked')
            if sgetattr(e, 'disabled'):
                dict_u(e, 'checked')

    for item in ['video_autoplay', 'no_profanity']:
        dict_u(driver.find_element(By.ID, item), 'checked')

    trs = driver.find_elements(By.TAG_NAME, 'tr')
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
            if sgetattr(e, 'id'):
                dict_u(e, 'checked')
            else:
                dict_u(e, 'value')
        if th.text in ['link options', 'comment options']:
            child, opt = options_element(current_options)
            dict_u(opt, 'value', key=sgetattr(child, 'name'))

    for e in driver.find_elements(By.TAG_NAME, 'select'):
        if e.get_attribute('name') == 'numsites':
            for child_e in e.find_elements(By.TAG_NAME, 'option'):
                if child_e.get_attribute('selected'):
                    settings.update({'numsites': {
                        'value': child_e.text,
                        'label': 'display [n] links at once',
                        'element': child_e}})
        elif e.get_attribute('name') == 'default_comment_sort':
            for child_e in e.find_elements(By.TAG_NAME, 'option'):
                if child_e.get_attribute('selected'):
                    settings.update({'default_comment_sort': {
                        'value': child_e.text,
                        'label': 'sort comments by',
                        'element': child_e}})

    return settings


def disable_tracking(driver):
    driver.get('https://old.reddit.com/personalization')
    elements = [e for e in driver.find_elements(By.XPATH, '//*[@id]')
                if sgetattr(e, 'id')]
    ads = ['activity_relevant_ads', '3rd_party',
           '3rd_party_data_personalized_ads']
    for e in elements:
        if sgetattr(e, 'id') in ads:
            if sgetattr(e, 'checked'):
                e.click()
    driver.find_element(By.CLASS_NAME, 'PersonalizationPage__btn').click()


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

    with open('default_settings.py', 'w') as f:
        f.write('class default_settings:\n    ')
        f.writelines(lines)
        f.write('\n')


def change_settings(driver, mysettings):
    try:
        fname = Path(f'{__file__}/default_settings.py')
    except NameError:
        fname = Path('default_settings.py')
    if not Path(fname).exists():
        create_settings_file(mysettings)
        from default_settings import default_settings  # noqa

    if default_settings.no_profanity and not default_settings.over_18:
        default_settings.over_18 = False
    if default_settings.label_nsfw and not default_settings.no_profanity:
        default_settings.no_profanity = False
    settings_items = list(set(default_settings.__dict__) & set(mysettings))

    for item in settings_items:
        value = dict(default_settings.__dict__)[item]
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
            for e in driver.find_elements(By.TAG_NAME, 'select'):
                if e.get_attribute('name') == item:
                    for child_e in e.find_elements(By.TAG_NAME, 'option'):
                        if child_e.get_attribute('selected'):
                            driver.execute_script(
                                'arguments[0].setAttribute("selected",'
                                'arguments[1])',
                                child_e, '')
                        if child_e.text == str(value):
                            driver.execute_script(
                                'arguments[0].setAttribute("selected",'
                                'arguments[1])',
                                child_e, 'selected')
