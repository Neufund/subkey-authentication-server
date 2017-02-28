import json


def read():
    from server import app
    with open(app.config["DB_NAME"], "r") as f:
        return json.loads(f.read())


def write(data):
    from server import app
    with open(app.config["DB_NAME"], "w") as f:
        f.write(json.dumps(data))


def get(key):
    return read()[key]


def put(key, value):
    data = read()
    data[key] = value
    write(data)
