from django.contrib import admin

from .models import Customer, Order, Tariff

# Register your models here.
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Tariff)