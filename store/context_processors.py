from .cart import get_cart
from .models import Category


def cart_summary(request):
    """Makes cart totals and the nav's featured categories available on every
    page without passing them explicitly from every view."""
    cart = get_cart(request, create=False)
    context = {'nav_cart_count': 0, 'nav_cart_subtotal': 0}
    if cart:
        context['nav_cart_count'] = cart.total_items
        context['nav_cart_subtotal'] = cart.subtotal
    context['nav_categories'] = Category.objects.filter(is_featured=True)[:4]
    return context
