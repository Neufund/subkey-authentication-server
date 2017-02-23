import random
import string
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import request
from werkzeug.exceptions import Forbidden

CHALLENGE_ALGORITHM = 'HS512'
LOGIN_ALGORITHM = 'ES512'
ISSUER = 'Neufund'
CHALLENGE_AUDIENCE = "Challenge"
MS2_AUDIENCE = "MS2"

with open("ec512.prv.pem", "r") as privateKey:
    PRIVATE_ECDSA_KEY = privateKey.read()

with open("ec512.pub.pem", "r") as publicKey:
    PUBLIC_ECDSA_KEY = publicKey.read()

HMAC_KEY_LENGTH = 64
HMAC_KEY = ''.join(
    random.SystemRandom().choice(string.ascii_uppercase + string.digits)
    for _ in range(HMAC_KEY_LENGTH))


def _get_claims(audience, ttl):
    return {
        # Expiration Time Claim
        'exp': datetime.utcnow() + ttl,
        # Not Before Time Claim
        'nbf': datetime.utcnow(),
        # Issuer Claim
        'iss': 'Neufund',
        # Audience Claim
        'aud': audience,
        # Issued At Claim
        'iat': datetime.utcnow()
    }


def sign_challenge(data):
    payload = {**data, **_get_claims(CHALLENGE_AUDIENCE, timedelta(minutes=1))}
    return jwt.encode(payload, HMAC_KEY, algorithm=CHALLENGE_ALGORITHM)


def sign_login_credentials(data):
    payload = {**data, **_get_claims(MS2_AUDIENCE, timedelta(minutes=30))}
    return jwt.encode(payload, PRIVATE_ECDSA_KEY, algorithm=LOGIN_ALGORITHM)


def verify_logged_in(token):
    return jwt.decode(token, PUBLIC_ECDSA_KEY,
                      audience=MS2_AUDIENCE,
                      issuer=ISSUER,
                      algorithms=LOGIN_ALGORITHM)


def verify_challenged(token):
    return jwt.decode(token, HMAC_KEY,
                      audience=CHALLENGE_AUDIENCE,
                      issuer=ISSUER,
                      algorithms=CHALLENGE_ALGORITHM)


def verify_jwt(check=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            auth_type, auth_value = auth_header.split()
            if auth_type != "JWT":
                return Forbidden("JWT required")
            auth_data = check(auth_value)
            request.authorization = auth_data
            return f(*args, **kwargs)

        return wrapped

    return decorator
