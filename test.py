import json
import unittest
from datetime import datetime, timedelta
from pprint import pprint

import jwt

from server import app


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
        pub_key = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"
        signed_challenge = self._request_challenge(pub_key)
        challenge = self._get_data_unsafe(signed_challenge)
        self.assertEqual(challenge["aud"], "MS2 challenge")
        self.assertEqual(challenge["iss"], "Neufund")
        self.assertEqual(challenge["pub_key"], pub_key)

    def testChallengeTimeout(self):
        pub_key = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"
        signed_challenge = self._request_challenge(pub_key)
        challenge = self._get_data_unsafe(signed_challenge)
        # Actual timeout is 10 seconds
        now_plus_5_sec = self._timestamp(datetime.now() + timedelta(seconds=5))
        now_plus_15_sec = self._timestamp(datetime.now() + timedelta(seconds=15))
        self.assertIn(challenge["exp"], range(now_plus_5_sec, now_plus_15_sec))

    def testChallengeResponse(self):
        pub_key = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"
        signed_token = self._login(pub_key)
        token = self._get_data_unsafe(signed_token)
        self.assertEqual(token['aud'], "MS2")

    def testTokenTimeout(self):
        pub_key = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"
        signed_token = self._login(pub_key)
        token = self._get_data_unsafe(signed_token)
        # Actual timeout is 30 minutes
        now_plus_25_min = self._timestamp(datetime.now() + timedelta(minutes=25))
        now_plus_35_min = self._timestamp(datetime.now() + timedelta(minutes=35))
        self.assertIn(token['exp'], range(now_plus_25_min, now_plus_35_min))

    def testDataFetch(self):
        pub_key = "0x45ad9df0526109ba95ca6aa099833c04c9220f19"
        signed_token = self._login(pub_key)
        data = self._get_user_data(signed_token).decode('utf-8')
        self.assertEqual(data, pub_key)
