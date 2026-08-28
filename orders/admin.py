from django.contrib import admin
from .models import Address, Order, OrderItem


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'pincode', 'is_default')
    search_fields = ('full_name', 'city', 'pincode')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'size', 'unit_price', 'quantity')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'razorpay_payment_id', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ()
    search_fields = ('id', 'user__username', 'razorpay_order_id', 'razorpay_payment_id')
    inlines = [OrderItemInline]
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at')

    actions = ['mark_shipped', 'mark_delivered']

    @admin.action(description='Mark selected orders as Shipped')
    def mark_shipped(self, request, queryset):
        queryset.update(status='SHIPPED')

    @admin.action(description='Mark selected orders as Delivered')
    def mark_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
