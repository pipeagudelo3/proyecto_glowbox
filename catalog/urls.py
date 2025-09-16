from django.urls import path
from .views import ProductListView, ProductDetailView
from . import views

app_name='catalog'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('p/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path("categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("categorias/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
]
