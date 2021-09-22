from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# Define a Custom User admin
class UserAdmin(BaseUserAdmin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # update fieldsets
        _fieldsets = list(super().fieldsets)
        try:
            _fieldsets.insert(2, (_('Account Types'), {'fields': ('types',)}))
        except Exception as e:
            _fieldsets.append((_('Account Types'), {'fields': ('types',)}))
        self.fieldsets = tuple(_fieldsets)

        # update search_fields
        self.search_fields = list(super().search_fields)
        self.search_fields.append('types')
        
        # update list_filter
        # self.list_filter = list(super().list_filter)
        # self.list_filter.append('types')

admin.site.register(User, UserAdmin)
