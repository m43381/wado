from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.safestring import mark_safe
from authentication.models import CustomUser

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем пояснения к полям
        self.fields['faculty'].help_text = mark_safe(
            '<div style="margin-bottom: 10px; font-weight: bold;">Выберите факультет из списка</div>'
        )
        self.fields['department'].help_text = mark_safe(
            '<div style="margin-bottom: 10px; font-weight: bold;">Выберите кафедру из списка</div>'
        )

class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    list_display = ('username', 'email', 'faculty', 'department')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
        ('Образовательная информация', {
            'fields': ('faculty', 'department'),
            'description': mark_safe(
                '<div style="margin: 10px 0; padding: 10px; background: #f8f8f8; border-radius: 5px;">'
                '<h3 style="margin-top: 0;">Выбор подразделения</h3>'
                '<p>Пожалуйста, выберите факультет и кафедру, к которым относится пользователь.</p>'
                '<p>Если информация отсутствует, оставьте поля пустыми.</p>'
                '</div>'
            )
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)