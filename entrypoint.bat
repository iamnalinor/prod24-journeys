@echo off

if "%1" == "run-polling" (
  pybabel compile -d locales/
  aerich upgrade
  python -m travelagent
) else if "%1" == "lint" (
  ruff check --fix
  ruff format
) else if "%1" == "test" (
  python -m unittest discover test -v
) else if "%1" == "update-messages" (
  pybabel extract travelagent -o locales/messages.pot -k Message
  pybabel update -i locales/messages.pot -d locales/
) else if "%1" == "add-locale" (
  pybabel extract travelagent -o locales/messages.pot -k Message
  pybabel init -i locales/messages.pot -d locales -l "%2"
) else if "%1" == "migrate" (
  aerich migrate
) else (
  echo Available commands: run-polling lint update-messages add-locale migrate
)
