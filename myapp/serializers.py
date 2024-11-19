from rest_framework import serializers
from .models import Category, Product, Doctor, Appointment, Specialization,Cart,CartItem,Purchase,HealthcarePackage,ContactUs
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


class CategorySerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'path']

    def get_path(self, obj):
        return str(obj)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Product
        fields = '__all__'


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']


class DoctorSerializer(serializers.ModelSerializer):
    specialties = SpecializationSerializer(many=True)

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialties', 'location',
                  'fees', 'qualification', 'description']


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'doctor', 'date']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['id', 'product_name', 'amount', 'purchase_type', 'purchase_date']

class HealthcarePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthcarePackage
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = "__all__"