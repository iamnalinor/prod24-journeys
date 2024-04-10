from tortoise import Model, fields


class User(Model):
    id = fields.BigIntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    lang_code = fields.CharField(max_length=2, null=True)
    name = fields.TextField(null=True)
    age = fields.IntField(null=True)
    bio = fields.TextField(null=True)
    home_area_id = fields.BigIntField(null=True)

    def __str__(self):
        return f"User #{self.id}"

    @property
    def registered(self):
        return all(
            getattr(self, field) for field in ("age", "bio", "home_area_id")
        )
