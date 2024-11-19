from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('product/<str:ItemID>/',
         views.ProductDetailView.as_view(), name='product-detail'),
    path('specializations/', views.SpecializationListView.as_view(),
         name='specializations'),

    path('available-doctors/', views.AvailableDoctorsView.as_view(),
         name='available_doctors'),
    path('book-appointment/', views.BookAppointmentView.as_view(),
         name='book_appointment'),
    path('cart/', views.CartView.as_view(), name='cart'),

    path('cart/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/remove/<int:item_id>/',
         views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('cart/update/', views.UpdateCartItemView.as_view(),
         name='update-cart-item'),
    path('checkout/', views.CreateCheckoutSessionView.as_view(), name='checkout'),
    path('purchases/', views.UserPurchasesView.as_view(), name='user-purchases'),
    path('packages/', views.HealthcarePackageListView.as_view(), name='packages'),

    path('contact/', views.ContactUsView.as_view(), name='contact'),



]
