-- $ sqlite3 ./var/wordle.db < ./share/wordle.sql

--PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    --user_id INTEGER primary key,
    username VARCHAR primary key,
    password VARCHAR,
    UNIQUE(username)
);

INSERT INTO users(username, password) VALUES('one','1pass');
INSERT INTO users(username, password) VALUES('two','2pass');
INSERT INTO users(username, password) VALUES('three','3pass');

COMMIT;
