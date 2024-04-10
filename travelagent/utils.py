"""
Utility functions.
"""

import random
import string
from collections.abc import Coroutine

from aiogram import types
from aiogram.utils.i18n.context import lazy_gettext as _lazy_gettext
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.widget_event import ensure_event_processor
from babel import Locale
from babel.support import LazyProxy


def rnd_id() -> str:
    """
    Generates a random 10-character string.
    :return: Random string consisting of letters and digits.
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=10))


def escape(text: str) -> str:
    """
    Escapes HTML text.
    :param text: Unsafe text
    :return: Safe text that can be included into HTML markup.
    """
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


def round_amount(number: int | float) -> int | float:
    """
    Rounds number to 3 decimal places, returning integer if possible.
    :param number: Number to be rounded
    :return: Integer or float
    """
    number = round(number, 3)
    if int(number) == number:
        return int(number)
    return number


def parse_ietf_tag(tag: str) -> str:
    """
    Parses IETF language tag, returning two-letter ISO 639-1 code.
    :param tag: IETF language tag
    :return: ISO 639-1 code
    """
    return Locale.parse(tag, sep="-").language


def lazy_gettext(*args, **kwargs) -> LazyProxy | str:
    """
    Lazy gettext function.

    The function does not return str, but return is annotated as str to
    help type hinters.
    """

    return _lazy_gettext(*args, **kwargs)


@ensure_event_processor
async def on_error(message: types.Message, *__) -> None:
    """
    Event processor for invalid inputs.
    :param message: Message to be answered
    :param __:
    """
    _ = lazy_gettext
    await message.answer(_("The input seems to be invalid. Please, try again."))


def maybe_next(manager: DialogManager) -> Coroutine[None, None, None]:
    """
    Either switch to the next state or mark the window as done.
    :param manager:
    :return:
    """
    if "single" in (manager.start_data or {}):
        return manager.done()

    return manager.next()
