# Reddit Accounts Generator


## Requirements
- [Google Chrome](https://www.google.com/chrome/)

## Getting started
### Step 1: Clone this repository
```bash
$ git clone https://github.com/Alyetama/reddit_accounts_generator.git
$ cd reddit_accounts_generator
$ pip install -r requirements.txt
```

### Step 2: Email verification
To verify your emails on the accounts, you have two options:
1. Use a disposable email service (cons: your IP might be blocked if you're using a VPN).
2. Use one Gmail account, which will allows you to create unlimited aliases.

#### Option 1: Create an API key to use disposable emails
- You only need to do this step once!
1. Sign up on https://mailsac.com/register
2. Go to https://mailsac.com/api-keys
3. Click `Generate New API Secret` and copy the `Secret` string
5. Create an `.env` file in the respoitory, replacing `<MAILSEC_API_KEY>` with what you just copied:
```bash
$ echo "SECRET=<MAILSEC_API_KEY>" > .env
```

#### Option 2: Use a Gmail account*
1. Allow "less ssecure apps" by following the instructions [here](https://support.google.com/accounts/answer/6010255?hl=en).
2. Create an `.env` file in the respoitory, replacing `<YOUR_EMAIL>` with your email address:
```bash
$ echo "EMAIL=<YOUR_EMAIL>" > .env
```

### Step 3: Run the script
```bash
$ python create_reddit_account.py
```

---

## Additional notes

### Your data
Your accounts data file is encryoted by default, and the key is stored in your system's keyring service (e.g., Keychain, Windows Credential Locker, etc.).  You can unencrypt the data to view it by running:
```python
$ python encrypted_json.py
```

### Automatic reCAPTCHA solving
If you have an API key with 2Captcha, you can use the fully automated accounts generator. For this, you will need to store the API key in your keyring service, replacing <YOUR_API_KEY> with your 2Captcha API key.

```python
import keyring

keyring.set_password('secrets', 'reddit', '<YOUR_API_KEY>')
```

Then you can run the fully automated script:
```bash
$ python auto_generator.py
```

---

## Disclaimer
This project is a proof of concept and is made for educational purposes only. Users of this program are expected to follow [Reddit User Agreement](https://www.redditinc.com/policies/user-agreement-october-15-2020). Developers assume no liability and are not responsible for any misuse or damage caused by this program.
