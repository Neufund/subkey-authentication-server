import json
import unittest
from datetime import datetime, timedelta
from random import randint
from unqlite import UnQLite

import jwt
from multimerchant.wallet import Wallet
from multimerchant.wallet.keys import PublicKey

from server import app

PUB_KEY = "04d3c41fb2f0e07d71f10416717e450bceb635d54d9b07dea0327f90bfa82f0da08b40aaf" \
          "d480811d4aba8c17fa768765c6a897009e000f9249c299724fd567414"
CHAIN_CODE = "7e08e87e875b9f6bfde7e4a2ab6b52b6c3229bf5b8ac9856487d532bbdaaaee8"
ADDRESS = "0x670884349DD0E57bd1bb71bB6913E921846ba149"
WALLET = Wallet(chain_code=CHAIN_CODE, public_key=PublicKey.from_hex_key(PUB_KEY))
BASE_PATH = "m/44'/60'/0'"
TEST_DB = "test.db"


class LedgerJWTServerTestCase(unittest.TestCase):
    def resetDB(self):
        open(TEST_DB, 'w').close()

    def createFixture(self):
        with UnQLite(TEST_DB) as db:
            x1, x2, x3 = randint(0, 2 ** 31), randint(0, 2 ** 31), randint(0, 2 ** 31)
            xPath = "{}/{}/{}".format(x1, x2, x3)
            x_child = WALLET.get_child_for_path(xPath)
            x_child.get_public_key_hex(False)
            value = {
                "xPath": xPath,
                "pubKey": x_child.get_public_key_hex(False).decode('utf-8'),
                "chainCode": x_child.chain_code.decode('utf-8')
            }
            db[ADDRESS] = json.dumps(value)

    def setUp(self):
        self.app = app.test_client()
        app.config["DB_NAME"] = TEST_DB
        self.resetDB()
        self.createFixture()

    def tearDown(self):
        self.resetDB()

    def _request_challenge(self, address):
        return self.app.post(
            '/challenge',
            data=json.dumps({"address": address}),
            content_type='application/json'
        ).data

    def _solve_challenge(self, jwt, response_address):
        jwt = jwt.decode('utf-8')
        return self.app.post(
            '/response',
            data=json.dumps({"address": response_address}),
            headers={"Authorization": "JWT {}".format(jwt)},
            content_type='application/json'
        ).data

    def _get_user_data(self, jwt):
        jwt = jwt.decode('utf-8')
        return self.app.get(
            '/data',
            headers={"Authorization": "JWT {}".format(jwt)},
            content_type='application/json'
        ).data

    @staticmethod
    def _get_data_unsafe(signed):
        return jwt.decode(signed, options={
            'verify_signature': False,
            'verify_aud': False
        })

    def _login(self, address):
        signed_challenge = self._request_challenge(address)
        challenge = self._get_data_unsafe(signed_challenge)
        path = challenge["path"]
        self.assertEqual(path[:len(BASE_PATH)], BASE_PATH)
        path = path[len(BASE_PATH) + 1:]
        address = WALLET.get_child_for_path(path).to_address()
        return self._solve_challenge(signed_challenge, address)

    @staticmethod
    def _timestamp(datetime):
        return int(datetime.strftime("%s"))

    def testChallenge(self):
        signed_challenge = self._request_challenge(ADDRESS)
        header = jwt.get_unverified_header(signed_challenge)
        challenge = self._get_data_unsafe(signed_challenge)
        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(challenge["aud"], "Challenge")
        self.assertEqual(challenge["iss"], "Neufund")
        self.assertEqual(challenge["address"], ADDRESS)

    def testChallengeTimeout(self):
        signed_challenge = self._request_challenge(ADDRESS)
        challenge = self._get_data_unsafe(signed_challenge)
        # Actual timeout is 60 seconds
        now_plus_55_sec = self._timestamp(datetime.now() + timedelta(seconds=55))
        now_plus_65_sec = self._timestamp(datetime.now() + timedelta(seconds=65))
        self.assertIn(challenge["exp"], range(now_plus_55_sec, now_plus_65_sec))

    def testChallengeResponse(self):
        signed_token = self._login(ADDRESS)
        header = jwt.get_unverified_header(signed_token)
        token = self._get_data_unsafe(signed_token)
        self.assertEqual(header["alg"], "ES512")
        self.assertEqual(token['aud'], "MS2")

    def testTokenTimeout(self):
        signed_token = self._login(ADDRESS)
        token = self._get_data_unsafe(signed_token)
        # Actual timeout is 30 minutes
        now_plus_25_min = self._timestamp(datetime.now() + timedelta(minutes=25))
        now_plus_35_min = self._timestamp(datetime.now() + timedelta(minutes=35))
        self.assertIn(token['exp'], range(now_plus_25_min, now_plus_35_min))

    def testDataFetch(self):
        signed_token = self._login(ADDRESS)
        data = self._get_user_data(signed_token).decode('utf-8')
        self.assertEqual(data, ADDRESS)
