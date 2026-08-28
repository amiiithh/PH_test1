from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import get_cart
from .models import Category, CartItem, Product


def home(request):
    featured_categories = Category.objects.filter(is_featured=True)[:6]
    bestsellers = Product.objects.filter(is_active=True, is_bestseller=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True)[:8]
    context = {
        'featured_categories': featured_categories,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'store/home.html', context)


def category_list(request):
    categories = Category.objects.all()
    return render(request, 'store/category_list.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(is_active=True)

    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {'category': category, 'page_obj': page_obj, 'sort': sort}
    return render(request, 'store/category_detail.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    sizes = Product.Size.choices
    context = {
        'product': product,
        'related': related,
        'sizes': [(code, label, product.price_for_size(code)) for code, label in sizes],
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'store/search_results.html', {'query': query, 'page_obj': page_obj})


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    size = request.POST.get('size', Product.Size.A4)
    quantity = int(request.POST.get('quantity', 1))

    cart = get_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, size=size)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    messages.success(request, f'Added "{product.name}" ({size}) to your cart.')
    return redirect(request.POST.get('next', 'store:cart_detail'))


@require_POST
def cart_update(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        item.delete()
        messages.info(request, 'Item removed from cart.')
    else:
        item.quantity = quantity
        item.save()
    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('store:cart_detail')
