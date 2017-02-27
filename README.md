# Ledger-JWT-Server [![Build Status](https://travis-ci.org/Neufund/Ledger-JWT-Server.svg?branch=master)](https://travis-ci.org/Neufund/Ledger-JWT-Server)
Ledger JWT auth server

## Setup

* On DEV:
    * Generate ECDSA keys by running `./generate_keys.sh`
    * Create virtualenv: `virtualenv -p python3.6 venv`
    * Enter virtualenv: `. venv/bin/activate`
    * Install dependencies: `pip install -r requirements.txt`
    * Run tests: `py.test`
    * Run server with reloading: `FLASK_DEBUG=1 FLASK_APP=server flask run`
* On PROD:
    * Load ECDSA keys from somewhere
    * Load DB data to `prod-data.json` from somewhere
    * Run server: `docker-compose up -d`

## API

### Admin endpoints

* Start registration (requires LOGIN_TOKEN)
    * `POST /start_registration {"base_address_hash": BASE_ADDRESS_HASH}`
    * `200 text/html REGISTRATION_TOKEN`
        * base_address_hash
        * path
* Registration (requires REGISTRATION_TOKEN)
    * `POST /register {"x_chain_code": X_CHAIN_CODE, "x_pub_key": X_PUB_KEY}`
    * `200 test/html BASE_ADDRESS_HASH`

### User endpoints

* Challenge
    * `POST /challenge {"base_address_hash": BASE_ADDRESS_HASH}`
    * `200 text/html CHALLENGE_TOKEN`
        * x_path
        * y_path
* Response (requires CHALLENGE_TOKEN)
    * `POST /response {"address": SOLUTION_ADDRESS}`
    * `200 text/html LOGIN_TOKEN`
        * base_address_hash

### Additional info

* Hash function used for address hashes is `sha3_256`, that's why `python3.6` is used

### Troubleshooting
* `#include <openssl/aes.h>` not found while installing dependencies
    * https://github.com/pyca/cryptography/issues/2350
    * This is due to Apple dropping support for OpenSSL and moving to their own library.