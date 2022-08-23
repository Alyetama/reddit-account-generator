# Reddit Account Generator


## Requirements
- [Google Chrome](https://www.google.com/chrome/)
- [Chrome Driver](https://chromedriver.chromium.org/downloads)
- *Optional, but recommended:* [MongoDB](https://www.mongodb.com/) (get a free database [here](https://www.mongodb.com/cloud/atlas/register)) 

## Getting started

### Step 1: Install the package
```sh
pip install -U reddit-gen
```

### Step 2: Configure your environment
```sh
reddit-gen --configure
```

## Usage

```
usage: reddit-gen [-h] [-d] [-s] [-i] [-j] [-p] [-n CREATE_N_ACCOUNTS]
                  [-c CONFIG_FILE] [-D] [-U] [--configure]
                  [--experimental-use-vpn]
                  [--check-subreddit-ban CHECK_SUBREDDIT_BAN] [-v]

options:
  -h, --help            show this help message and exit
  -d, --disable-headless
                        Disable headless mode
  -s, --solve-manually  Solve the captcha manually
  -i, --ip-rotated      The public IP address was changed by the user since
                        the last created account (to bypass the cooldown)
  -j, --use-json        Read from the local JSON database (pass if you're not
                        using MongoDB). A new local database will be created
                        if not found
  -p, --show-local-database-path
                        Prints the path to the local database, if exists
  -n CREATE_N_ACCOUNTS, --create-n-accounts CREATE_N_ACCOUNTS
                        Number of accounts to create (default: 1)
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Path to the config file. Defaults to
                        /Users/$USER/.redditgen.env
  -D, --debug           Debug mode
  -U, --update-database
                        Update accounts metadata (MongoDB-only)
  --configure           Configure your environment
  --experimental-use-vpn
                        Experimental feature (unstable)
  --check-subreddit-ban CHECK_SUBREDDIT_BAN
                        Check if your accounts are banned from a specific
                        subreddit (MongoDB-only)
  -v, --verbose         Print more logs
```

## Example

```sh
$ reddit-gen
# ───────────────────────────────── Starting... ─────────────────────────────────
# 2022-06-20 17:22:42.739 | INFO     | reddit_gen.generator:_signup_info:65 - Your account\'s email address: some_random_username@example.com
# 2022-06-20 17:22:42.739 | INFO     | reddit_gen.generator:_signup_info:67 - Username: some_random_username
# 2022-06-20 17:22:45.976 | DEBUG    | reddit_gen.generator:generate:196 - Solving captcha...
# 2022-06-20 17:24:12.579 | DEBUG    | reddit_gen.generator:generate:200 - Solved!
# 2022-06-20 17:24:38.841 | DEBUG    | reddit_gen.generator:generate:263 - Checking account info...
# 2022-06-20 17:24:39.069 | DEBUG    | reddit_gen.generator:generate:266 - Passed!
# 2022-06-20 17:24:39.069 | INFO     | reddit_gen.generato──r:generate:274 - Account verified!
# ───────────────────────────────────── Done! ───────────────────────────────────
```
