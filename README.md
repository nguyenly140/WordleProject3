# WordleCPSC449
This is a project for class. An API and database system that can handle requests relating to the game "Wordle".
In this project we create two micro services and implement reverse proxys and load balancing.

Developed by:      |
Joshua Popp        |
Apeksha shah       |
Hardik Vagrecha    |
Ly Nguyen          |
                   |
7 PM: Tuesday Class|
Section-01         |
___________________|




Welcome to Project 2

Set-Up Instructions:
	1) Copy the nginx.txt contents into the nginx config file on your system
	2) Restart the nginx file with the nginx restart command
	3) Inside the api directory run "bin/init.sh" to initiate db
	4) Verify that the var folder contains a users.db and a games.db
	5) run "foreman start --formation users_service=1,game_service=3"
	6) The servers should be running after this
	7) Open a new terminal and begin making API calls below


API calls using http:

** anything in [] you type in **


	Sign-Up:                          http POST tuffix-vm/signUp username=[example] password=[example]

	Make new game:                    http --auth username:password POST tuffix-vm/makeGame

	Get all current games for user:   http --auth username:password GET  http://tuffix-vm/getGames

	Make a guess for a game:          http --auth username:password POST tuffix-vm/makeGuess guess=[apple] game_id=[example]

	Get game status:                  http --auth username:password GET tuffix-vm/gameStatus/[game_id]

=====================================================================

Online References:
https://dev.to/danielkun/nginx-everything-about-proxypass-2ona
http://nginx.org/en/docs/http/ngx_http_upstream_module.html
