from django.db.models import Count, Q
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from .models import Category, Product

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class CategoryListView(ListView):
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # categorías ordenadas por nombre + conteo de productos ACTIVO
        return (
            Category.objects
            .annotate(product_count=Count("productos", filter=Q(productos__activo=True)))
            .order_by("nombre")
        )

class CategoryDetailView(DetailView):
    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = (
            Product.objects
            .filter(categoria=self.object, activo=True)
            .order_by("-created_at")
        )
        paginator = Paginator(qs, 12)  # 12 por página
        page_obj = paginator.get_page(self.request.GET.get("page"))
        ctx["page_obj"] = page_obj
        ctx["products"] = page_obj.object_list
        return ctx