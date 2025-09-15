from django.urls import path
from . import views

app_name='cart'
urlpatterns = [
    path('', views.detail, name='detail'),
    path('add/<uuid:product_id>/', views.add, name='add'),
    path('remove/<uuid:product_id>/', views.remove, name='remove'),
    path('inc/<uuid:product_id>/', views.increment, name='inc'),
    path('dec/<uuid:product_id>/', views.decrement, name='dec'),
    path('checkout/', views.checkout, name='checkout'),
]
