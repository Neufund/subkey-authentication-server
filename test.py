import hashlib
import json
import unittest
from datetime import datetime, timedelta

import jwt
from multimerchant.wallet import Wallet
from multimerchant.wallet.keys import PublicKey

import db
from config import LEDGER_BASE_PATH
from server import app

BASE_PATH = "m/44'/60'/0'"
TEST_DB = "test.json"


class LedgerJWTServerTestsBase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config["DB_NAME"] = TEST_DB

    def _request_challenge(self, base_address_hash):
        return self.app.post(
            '/challenge',
            data=json.dumps({"base_address_hash": base_address_hash}),
            content_type='application/json'
        ).data.decode("utf-8")

    def _solve_challenge(self, token, response_address):
        return self.app.post(
            '/response',
            data=json.dumps({"address": response_address}),
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data.decode("utf-8")

    def _get_user_data(self, token):
        return self.app.get(
            '/data',
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data.decode("utf-8")

    @staticmethod
    def _get_data_unsafe(signed):
        return jwt.decode(signed, options={
            'verify_signature': False,
            'verify_aud': False
        })

    def _login(self, base_address_hash, x_wallet):
        signed_challenge = self._request_challenge(base_address_hash)
        challenge = self._get_data_unsafe(signed_challenge)
        path = challenge["path"]
        self.assertEqual(path[:len(BASE_PATH)], BASE_PATH)
        x_y_path = path[len(BASE_PATH) + 1:]
        y_path = "/".join(x_y_path.split('/')[3:])
        address = x_wallet.get_child_for_path(y_path).to_address()
        return self._solve_challenge(signed_challenge, address)

    @staticmethod
    def _timestamp(time):
        return int(time.strftime("%s"))


class ChallengeResponseTests(LedgerJWTServerTestsBase):
    def setUp(self):
        super(ChallengeResponseTests, self).setUp()
        self.base_address_hash = "01b0021097fc768ec42c1828be5131e18b479ab210224122e467f144018396df"
        test_data = db.get(self.base_address_hash)
        self.x_wallet = Wallet(chain_code=test_data["chainCode"],
                               public_key=PublicKey.from_hex_key(test_data["pubKey"]))

    def testChallenge(self):
        signed_challenge = self._request_challenge(self.base_address_hash)
        header = jwt.get_unverified_header(signed_challenge)
        challenge = self._get_data_unsafe(signed_challenge)
        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(challenge["aud"], "Challenge")
        self.assertEqual(challenge["iss"], "Neufund")
        self.assertEqual(challenge["base_address_hash"], self.base_address_hash)
        self.assertIn("path", challenge)

    def testChallengeTimeout(self):
        signed_challenge = self._request_challenge(self.base_address_hash)
        challenge = self._get_data_unsafe(signed_challenge)
        # Actual timeout is 60 seconds
        now_plus_55_sec = self._timestamp(datetime.now() + timedelta(seconds=55))
        now_plus_65_sec = self._timestamp(datetime.now() + timedelta(seconds=65))
        self.assertIn(challenge["exp"], range(now_plus_55_sec, now_plus_65_sec))

    def testChallengeResponse(self):
        signed_token = self._login(self.base_address_hash, self.x_wallet)
        header = jwt.get_unverified_header(signed_token)
        token = self._get_data_unsafe(signed_token)
        self.assertEqual(header["alg"], "ES512")
        self.assertEqual(token['aud'], "MS2")

    def testTokenTimeout(self):
        signed_token = self._login(self.base_address_hash, self.x_wallet)
        token = self._get_data_unsafe(signed_token)
        # Actual timeout is 30 minutes
        now_plus_25_min = self._timestamp(datetime.now() + timedelta(minutes=25))
        now_plus_35_min = self._timestamp(datetime.now() + timedelta(minutes=35))
        self.assertIn(token['exp'], range(now_plus_25_min, now_plus_35_min))


class StateModifyingTestCaseMixin():
    def setUp(self):
        super(StateModifyingTestCaseMixin, self).setUp()
        self.initial_db_state = db.read()

    def tearDown(self):
        super(StateModifyingTestCaseMixin, self).tearDown()
        db.write(self.initial_db_state)


class AdminTests(StateModifyingTestCaseMixin, LedgerJWTServerTestsBase):
    def setUp(self):
        super(AdminTests, self).setUp()
        admin_base_address_hash = "01b0021097fc768ec42c1828be5131e18b479ab210224122e467f144018396df"
        test_data = db.get(admin_base_address_hash)
        admin_x_wallet = Wallet(chain_code=test_data["chainCode"],
                                public_key=PublicKey.from_hex_key(test_data["pubKey"]))
        self.token = self._login(admin_base_address_hash, admin_x_wallet)
        self.new_wallet = Wallet.new_random_wallet()
        base_address = self.new_wallet \
            .get_child_for_path(LEDGER_BASE_PATH) \
            .to_address().encode("utf-8")
        self.base_address_hash = hashlib.sha3_256(base_address).hexdigest()

    def _start_registration(self, token, base_address_hash):
        return self.app.post(
            '/start_registration',
            data=json.dumps({"base_address_hash": base_address_hash}),
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data.decode("utf-8")

    def _register(self, registration_token, pub_key, chain_code):
        return self.app.post(
            '/register',
            data=json.dumps({"x_pub_key": pub_key,
                             "x_chain_code": chain_code}),
            headers={"Authorization": "JWT {}".format(registration_token)},
            content_type='application/json'
        ).data.decode("utf-8")

    def _register_new_wallet(self, base_address_hash, wallet):
        registration_token = self._start_registration(self.token, base_address_hash)
        path = self._get_data_unsafe(registration_token)["path"]
        child_wallet = wallet.get_child_for_path(path)
        chain_code = child_wallet.chain_code.decode("utf-8")
        pub_key = child_wallet.public_key.get_key().decode("utf-8")
        return self._register(registration_token, pub_key, chain_code)

    def testStartRegistrationToken(self):
        registration_token = self._start_registration(self.token, self.base_address_hash)
        header = jwt.get_unverified_header(registration_token)
        registration_data = self._get_data_unsafe(registration_token)
        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(registration_data["aud"], "Registration")
        self.assertEqual(registration_data["iss"], "Neufund")
        self.assertEqual(registration_data["base_address_hash"], self.base_address_hash)
        self.assertIn("path", registration_data)

    def testStartRegistrationPath(self):
        registration_token = self._start_registration(self.token, self.base_address_hash)
        registration_data = self._get_data_unsafe(registration_token)
        path = registration_data["path"]
        self.assertRegexpMatches(path, LEDGER_BASE_PATH + "(/\\d{1,10}'){3}")

    def testRegistrationSucceeds(self):
        response = self._register_new_wallet(self.base_address_hash, self.new_wallet)
        self.assertEqual(response, self.base_address_hash)
