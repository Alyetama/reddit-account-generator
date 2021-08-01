# Reddit Accounts Generator


## Requirements
- [Google Chrome](https://www.google.com/chrome/)

## Getting started
### Clone this repository
```bash
$ git clone https://github.com/Alyetama/reddit_accounts_generator.git
$ cd reddit_accounts_generator
$ pip install -r requirements.txt
```

### Create an API key to use disposable emails
- You only need to do this step once!
1. Sign up on https://mailsac.com/register
2. Go to https://mailsac.com/api-keys
3. Click `Generate New API Secret` and copy the `Secret` string
5. Create an `.env` file in the respoitory, replacing `replace_this_with_the_api_key` with what you just copied:
```bash
$ echo "SECRET=replace_this_with_the_api_key" > .env
```

### Run the script
```bash
$ python create_reddit_account.py
```
