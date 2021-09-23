from django.apps import AppConfig
from django.db.models.signals import post_save

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # In this section post_save_user_handler not working
        # So i put this section at accounts.models.py
        # print("inside ready...")
        # from .signals import post_save_user_handler
        # # from django.contrib.auth import get_user_model
        # post_save.connect(
        #     post_save_user_handler,
        #     sender='app_label.User',
        #     dispatch_uid='accounts.signals.post_save_user_handler'
        # )
        pass
