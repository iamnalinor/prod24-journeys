import os
from collections import namedtuple

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWM_APPID = os.environ["OWM_APPID"]

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/postgres"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["travelagent.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

Locale = namedtuple("Locale", ["lang_code", "flag", "name"])
LOCALES = {
    "en": Locale("en", ":United_States:", "English"),
    "ru": Locale("ru", ":Russia:", "Русский"),
}
DEFAULT_LOCALE = LOCALES["en"]
