from random import randint
from streql import equals

from flask import Flask, request
from multimerchant.wallet import Wallet
from multimerchant.wallet.keys import PublicKey
from werkzeug.exceptions import Unauthorized

import auth
import db

app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.route('/challenge', methods=['POST'])
def challenge():
    base_address_hash = request.get_json()["base_address_hash"]
    y1, y2, y3 = randint(0, 2 ** 31), randint(0, 2 ** 31), randint(0, 2 ** 31)
    xPath = db.get(base_address_hash)["xPath"]
    yPath = "{}/{}/{}".format(y1, y2, y3)
    challenge_data = {
        "base_address_hash": base_address_hash,
        "path": "{}/{}/{}".format(app.config["LEDGER_BASE_PATH"], xPath, yPath)
    }
    return auth.sign_challenge(challenge_data)


def solve_challenge(address, path):
    user_data = db.get(address)
    x_wallet = Wallet(chain_code=user_data["chainCode"],
                      public_key=PublicKey.from_hex_key(user_data["pubKey"]))
    y_path = "/".join(path.split("/")[-3:])
    return x_wallet.get_child_for_path(y_path).to_address()


@app.route('/response', methods=['POST'])
@auth.verify_jwt(check=auth.verify_challenged)
def response():
    base_address_hash = request.authorization["base_address_hash"]
    path = request.authorization["path"]
    expected_address = solve_challenge(base_address_hash, path)
    submitted_address = request.get_json()["address"]
    # Secure against timing attacks
    if not equals(submitted_address, expected_address):
        raise Unauthorized("Wrong challenge solution")
    return auth.sign_login_credentials({"base_address_hash": base_address_hash})


if __name__ == '__main__':
    app.run()
