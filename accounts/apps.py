from django.apps import AppConfig
from django.db.models.signals import post_save

class AccountsConfig(AppConfig):
    name = 'accounts'

    # def ready(self):
    #     # singal did not work inside ready function for accounts.User model
    #     # exact reason don't know
    #     # but work inside accounts.models.py file
    #     # currently all signals of accounts app inside accounts.models.py file
    #     pass