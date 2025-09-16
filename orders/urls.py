from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("exito/<str:numero>/", views.success, name="success"),
    path("orden/<str:numero>/", views.order_detail, name="detail"),
]
