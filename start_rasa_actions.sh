#!/bin/sh 

export PYTHONPATH=${PWD}
export DJANGO_SETTINGS_MODULE=investment_bot.settings
export DJANGO_ALLOW_ASYNC_UNSAFE=true
(cd rasachat && rasa run actions --debug -p 5007)
