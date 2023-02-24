from django.contrib import admin

from .models import Customer, Message, Order, Tariff

# Register your models here.
admin.site.register(Customer)
admin.site.register(Message)
admin.site.register(Order)
admin.site.register(Tariff)