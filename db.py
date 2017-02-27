import json


def _read():
    from server import app
    with open(app.config["DB_NAME"], "r") as f:
        return json.loads(f.read())


def _write(data):
    from server import app
    with open(app.config["DB_NAME"], "w") as f:
        f.write(json.dumps(data))


def get(key):
    return _read()[key]


def put(key, value):
    data = _read()
    data[key] = value
    _write(data)
