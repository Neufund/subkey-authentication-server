from datetime import datetime
from functools import wraps

import jwt
from flask import request
from werkzeug.exceptions import Forbidden

ALGORITHM = 'ES512'
ISSUER = 'Neufund'

with open("ec512.prv.pem", "r") as privateKey:
    PRIVATE_KEY = privateKey.read()

with open("ec512.pub.pem", "r") as publicKey:
    PUBLIC_KEY = publicKey.read()


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


def sign(data, audience, ttl):
    payload = {**data, **_get_claims(audience, ttl)}
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)


def verify(signed, audience):
    return jwt.decode(signed, PUBLIC_KEY, audience=audience, issuer=ISSUER, algorithms=ALGORITHM)


def logged_in(audience=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            auth_type, auth_value = auth_header.split()
            if auth_type != "JWT":
                return Forbidden("JWT required")
            auth_data = verify(auth_value, audience)
            request.authorization = auth_data
            return f(*args, **kwargs)

        return wrapped

    return decorator
