import os

from telegram import User

ADMINS = os.environ['ADMIN_USERS']


def is_admin(user: User):
    return user.name in ADMINS.split(";")

