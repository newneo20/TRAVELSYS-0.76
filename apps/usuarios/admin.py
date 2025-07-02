from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'username', 'is_staff', 'is_manager']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_manager',)}),  # Agregamos solo los campos adicionales
    )

admin.site.register(CustomUser, CustomUserAdmin)