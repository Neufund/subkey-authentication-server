import random

from flask import Flask, request

import auth

app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.route('/challenge', methods=['POST'])
def challenge():
    pub_key = request.get_json()["pub_key"]
    challenge_index = random.randint(0, 2 ** 31)
    data = {
        "pub_key": pub_key,
        "challenge_index": challenge_index
    }
    signed = auth.sign_challenge(data)
    return signed


@app.route('/solution', methods=['POST'])
@auth.verify_jwt(check=auth.verify_challenged)
def solution():
    pub_key = request.authorization["pub_key"]
    # TODO Verify challenge response
    return auth.sign_login_credentials({"pub_key": pub_key})


@app.route('/data', methods=["GET"])
@auth.verify_jwt(check=auth.verify_logged_in)
def data():
    pub_key = request.authorization["pub_key"]
    return pub_key


if __name__ == '__main__':
    app.run()
