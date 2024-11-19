from django.contrib import admin
from .models import Product,Category,Doctor,Appointment,Specialization,Cart,CartItem,Purchase,HealthcarePackage,ContactUs
# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Specialization)
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Purchase)
admin.site.register(HealthcarePackage)
admin.site.register(ContactUs)