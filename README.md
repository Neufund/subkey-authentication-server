# Ledger-JWT-Server [![Build Status](https://travis-ci.org/Neufund/Ledger-JWT-Server.svg?branch=master)](https://travis-ci.org/Neufund/Ledger-JWT-Server)
Ledger JWT auth server

## Setup
* On DEV:
    * Generate ECDSA keys by running `./generate_keys.sh`
    * Create virtualenv: `virtualenv venv`
    * Enter virtualenv: `. venv/bin/activate`
    * Install dependencies: `pip install -r requirements.txt`
    * Run tests: `py.test test.py`
    * Run server with reloading: `FLASK_DEBUG=1 FLASK_APP=server flask run`
* On PROD:
    * Load ECDSA keys from somewhere
    * Load DB data to `prod-data.json` from somewhere
    * Run server: `docker-compose up -d`

## API
* Challenge
    * `POST /challenge {"address": BASE_ADDRESS}`
    * `200 text/html CHALLENGE_TOKEN`
* Response (requires CHALLENGE_TOKEN)
    * `POST /response {"address": SOLUTION_ADDRESS}`
    * `200 text/html LOGIN_TOKEN`
* Data (requires LOGIN_TOKEN)
    * `GET /data`
    * `200 text/html USER_DATA`