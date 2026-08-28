from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from store.models import Cart, CartItem
from orders.models import Address
from .forms import SignUpForm


def merge_session_cart_into_user(request, user):
    """When an anonymous user with items already in their cart logs in or
    registers, fold that session cart into their permanent account cart
    instead of silently losing it."""
    session_key = request.session.session_key
    if not session_key:
        return
    session_cart = Cart.objects.filter(session_key=session_key).first()
    if not session_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.items.all():
        existing = CartItem.objects.filter(cart=user_cart, product=item.product, size=item.size).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    session_cart.delete()


def register(request):
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            merge_session_cart_into_user(request, user)
            messages.success(request, f'Welcome to PosterHub, {user.first_name}!')
            return redirect('store:home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/register.html', {'form': form})


class PosterHubLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        merge_session_cart_into_user(self.request, self.request.user)
        messages.success(self.request, f'Welcome back, {self.request.user.first_name or self.request.user.username}!')
        return response


class PosterHubLogoutView(LogoutView):
    next_page = 'store:home'


@login_required
def profile(request):
    addresses = request.user.addresses.all()
    orders = request.user.orders.all()[:5]
    return render(request, 'accounts/profile.html', {'addresses': addresses, 'orders': orders})


@login_required
def address_delete(request, address_id):
    Address.objects.filter(pk=address_id, user=request.user).delete()
    messages.info(request, 'Address removed.')
    return redirect('accounts:profile')
