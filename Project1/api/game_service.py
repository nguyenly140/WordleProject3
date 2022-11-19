import collections
import dataclasses
import sqlite3
import textwrap
import random

import databases
import toml
import uuid

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)

#@dataclasses.dataclass
#class Game:
#    username: str

@dataclasses.dataclass
class Guess:
    guess: str
    game_id: str


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

@app.route("/game/", methods=["GET"])
async def game():
    return "Starting game"

# =======================================
# =========== GAME API ROUTES ===========
# =======================================

@app.route("/game/new", methods=["POST"])
#@validate_request(Game)
async def create_game():
    db = await _get_db()

    username = request.authorization["username"]

    #testing for storage into db
    #try:
    #    await db.execute(
    #            """
    #            INSERT INTO users(username)
    #            VALUES(:username);
    #            """,
    #            values={"username": username}
    #            )
    #except sqlite3.IntegrityError as e:
    #    abort(409, e)

    # Get a random word for the secret word
    rand = random.randint(1, 2309)
    secretWord = await db.fetch_one("SELECT word FROM answers WHERE answer_id = :answer_id"
    , values={"answer_id": rand})

    # inserts game into db
    test = str(uuid.uuid4())
    game = {'game_id': test, "username": username, 'guessAmount': 6, 'secretWord': secretWord[0]}
    try:
        id = await db.execute(
            """
            INSERT INTO game(game_id, username, guessAmount, secretWord)
            VALUES(:game_id, :username, :guessAmount, :secretWord);
            """,
            game
         )
    except sqlite3.IntegrityError as e:
        abort(409, e)
    return { "gameId": test, "username": username }

# Get all games for a certain user
@app.route("/game/getGames", methods=["GET"])
async def get_games():
    db = await _get_db()

    username = request.authorization["username"]

    # gets all current games for that user
    games = await db.fetch_all("SELECT game_id, finished FROM game WHERE username = :username and finished = False"
    , values={"username": username})
    listOfGames = []
    if games:
        for x in games:
            listOfGames.append({"gamed_id:": x[0]})
        return listOfGames
    else:
        abort(404)

def letter_exists(letter, *list):
    for x in list:
        if (x == letter):
            return True
    return False

async def evaluate_word(secret_word, guess_word):
    correct = [0]    # stores all letter in the correct location
    exist = [0]      # stores all letters that exist in word
    correctWithSpots=[0]
    incorrect = [0]  # stores all letters that aren't in the word
    for g, gl in enumerate(guess_word):
        for s, sl in enumerate(secret_word):
            if (sl == gl and s == g):
                correct.append(gl)
                correctWithSpots.append({"letter": gl, "spot": g})
            elif (sl == gl and (not(letter_exists(gl, *exist)))):
                exist.append(gl)
        if (not(letter_exists(gl, *correct)) and not(letter_exists(gl, *exist))):
            incorrect.append(gl)

    # remove the 0 placeholder from each array
    correctWithSpots.pop(0)
    exist.pop(0)
    incorrect.pop(0)

    return {"correct": correctWithSpots, "exist": exist, "incorrect": incorrect}

# Make a guess for a game
@app.route("/game/makeGuess", methods=["POST"])
@validate_request(Guess)
async def make_guess(data):
    db = await _get_db()
    guess = dataclasses.asdict(data)

    username = request.authorization["username"]

    # TODO
    # Prepare all data for guess

    secretWord = None

    game = await db.fetch_one("SELECT secretWord, finished, guessAmount FROM game WHERE game_id = :game_id AND username = :username"
    , values={"game_id": guess["game_id"], "username": username})
    if (game):
        # game is not finished
        if(game[1] == 0 and game[2] != 0):
            secretWord = game[0]
        elif (game[1] == True and game[2] > 0):
            return {"guessAmount": game[2], "solved": True}
        elif (game[1] == True and game[2] <= 0):
            return {"guessAmount": 0, "solved": False}
    else:
        abort(404)

    # !!!! USE THESE AND "SecretWord" !!!!
    guessWord = guess["guess"]
    game_id = guess["game_id"]

    # TODO
    # Check the guess if valid

    value = await db.fetch_one("SELECT EXISTS(SELECT 1 FROM validGuess WHERE word= :guessWord)"
    , values={"guessWord": guessWord})
    value2 = await db.fetch_one("SELECT EXISTS(SELECT 1 FROM answers WHERE word= :guessWord)"
    , values={"guessWord": guessWord})
    if (value[0] or value2[0] or guessWord == secretWord):

        # add guess to guess table and decrement guess amount
        guess = {'guess_word': guessWord, 'game_id': game_id}
        try:
            id = await db.execute(
                """
                INSERT INTO guess(game_id, guess_word)
                VALUES(:game_id, :guess_word);
                """,
                guess,
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)

        payload = {"guessAmount": game[2] - 1,"game_id": game_id}
        try:
            id = await db.execute(
                """
                UPDATE game SET guessAmount = :guessAmount WHERE game_id = :game_id
                """,
                payload,
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)

        if (guessWord == secretWord or game[2] == 0):
            payload = {"finished": True,"game_id": game_id}
            try:
                id = await db.execute(
                    """
                    UPDATE game SET finished = :finished WHERE game_id = :game_id
                    """,
                    payload,
                    )
            except sqlite3.IntegrityError as e:
                abort(409, e)

            if (game[2] == 0):
                remaining = game[2]
                correct = False
            else:
                remaining = game[2] - 1,
                correct = True
            return {
                "Guess_valid": True,
                "Guess_correct": correct ,
                "Guesses_remaining": remaining,
            }

        # Gets the actual past guesses/ guess words as "guess"
        guesses = await db.fetch_all("SELECT guess_word as guess FROM guess WHERE game_id = :game_id"
        , values={"game_id": game_id})

        # get all past results for each guess
        data = []
        for x in guesses:
            guess = x[0]
            res = await evaluate_word(secretWord, guess)
            data.append({"Guess": guess, "Results": res})


        # store all the guesses and results as a dictionary object
        listOfGuesses = list(map(dict, data))

        #return correct locations and letters for current guess
        locations = await evaluate_word(secretWord ,guessWord)

        # return all data as a JSON object if no guesses just return # guesses left
        if (guesses):
            return {
            "Guess_valid": True,
            "Guess_correct": False ,
            "Guesses_remaining": game[2] - 1,
            "pastGuesses": listOfGuesses,
            "Guess_results": {"guess": guessWord, "results": locations},
            }
        else:
            return {"guessesLeft": 0}

    else:
        return {"ERROR": "GUESS IS NOT A VALUD GUESS"}

# Get the status of a current game
@app.route("/game/gameStatus/<string:game_id>", methods=["GET"])
async def get_status(game_id):
    db = await _get_db()

    username = request.authorization["username"]

    # Get user_id to use later
    #user = await db.fetch_one("SELECT user FROM users WHERE username = :username"
    #, values={"username": username})
    #user_id = user[0]

    # Gets the number of guesses left for the game that user started
    numOfGuesses = 0
    game = await db.fetch_one("SELECT guessAmount, secretWord FROM game WHERE game_id = :game_id AND username = :username"
    , values={"game_id": game_id, "username": username})
    if (game):
        numOfGuesses = game[0]
    else:
        abort(404)

    # Gets the actual past guesses/ guess words as "guess"
    guesses = await db.fetch_all("SELECT guess_word as guess FROM guess WHERE game_id = :game_id"
    , values={"game_id": game_id})

    # get all past results for each guess
    data = []
    for x in guesses:
        guess = x[0]
        secretWord = game[1]
        res = await evaluate_word(secretWord, guess)
        data.append({"Guess": guess, "Results": res})


    # store all the guesses and results as a dictionary object
    listOfGuesses = list(map(dict, data))


    # return all data as a JSON object if no guesses just return # guesses left
    if (guesses):
        return {"pastGuesses": listOfGuesses, "guessesLeft": numOfGuesses}
    else:
        return {"guessesLeft": numOfGuesses}

    abort(410)
