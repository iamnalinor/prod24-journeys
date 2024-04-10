import random
import string
from datetime import timedelta

from tortoise import Model, fields
from tortoise.timezone import now


# Duplicate of travelagent.utils.rnd_id
# We cannot use instance from utils module itself. Explained in __init__py.
def rnd_id() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=10))


class JourneyInvite(Model):
    id = fields.CharField(max_length=10, default=rnd_id, pk=True)
    journey = fields.ForeignKeyField("models.Journey")
    owner = fields.ForeignKeyField("models.User")
    expires_at = fields.DatetimeField(default=lambda: now() + timedelta(days=1))

    @property
    def valid(self) -> bool:
        return self.expires_at > now()
