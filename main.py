from datetime import datetime, timedelta

import jwt

DATA = {
    'some': 'payload'
}
CLAIMS = {
    # Expiration Time Claim
    'exp': datetime.utcnow() + timedelta(minutes=30),
    # Not Before Time Claim
    'nbf': datetime.utcnow(),
    # Issuer Claim
    'iss': 'Neufund',
    # Audience Claim
    'aud': 'MS2 investor',
    # Issued At Claim
    'iat': datetime.utcnow(),
}
PAYLOAD = {**DATA, **CLAIMS}
SECRET = 'secret'
signed = jwt.encode(PAYLOAD, SECRET, algorithm='HS512')
payload = jwt.decode(signed, SECRET,
                     audience='MS2 investor', issuer='Neufund', leeway=timedelta(minutes=1))
assert PAYLOAD == payload
print(payload)
