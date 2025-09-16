# cart/urls.py
from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/<uuid:product_id>/", views.add, name="add"),
    path("inc/<uuid:item_id>/", views.increment, name="inc"),
    path("dec/<uuid:item_id>/", views.decrement, name="dec"),
    path("remove/<uuid:item_id>/", views.remove, name="remove"),
    path("clear/", views.clear, name="clear"),
]
