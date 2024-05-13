#!/bin/sh 

export PYTHONPATH=${PWD}
export DJANGO_SETTINGS_MODULE=investment_bot.settings
(cd rasachat && rasa run --debug --enable-api --cors "*" -p 5057)

