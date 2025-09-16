from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("exito/<str:numero>/", views.success, name="success"),
    path("mis-pedidos/", views.my_orders, name="my_orders"),
    path("track/<str:numero>/", views.set_tracking, name="set_tracking"),
    path("<str:numero>/", views.order_detail, name="order_detail"),

]
