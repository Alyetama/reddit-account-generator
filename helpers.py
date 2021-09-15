import json
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.theme import Theme


def custom_theme():
    my_theme = Theme({
        'critical': '#ff5555 bold',
        'warning': '#f1fa8c',
        'info': '#8be9fd',
        'OK': '#50fa7b'
    })
    return my_theme


def print_diff(obj1, obj2) -> str:
    def whitespace(string):
        return cols - len(re.sub(r'\[[^]]*]', '', string))

    s1 = json.dumps(obj1, indent=0).split('\n')
    s2 = json.dumps(obj2, indent=0).split('\n')

    try:
        cols = os.get_terminal_size()
        cols = cols.columns
    except OSError:
        cols = 80

    any_diff = False
    skipped = []

    cprints = []

    for n, (x, y) in enumerate(zip(s1, s2)):
        e = ' ' * len(str(n))
        m = ' ' * (5 - len(str(n)))
        r = ' ' * (len(str(max(s1))) - (len(str(n))) + 2)
        if x not in ['{', '}']:
            dots = '·' * 4
        else:
            dots = ''
        if x != y:
            any_diff = True

            changed_x = f'[#C8D1D9 on #532425]{n}{m}{e}{r}' \
                        f'[#584D4F on #301B1E]{dots}[#C9D1D9 on #301B1E]{x} '
            changed_y = f'[#C8D1D9 on #1C4428]{e}{m}{n}{r}' \
                        f'[#49534E on #12261D]{dots}[#C9D1D9 on #12261D]{y}'
            if sys.stdout.isatty():
                cprints.append('\n'.join(skipped[-3:]))
                cprints.append(changed_x + ' ' * whitespace(changed_x))
                cprints.append(changed_y + ' ' * whitespace(changed_y))
            else:
                changed_x = '' + '"'.join(
                    f'{" ".join(changed_x.split())}'.split('"')[1:])
                changed_y = '"' + '"'.join(
                    f'{" ".join(changed_y.split())}'.split('"')[1:])
                cprints.append(f'{changed_x} ==> {changed_y}')
        elif x == y and sys.stdout.isatty():
            no_change = f'[#484F58 on #0C1117]{n}{m}{n}{r}' \
                        f'[#C9D1D9 on #0D1117]{dots}{x}'
            if n > len(s1) - 4 and any_diff is True:
                cprints.append(no_change + ' ' * whitespace(no_change))
            else:
                skipped.append(no_change + ' ' * whitespace(no_change))

    cprints = [
        cprints[i] for i in range(len(cprints))
        if (i == 0) or cprints[i] != cprints[i - 1]
    ]
    for line in cprints:
        cprint(line)

    return '\n'.join(cprints)


console = Console(theme=custom_theme())
cprint = console.print
data_path = f'{Path(__file__).parent}/reddit_accounts.json'
