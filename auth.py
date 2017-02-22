from datetime import datetime
from functools import wraps

import jwt
from flask import request
from werkzeug.exceptions import Forbidden

ALGORITHM = 'HS512'
ISSUER = 'Neufund'


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
    from server import app
    return jwt.encode(payload, app.config["JWT_SECRET"], algorithm=ALGORITHM)


def verify(signed, audience):
    from server import app
    return jwt.decode(signed, app.config["JWT_SECRET"],
                      audience=audience, issuer=ISSUER, algorithms=ALGORITHM)


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
