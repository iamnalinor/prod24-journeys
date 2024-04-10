from datetime import timedelta

from tortoise import Model, fields


class Journey(Model):
    id = fields.BigIntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=255)

    notes = fields.ManyToManyField("models.JourneyNote")
    locations = fields.ManyToManyField("models.JourneyLocation")

    """
    Users that have access to the journey.
    
    Users are ordered by the time they were added. Note that the order is important.
    """
    users = fields.ManyToManyField("models.User")


class JourneyNote(Model):
    id = fields.BigIntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.User")
    text = fields.TextField()


class JourneyLocation(Model):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)
    address = fields.TextField(null=True)
    area_id = fields.BigIntField()
    start_date = fields.DateField()
    end_date = fields.DateField()

    @property
    def duration(self):
        return self.end_date - self.start_date + timedelta(days=1)
