from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.utils.i18n import I18n
from aiogram_dialog import StartMode
from aiogram_dialog.widgets.kbd import Back, Cancel, Start
from aiogram_dialog.widgets.text import Const
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import Overpass

from travelagent.config import BOT_TOKEN, DEFAULT_LOCALE, REDIS_URL
from travelagent.states import MainSG
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize

bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(
    storage=RedisStorage.from_url(
        REDIS_URL,
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
)

i18n = I18n(path="locales/", default_locale=DEFAULT_LOCALE.lang_code)

BACK = Cancel(Const(_("‹ Back")))
BACK_STATE = Back(Const(_("‹ Back")))
CANCEL = Back(Const(_("‹ Cancel")))
HOME = Start(
    Emojize(_(":house: Home")),
    id="go_home",
    state=MainSG.intro,
    mode=StartMode.RESET_STACK,
)

nominatim = Nominatim()
overpass = Overpass()
