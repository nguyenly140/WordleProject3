import collections
import dataclasses
import sqlite3
import textwrap
import random

import databases
import toml

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)

@dataclasses.dataclass
class User:
    username: str
    password: str

async def _connect_db():
    database = databases.Database(app.config["DATABASES"]["URL"])
    await database.connect()
    return database


def _get_db():
    if not hasattr(g, "sqlite_db"):
        g.sqlite_db = _connect_db()
    return g.sqlite_db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.route("/user/", methods=["GET"])
async def user():
    return "Welcome user"

# =======================================
# =========== USER API ROUTES ===========
# =======================================

@app.route("/user/auth/<string:username>&<string:password>", methods=["GET"])
async def authenticate(username, password):
    db = await _get_db()
    user = await db.fetch_one("SELECT * FROM users WHERE username = :username AND password = :password"
    , values={"username": username, "password": password})
    if user:
        return {"authenticated": "True"}
        
    else:
        abort(404)
        

@app.route("/user/signup", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)
    try:
        id = await db.execute(
            """
            INSERT INTO users(username, password)
            VALUES(:username,:password);
            """,
            user,
        )
    except sqlite3.IntegrityError as e:
        abort(409, e)

    user["id"] = id
    return user, 201, {"Location": f"/user/{id}"}
      
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
