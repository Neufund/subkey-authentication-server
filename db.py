import json
from unqlite import UnQLite


def load_fixture(name, db_name, append=True):
    with open("fixtures/{}".format(name), "r") as f:
        fixture = json.loads(f.read())
    if not append:
        open(db_name, "w").close()  # Clear DB
    with UnQLite(db_name) as db:
        for key, value in fixture.items():
            db[key] = json.dumps(value)
