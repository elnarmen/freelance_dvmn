from django.contrib import admin

from .models import Customer, Message, Order, Tariff

# Register your models here.
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at']

admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Tariff)