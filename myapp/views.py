from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_date
from .serializers import ProfileSerializer, CategorySerializer, ProductSerializer, DoctorSerializer, AppointmentSerializer, SpecializationSerializer, CartItemSerializer, CartSerializer, PurchaseSerializer, HealthcarePackageSerializer, ContactSerializer
from .models import Product, Category, Appointment, Doctor, Specialization, CartItem, Cart, Purchase, HealthcarePackage
from django.conf import settings
import stripe


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data)


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:  # If a primary key is provided, get that specific category
            category = get_object_or_404(Category, pk=pk)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        else:  # Otherwise, return a list of all categories
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ItemID):
        product = get_object_or_404(Product, ItemID=ItemID)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpecializationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        specializations = Specialization.objects.all()
        serializer = SpecializationSerializer(specializations, many=True)
        return Response(serializer.data)


class AvailableDoctorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        location = request.query_params.get('location')
        specialization_ids = request.query_params.get('specializations')

        if specialization_ids:
            specialization_ids = list(map(int, specialization_ids.split(',')))

        date = request.query_params.get('date')

        # Validate date format
        if not date or not parse_date(date):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter doctors based on location and specialization
        doctors = Doctor.objects.filter(
            location=location, specialties__id__in=specialization_ids).distinct()

        # Check availability for the selected date
        available_doctors = [
            doctor for doctor in doctors if not Appointment.objects.filter(doctor=doctor, date=date).exists()
        ]

        serializer = DoctorSerializer(available_doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        doctor_id = request.data.get('doctor_id')
        date = request.data.get('date')

        if not date or not parse_date(date):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Check if the doctor is already booked for the selected date
        if Appointment.objects.filter(doctor=doctor, date=date).exists():
            return Response({"error": "Doctor is already booked for this date."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new appointment
        appointment_data = {
            'user': user.id,
            'doctor': doctor.id,
            'date': date
        }

        serializer = AppointmentSerializer(data=appointment_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        cart, created = Cart.objects.get_or_create(user=user)
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product)

        if created:
            # If the cart item is newly created, set the quantity directly
            cart_item.quantity = int(quantity)
        else:
            # If the cart item already exists, add to the current quantity
            cart_item.quantity += int(quantity)

        cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        cart_item.delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        item_id = request.data.get('item_id')
        new_quantity = request.data.get('quantity')

        cart_item = get_object_or_404(
            CartItem, id=item_id, cart__user=request.user)
        cart_item.quantity = new_quantity
        cart_item.save()

        serializer = CartSerializer(cart_item.cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        items = request.data.get('items', [])
        purchase_type = request.data.get('purchase_type')
        user = request.user

        try:
            line_items = []

            if purchase_type == 'Medicine':
                purchased_items = []

                for item in items:
                    price = float(item['product']['price'])
                    name = item['product']['name']
                    quantity = item.get('quantity', 1)

                    line_items.append({
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': name,
                            },
                            'unit_amount': int(price * 100),
                        },
                        'quantity': quantity,
                    })

                    purchased_items.append({
                        'name': name,
                        'price': price,
                        'quantity': quantity,
                        'total': price * quantity
                    })

                    Purchase.objects.create(
                        user=user,
                        product_name=name,
                        amount=price * quantity,
                        purchase_type=purchase_type
                    )

                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url="https://pharmacare-react.onrender.com/success",
                    cancel_url="https://pharmacare-react.onrender.com/cancel",
                    customer_email=user.email,
                    shipping_address_collection={
                        'allowed_countries': ['IN'],
                    },
                )

                send_medicine_purchase_email(user, purchased_items)

                Cart.objects.filter(user=user).delete()

            elif purchase_type == 'appointment':
                for item in items:
                    doctor = Doctor.objects.get(id=item['doctor_id'])
                    appointment_date = item['date']
                    fees = doctor.fees

                    line_items.append({
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': f"Appointment with Dr. {doctor.name}",
                            },
                            'unit_amount': int(fees * 100),
                        },
                        'quantity': 1,
                    })

                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url="https://pharmacare-react.onrender.com/success",
                    cancel_url="https://pharmacare-react.onrender.com/cancel",
                    customer_email=user.email,
                    shipping_address_collection={
                        'allowed_countries': ['IN'],
                    },
                )

                # Save purchase and send appointment confirmation email
                for item in items:
                    doctor = Doctor.objects.get(id=item['doctor_id'])
                    Purchase.objects.create(
                        user=user,
                        product_name=f"Appointment with Dr. {doctor.name}",
                        amount=doctor.fees,
                        purchase_type=purchase_type
                    )
                    send_appointment_booking_email(
                        user, doctor.name, appointment_date, doctor.fees)

            elif purchase_type == 'package':
                for item in items:
                    price = float(item['price'])
                    package_name = item['package_name']

                    line_items.append({
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': package_name,
                            },
                            'unit_amount': int(price * 100),
                        },
                        'quantity': 1,
                    })

                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url="https://pharmacare-react.onrender.com/success",
                    cancel_url="https://pharmacare-react.onrender.com/cancel",
                    customer_email=user.email,
                    shipping_address_collection={
                        'allowed_countries': ['IN'],
                    },
                )

                for item in items:
                    Purchase.objects.create(
                        user=user,
                        product_name=item['package_name'],
                        amount=item['price'],
                        purchase_type=purchase_type
                    )
                    send_health_package_purchase_email(
                        user, item['package_name'], item['price'])

            return Response({'sessionId': session.id}, status=status.HTTP_200_OK)

        except Exception as e:

            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPurchasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        purchases = Purchase.objects.filter(user=request.user)
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)


class HealthcarePackageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        healthcare_packages = HealthcarePackage.objects.all()
        serializer = HealthcarePackageSerializer(
            healthcare_packages, many=True)
        return Response(serializer.data)


def send_medicine_purchase_email(user, purchased_items):
    """Send email for medicine purchases in a table format"""
    subject = "Your Medicine Purchase Confirmation"

    total_amount = sum(item['total'] for item in purchased_items)

    html_message = render_to_string('medicine_purchase_confirmation.html', {
        'user_name': user.get_full_name(),
        'purchased_items': purchased_items,
        'total_amount': total_amount
    })

    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )


def send_appointment_booking_email(user, doctor_name, appointment_date, fees):
    """Send email for doctor appointment bookings"""
    subject = "Your Appointment Confirmation"
    html_message = render_to_string('appointment_confirmation.html', {
        'user_name': user.get_full_name(),
        'doctor_name': doctor_name,
        'appointment_date': appointment_date,
        'fees': fees,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )


def send_health_package_purchase_email(user, package_name, total_amount):
    """Send email for health care package purchases"""
    subject = "Your Health Care Package Purchase Confirmation"
    html_message = render_to_string('health_package_confirmation.html', {
        'user_name': user.get_full_name(),
        'package_name': package_name,
        'total_amount': total_amount,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )


class ContactUsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data["name"]
            email = serializer.validated_data['email']
            confirmation_email_html = render_to_string(
                'contact.html', {'name': name})

            send_mail(
                subject='Confirmation: Your message has been received',
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=confirmation_email_html,
            )
            serializer.save()
            return Response({"message": "Message Send SuccessFully"})
        return Response({"error": "Message Not Send"})
