from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', related_name='children', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' > '.join(full_path[::-1])


class Product(models.Model):
    ItemID = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True, null=True)
    AllImagesURLs = models.JSONField()
    ItemSpecifications = models.JSONField()

    def __str__(self):
        return self.name


class Specialization(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    # ManyToManyField for multiple specialties
    specialties = models.ManyToManyField(Specialization)
    location = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200, null=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = models.TextField(
        max_length=500, null=True)  # Allow null values

    def __str__(self):
        return self.name


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ('doctor', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.doctor.name} - {self.date}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items",
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in {self.cart.user.username}'s cart"


class Purchase(models.Model):
    PURCHASE_TYPES = (
        ('medicine', 'Medicine'),
        ('appointment', 'Appointment'),
        ('package', 'Healthcare Package'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="purchases")
    product_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_type = models.CharField(max_length=20, choices=PURCHASE_TYPES)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product_name} - {self.purchase_type}"


class HealthcarePackage(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()

    def __str__(self):
        return self.name


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()