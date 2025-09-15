# cart/context_processors.py
from .models import Cart

def cart_count(request):
    cid = request.session.get('cart_id')
    count = 0
    if cid:
        try:
            from uuid import UUID
            c = Cart.objects.get(id=UUID(cid))
            count = c.items.count()
        except Exception:
            pass
    return {'cart_count': count}
