import random
import string

LEDGER_BASE_PATH = "m/44'/60'/0'"
DB_NAME = 'main.db'
CHALLENGE_ALGORITHM = 'HS512'
LOGIN_ALGORITHM = 'ES512'
ISSUER = 'Neufund'
CHALLENGE_AUDIENCE = "Challenge"
MS2_AUDIENCE = "MS2"

PRIV_KEY_PATH = "ec512.prv.pem"
PUB_KEY_PATH = "ec512.pub.pem"

HMAC_KEY_LENGTH = 64
HMAC_KEY = ''.join(
    random.SystemRandom().choice(string.ascii_uppercase + string.digits)
    for _ in range(HMAC_KEY_LENGTH))

PRIVATE_ECDSA_KEY = None
PUBLIC_ECDSA_KEY = None


def read_keys():
    global PRIVATE_ECDSA_KEY, PUBLIC_ECDSA_KEY
    from server import app
    with open(PRIV_KEY_PATH, "r") as privateKey:
        PRIVATE_ECDSA_KEY = privateKey.read()
    with open(PUB_KEY_PATH, "r") as publicKey:
        PUBLIC_ECDSA_KEY = publicKey.read()


read_keys()
