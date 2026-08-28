"""
Small helper module that centralises "how do I get the current cart".

Logged-in users get a Cart tied to their user account (so it persists across
devices/logins). Anonymous visitors get a Cart tied to their session key.
When an anonymous user logs in, their session cart is merged into their
account cart — see `merge_session_cart_into_user` in accounts/views.py.
"""
from .models import Cart


def get_cart(request, create=True):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user) if create else (
            Cart.objects.filter(user=request.user).first(), False
        )
        return cart

    if not request.session.session_key:
        if not create:
            return None
        request.session.create()

    session_key = request.session.session_key
    if create:
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart
    return Cart.objects.filter(session_key=session_key).first()
