# Ledger-JWT-Server [![Build Status](https://travis-ci.org/Neufund/Ledger-JWT-Server.svg?branch=master)](https://travis-ci.org/Neufund/Ledger-JWT-Server)
Ledger JWT auth server is used to authenticate `Ledger Nano S` (later `Nano`) owners.

## Features
* Admin can register a new `Nano`
* User with a registered `Nano` is able to receive a JWT which he can later use to login to different services

## Protocol documentation

### The path schema:
**`m/44'/60'/0'`***`/{x1}'/{x2}'/{x3}'`*`/{y1}/{y2}/{y3}`

  `\______________________________________________/`

  `x_y_path`

  `\_____________________________/`

  `x_path`

  `\__________/`

  `base_path`

### Storage
We store data in a simple json file. 
Take a look at [test.json](./test.json) to get a better understanding of a storage schema.
This file is also used as a test fixture. It has data for test `Nano`

Server has a `key -> value` storage of:
```
base_address_hash: {
    chainCode, (for given x_path)
    pubKey, (for given x_path)
    xPath
}
```
Initially it has only admin `Nano`, but later admin can add users devices.

### Admin protocol
* Admin calls `/start_registration` and it generates a random `x_path`
* Admin gets public key and a chain code for that `x_path`. This requires a `Nano`
* Admin calls `/register` wih this data and it gets written to the DB

### User protocol
* User calls `/challenge` and it generates random y_path
* User gets address for that `y_path`. This requires a `Nano`
* User calls `/response` with the generated address and gets a LOGIN_TOKEN

For more detailed API description take a look at API section below

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
        * path
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