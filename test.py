import json
import unittest
from datetime import datetime, timedelta

import jwt
from multimerchant.wallet import Wallet
from multimerchant.wallet.keys import PublicKey

import db
from server import app

BASE_PATH = "m/44'/60'/0'"
TEST_DB = "test.json"


class LedgerJWTServerTestsBase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config["DB_NAME"] = TEST_DB
        self.base_address_hash = "01b0021097fc768ec42c1828be5131e18b479ab210224122e467f144018396df"
        test_data = db.get(self.base_address_hash)
        self.x_wallet = Wallet(chain_code=test_data["chainCode"],
                               public_key=PublicKey.from_hex_key(test_data["pubKey"]))

    def _request_challenge(self):
        return self.app.post(
            '/challenge',
            data=json.dumps({"base_address_hash": self.base_address_hash}),
            content_type='application/json'
        ).data

    def _solve_challenge(self, token, response_address):
        token = token.decode('utf-8')
        return self.app.post(
            '/response',
            data=json.dumps({"address": response_address}),
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data

    def _get_user_data(self, token):
        token = token.decode('utf-8')
        return self.app.get(
            '/data',
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data

    @staticmethod
    def _get_data_unsafe(signed):
        return jwt.decode(signed, options={
            'verify_signature': False,
            'verify_aud': False
        })

    def _login(self):
        signed_challenge = self._request_challenge()
        challenge = self._get_data_unsafe(signed_challenge)
        path = challenge["path"]
        self.assertEqual(path[:len(BASE_PATH)], BASE_PATH)
        x_y_path = path[len(BASE_PATH) + 1:]
        y_path = "/".join(x_y_path.split('/')[3:])
        address = self.x_wallet.get_child_for_path(y_path).to_address()
        return self._solve_challenge(signed_challenge, address)

    @staticmethod
    def _timestamp(time):
        return int(time.strftime("%s"))


class ChallengeResponseTests(LedgerJWTServerTestsBase):
    def testChallenge(self):
        signed_challenge = self._request_challenge()
        header = jwt.get_unverified_header(signed_challenge)
        challenge = self._get_data_unsafe(signed_challenge)
        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(challenge["aud"], "Challenge")
        self.assertEqual(challenge["iss"], "Neufund")
        self.assertEqual(challenge["base_address_hash"], self.base_address_hash)
        self.assertIn("path", challenge)

    def testChallengeTimeout(self):
        signed_challenge = self._request_challenge()
        challenge = self._get_data_unsafe(signed_challenge)
        # Actual timeout is 60 seconds
        now_plus_55_sec = self._timestamp(datetime.now() + timedelta(seconds=55))
        now_plus_65_sec = self._timestamp(datetime.now() + timedelta(seconds=65))
        self.assertIn(challenge["exp"], range(now_plus_55_sec, now_plus_65_sec))

    def testChallengeResponse(self):
        signed_token = self._login()
        header = jwt.get_unverified_header(signed_token)
        token = self._get_data_unsafe(signed_token)
        self.assertEqual(header["alg"], "ES512")
        self.assertEqual(token['aud'], "MS2")

    def testTokenTimeout(self):
        signed_token = self._login()
        token = self._get_data_unsafe(signed_token)
        # Actual timeout is 30 minutes
        now_plus_25_min = self._timestamp(datetime.now() + timedelta(minutes=25))
        now_plus_35_min = self._timestamp(datetime.now() + timedelta(minutes=35))
        self.assertIn(token['exp'], range(now_plus_25_min, now_plus_35_min))


class AdminTests(LedgerJWTServerTestsBase):
    pass
