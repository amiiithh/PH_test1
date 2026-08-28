from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """A poster collection, e.g. Marvel, Cars & Bikes, Motivational."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text='Show on homepage')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """A single poster design. Sold in multiple physical sizes."""

    class Size(models.TextChoices):
        A4 = 'A4', 'A4 (8.3 x 11.7 in)'
        A3 = 'A3', 'A3 (11.7 x 16.5 in)'
        A2 = 'A2', 'A2 (16.5 x 23.4 in)'

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/')

    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='Base price for A4 size')
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    stock = models.PositiveIntegerField(default=100)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base_slug}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    def price_for_size(self, size_code):
        """A2 costs more, A3 a bit more, A4 is base price."""
        from decimal import Decimal
        multipliers = {'A4': Decimal('1.0'), 'A3': Decimal('1.4'), 'A2': Decimal('1.9')}
        base = self.current_price
        return round(base * multipliers.get(size_code, Decimal('1.0')), 2)


class ProductImage(models.Model):
    """Extra gallery images for a product (optional, beyond the main image)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f'Image for {self.product.name}'


class Cart(models.Model):
    """One cart per logged-in user, or per anonymous session."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart #{self.pk} ({self.user or self.session_key})'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=2, choices=Product.Size.choices, default=Product.Size.A4)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'size')

    def __str__(self):
        return f'{self.quantity} x {self.product.name} ({self.size})'

    @property
    def unit_price(self):
        return self.product.price_for_size(self.size)

    @property
    def line_total(self):
        return self.unit_price * self.quantity
