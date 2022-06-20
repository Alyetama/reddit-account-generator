# Reddit Accounts Generator


## Requirements
- [Google Chrome](https://www.google.com/chrome/)
- [MongoDB](https://www.mongodb.com/) (get a free database [here](https://www.mongodb.com/cloud/atlas/register))

## Getting started
### Step 1: Clone this repository
```sh
git clone https://github.com/Alyetama/reddit_accounts_generator.git
cd reddit_accounts_generator
```

### Step 2: Build the package
```sh
pip install poetry
poetry build
pip install dist/*.whl
```

### Step 3: Edit the content of `.env`
```sh
mv .env.example .env
nano .env  # or any other editor
```

## Usage

```
$ reddit-gen -h         
usage: reddit-gen [-h] [-d] [-s] [-i] [-D]

optional arguments:
  -h, --help            show this help message and exit
  -d, --disable-headless
                        Disable headless mode
  -s, --solve-manually  Solve the captcha manually
  -i, --ip-rotated      The public IP address was changed by the user since the last created account (to bypass the cooldown)
  -D, --debug           Debug mode (logs all exceptions)
```

## Example

```
$ reddit-gen   
───────────────────────────────── Starting... ─────────────────────────────────
2022-06-20 17:22:42.739 | INFO     | reddit_gen.generator:_signup_info:65 - Your account's email address: john_87493@example.com
2022-06-20 17:22:42.739 | INFO     | reddit_gen.generator:_signup_info:67 - Username: john_87493
2022-06-20 17:22:45.976 | DEBUG    | reddit_gen.generator:generate:196 - Solving captcha...
2022-06-20 17:24:12.579 | DEBUG    | reddit_gen.generator:generate:200 - Solved!
2022-06-20 17:24:38.841 | DEBUG    | reddit_gen.generator:generate:263 - Checking account info...
2022-06-20 17:24:39.069 | DEBUG    | reddit_gen.generator:generate:266 - Passed!
2022-06-20 17:24:39.069 | INFO     | reddit_gen.generato──r:generate:274 - Account verified!
───────────────────────────────────── Done! ───────────────────────────────────
```
