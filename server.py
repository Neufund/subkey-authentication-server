import random
from datetime import timedelta

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
    signed = auth.sign(data, audience="MS2 challenge", ttl=timedelta(seconds=10))
    return signed


@app.route('/solution', methods=['POST'])
@auth.logged_in(audience="MS2 challenge")
def solution():
    pub_key = request.authorization["pub_key"]
    # TODO Verify challenge response
    return auth.sign({"pub_key": pub_key}, audience="MS2", ttl=timedelta(minutes=30))


@app.route('/data', methods=["GET"])
@auth.logged_in(audience="MS2")
def data():
    pub_key = request.authorization["pub_key"]
    return pub_key


if __name__ == '__main__':
    app.run()
