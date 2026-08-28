from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('collections/', views.category_list, name='category_list'),
    path('collections/<slug:slug>/', views.category_detail, name='category_detail'),
    path('poster/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
]
