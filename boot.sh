#!/bin/bash

cd /home/user/lateness || exit
/usr/bin/screen -dmS lateness pipenv run uvicorn lateness.main:app
