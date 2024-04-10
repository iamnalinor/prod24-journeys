"""
FSM states, describing window transitions.

The format is as follows:
    <name>SG
    <name> - human-readable name of group (can match the file name) in UpperCamelCase.
    Example: MainSG

The first state of a group is usually named "intro". Exception can be made
for a subgroup waiting for some user input.
If needed, the last state is always named "outro".
"""

from aiogram.fsm.state import State, StatesGroup


class MainSG(StatesGroup):
    intro = State()


class SettingsSG(StatesGroup):
    intro = State()
    choose_lang = State()


class RegisterSG(StatesGroup):
    age = State()
    bio = State()
    home = State()
    outro = State()


class JourneyCreateSG(StatesGroup):
    name = State()
    description = State()
    location_name = State()
    location_dates = State()
    outro = State()


class JourneySG(StatesGroup):
    list = State()
    view = State()
    confirm_leave = State()


class JourneyUsersSG(StatesGroup):
    list = State()
    user_view = State()
    user_kick_confirm = State()
    invite = State()


class JourneyLocationsSG(StatesGroup):
    list = State()
    view = State()
    confirm_delete = State()
    weather = State()


class ConfirmJoinSG(StatesGroup):
    intro = State()
