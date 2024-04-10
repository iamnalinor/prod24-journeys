import logging

from aiogram import BaseMiddleware

from travelagent.models.user import User

logger = logging.getLogger(__name__)


class ACLMiddleware(BaseMiddleware):
    """
    Adds a User object to middleware data, creating DB record if user is not found.
    """

    async def __call__(
        self,
        handler,
        event,
        data,
    ):
        if (event_user := data.get("event_from_user")) and "user" not in data:
            user = await User.get_or_none(id=event_user.id)
            if user is None:
                user = await User.create(
                    id=event_user.id, name=event_user.full_name
                )
                logger.info(f"Created new user: {user} from {event}")
            else:
                full_name = event_user.full_name
                if len(full_name) > 20:
                    full_name = full_name[:20] + "..."
                if full_name != user.name:
                    await user.update_from_dict({"name": full_name}).save()
                    logger.info(f"Updated user name: {user} from {event}")
            data["user"] = user

        return await handler(event, data)
