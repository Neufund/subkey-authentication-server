import json
import unittest
from datetime import datetime, timedelta

import jwt

from server import app

PUB_KEY = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"


class LedgerJWTServerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def _request_challenge(self, pub_key):
        return self.app.post(
            '/challenge',
            data=json.dumps({"pub_key": pub_key}),
            content_type='application/json'
        ).data

    def _solve_challenge(self, jwt):
        jwt = jwt.decode('utf-8')
        return self.app.post(
            '/solution',
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

    def _login(self, pub_key):
        signed_challenge = self._request_challenge(pub_key)
        return self._solve_challenge(signed_challenge)

    @staticmethod
    def _timestamp(datetime):
        return int(datetime.strftime("%s"))

    def testChallenge(self):
        signed_challenge = self._request_challenge(PUB_KEY)
        header = jwt.get_unverified_header(signed_challenge)
        challenge = self._get_data_unsafe(signed_challenge)
        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(challenge["aud"], "Challenge")
        self.assertEqual(challenge["iss"], "Neufund")
        self.assertEqual(challenge["pub_key"], PUB_KEY)

    def testChallengeTimeout(self):
        signed_challenge = self._request_challenge(PUB_KEY)
        challenge = self._get_data_unsafe(signed_challenge)
        # Actual timeout is 60 seconds
        now_plus_55_sec = self._timestamp(datetime.now() + timedelta(seconds=55))
        now_plus_65_sec = self._timestamp(datetime.now() + timedelta(seconds=65))
        self.assertIn(challenge["exp"], range(now_plus_55_sec, now_plus_65_sec))

    def testChallengeResponse(self):
        signed_token = self._login(PUB_KEY)
        header = jwt.get_unverified_header(signed_token)
        token = self._get_data_unsafe(signed_token)
        self.assertEqual(header["alg"], "ES512")
        self.assertEqual(token['aud'], "MS2")

    def testTokenTimeout(self):
        signed_token = self._login(PUB_KEY)
        token = self._get_data_unsafe(signed_token)
        # Actual timeout is 30 minutes
        now_plus_25_min = self._timestamp(datetime.now() + timedelta(minutes=25))
        now_plus_35_min = self._timestamp(datetime.now() + timedelta(minutes=35))
        self.assertIn(token['exp'], range(now_plus_25_min, now_plus_35_min))

    def testDataFetch(self):
        signed_token = self._login(PUB_KEY)
        data = self._get_user_data(signed_token).decode('utf-8')
        self.assertEqual(data, PUB_KEY)
