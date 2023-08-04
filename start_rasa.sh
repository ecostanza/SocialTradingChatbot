#!/bin/sh 

export PYTHONPATH=${PWD}
export DJANGO_SETTINGS_MODULE=investment_bot.settings
(cd rasachat && rasa run --enable-api --cors "*" --debug -p 5056)

