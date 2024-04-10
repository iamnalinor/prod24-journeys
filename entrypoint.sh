#!/usr/bin/env sh

set -e

case "$1" in
  run-polling)
    pybabel compile -d locales/

    aerich upgrade
    python -m travelagent
    ;;

  lint)
    ruff check --fix
    ruff format
    ;;

  test)
    python -m unittest discover test -v
    ;;

  update-messages)
    pybabel extract travelagent -o locales/messages.pot -k Message
    pybabel update -i locales/messages.pot -d locales/
    ;;

  add-locale)
    pybabel extract travelagent -o locales/messages.pot -k Message
    pybabel init -i locales/messages.pot -d locales -l "$1"
    ;;

  migrate)
    aeirch migrate
    ;;

  *)
    echo Available commands: run-polling lint update-messages add-locale migrate
    ;;
esac