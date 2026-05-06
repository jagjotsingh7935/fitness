from django.contrib import admin
from .models import User, Category, Role, TrainerProfile, ClientProfile, TrainerClientLink, EmailOTP

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'is_admin', 'is_trainer', 'is_client', 'is_active']
    list_filter = ['is_admin', 'is_trainer', 'is_client', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_staff', 'is_client', 'created_at']
    list_filter = ['is_staff', 'is_client']
    search_fields = ['name']
    filter_horizontal = ['permissions']

@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'admin', 'specialization', 'is_active', 'created_at']
    list_filter = ['is_active', 'categories']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'specialization']
    filter_horizontal = ['categories']

    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Categories'

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'categories']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']
    filter_horizontal = ['categories']

    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Categories'

@admin.register(TrainerClientLink)
class TrainerClientLinkAdmin(admin.ModelAdmin):
    list_display = ['client', 'trainer', 'is_active', 'is_subscribed', 'assigned_at']
    list_filter = ['is_active', 'is_subscribed']
    search_fields = ['client__user__email', 'trainer__user__email']

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp', 'created_at', 'is_verified']
    list_filter = ['is_verified']
    search_fields = ['email']