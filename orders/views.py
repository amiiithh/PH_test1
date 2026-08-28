import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from store.cart import get_cart
from .forms import AddressForm
from .models import Address, Order, OrderItem
from .razorpay_client import create_razorpay_order, verify_payment_signature

SHIPPING_FEE = 49  # flat rate; free above a threshold, handled in checkout()
FREE_SHIPPING_THRESHOLD = 999


@login_required
def checkout(request):
    cart = get_cart(request, create=False)
    if not cart or cart.total_items == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart_detail')

    addresses = request.user.addresses.all()

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id == 'new':
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = request.user
                if not addresses.exists():
                    address.is_default = True
                address.save()
            else:
                return render(request, 'orders/checkout.html', {
                    'cart': cart, 'addresses': addresses, 'form': form,
                    'shipping_fee': _shipping_fee(cart.subtotal),
                })
        else:
            address = get_object_or_404(Address, pk=address_id, user=request.user)

        request.session['checkout_address_id'] = address.id
        return redirect('orders:payment')

    form = AddressForm()
    return render(request, 'orders/checkout.html', {
        'cart': cart, 'addresses': addresses, 'form': form,
        'shipping_fee': _shipping_fee(cart.subtotal),
    })


def _shipping_fee(subtotal):
    return 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE


@login_required
def payment(request):
    """Creates a PENDING Order + a matching Razorpay order, then renders the
    Razorpay Checkout.js page (test mode)."""
    cart = get_cart(request, create=False)
    address_id = request.session.get('checkout_address_id')
    if not cart or cart.total_items == 0 or not address_id:
        return redirect('store:cart_detail')

    address = get_object_or_404(Address, pk=address_id, user=request.user)

    subtotal = cart.subtotal
    shipping_fee = _shipping_fee(subtotal)
    total = subtotal + shipping_fee

    # If the user refreshes this page, goes back, or retries payment, we'd
    # otherwise create a brand-new Order (and a brand-new Razorpay order)
    # every single time. Clear out any of their still-unpaid orders first so
    # each checkout attempt only ever has one live PENDING order.
    Order.objects.filter(user=request.user, status=Order.Status.PENDING).delete()

    order = Order.objects.create(
        user=request.user,
        address=address,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total_amount=total,
        status=Order.Status.PENDING,
    )
    for item in cart.items.select_related('product'):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            size=item.size,
            unit_price=item.unit_price,
            quantity=item.quantity,
        )

    razorpay_order = None
    try:
        razorpay_order = create_razorpay_order(total, receipt=f'order_{order.id}')
    except Exception:
        # Most commonly: RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET in .env are
        # still the placeholder values, or there's no internet access from
        # this machine. Fail politely instead of a raw 500 debug page.
        order.delete()
        messages.error(
            request,
            'Payment could not be started. Check that RAZORPAY_KEY_ID and '
            'RAZORPAY_KEY_SECRET are set correctly in your .env file (see README.md).'
        )
        return redirect('store:cart_detail')

    order.razorpay_order_id = razorpay_order['id']
    order.save(update_fields=['razorpay_order_id'])

    context = {
        'order': order,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'amount_paise': razorpay_order['amount'],
        'currency': razorpay_order['currency'],
        'callback_url': request.build_absolute_uri(reverse('orders:payment_verify')),
        'customer_name': request.user.get_full_name() or request.user.username,
        'customer_email': request.user.email,
        'customer_phone': address.phone,
    }
    return render(request, 'orders/payment.html', context)


@csrf_exempt
@require_POST
def payment_verify(request):
    """Razorpay Checkout.js POSTs here (as a normal form submit) after the
    user completes/cancels the payment popup."""
    data = {
        'razorpay_order_id': request.POST.get('razorpay_order_id', ''),
        'razorpay_payment_id': request.POST.get('razorpay_payment_id', ''),
        'razorpay_signature': request.POST.get('razorpay_signature', ''),
    }

    order = get_object_or_404(Order, razorpay_order_id=data['razorpay_order_id'])

    if all(data.values()) and verify_payment_signature(data):
        order.razorpay_payment_id = data['razorpay_payment_id']
        order.razorpay_signature = data['razorpay_signature']
        order.status = Order.Status.PAID
        order.save()

        # empty the cart now that the order is confirmed
        cart = get_cart(request, create=False)
        if cart:
            cart.items.all().delete()
        request.session.pop('checkout_address_id', None)

        return redirect('orders:order_success', order_id=order.id)

    messages.error(request, 'Payment verification failed. Please try again or use a different method.')
    return redirect('orders:payment_failed', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def payment_failed(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/payment_failed.html', {'order': order})


@login_required
def order_history(request):
    orders = request.user.orders.all().prefetch_related('items')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
