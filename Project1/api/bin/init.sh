#!/bin/sh

sqlite3 ./var/games.db < share/games.sql

sqlite3 ./var/users.db < share/users.sql
