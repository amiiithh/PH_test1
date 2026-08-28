"""
Seeds the database with demo categories and products so the site looks
complete right after setup, without needing internet access for images.

Usage: python manage.py seed_store
"""
import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from store.models import Category, Product

CATEGORIES = [
    ('Movies & TV', '#1b2a4a', '#f5b935'),
    ('Cars & Bikes', '#1c1c1c', '#e8432c'),
    ('Anime', '#2a1b3d', '#f5b935'),
    ('Motivational', '#17171c', '#e8432c'),
    ('Music', '#3d1b2a', '#f5b935'),
    ('Nature & Travel', '#123524', '#f5b935'),
]

PRODUCT_WORDS = [
    'Skyline', 'Vintage', 'Neon Nights', 'Retro Wave', 'Midnight', 'Horizon',
    'Legacy', 'Velocity', 'Dream State', 'Solitude', 'Momentum', 'Echo',
    'Golden Hour', 'Static', 'Wanderlust', 'Afterglow', 'Rebel', 'Origin',
]


def make_placeholder_image(text, bg_hex, accent_hex, size=(800, 1100)):
    """Generates a simple, good-looking poster-style placeholder graphic
    entirely offline using PIL — stands in for real artwork/photography."""
    img = Image.new('RGB', size, bg_hex)
    draw = ImageDraw.Draw(img)

    # a few decorative geometric shapes for visual interest
    w, h = size
    draw.ellipse([w * 0.1, h * 0.55, w * 0.9, h * 1.05], fill=accent_hex)
    draw.rectangle([0, 0, w, h * 0.08], fill=accent_hex)

    try:
        font = ImageFont.load_default(size=54)
        small_font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
        small_font = font

    label = text.upper()
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, h * 0.35), label, fill='white', font=font)

    tagline = 'POSTERHUB EDITION'
    bbox2 = draw.textbbox((0, 0), tagline, font=small_font)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((w - tw2) / 2, h * 0.42), tagline, fill=accent_hex, font=small_font)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = 'Seeds demo categories and products with generated placeholder artwork.'

    def add_arguments(self, parser):
        parser.add_argument('--per-category', type=int, default=6)

    @transaction.atomic
    def handle(self, *args, **options):
        per_category = options['per_category']
        self.stdout.write('Seeding categories and products...')

        for order, (name, bg, accent) in enumerate(CATEGORIES):
            category, created = Category.objects.get_or_create(
                name=name, defaults={'is_featured': True, 'order': order}
            )
            if created or not category.image:
                category.image.save(f'{category.slug}.jpg', make_placeholder_image(name, bg, accent, (600, 750)), save=True)

            for i in range(per_category):
                word = random.choice(PRODUCT_WORDS)
                product_name = f'{name.split(" ")[0]} {word} Poster #{i+1}'
                if Product.objects.filter(name=product_name).exists():
                    continue

                price = random.choice([149, 199, 249, 299, 349, 399])
                has_discount = random.random() < 0.35
                discount_price = round(price * 0.8) if has_discount else None

                product = Product(
                    category=category,
                    name=product_name,
                    description=(
                        f'A striking {name.lower()} print featuring bold colour and clean composition. '
                        'Printed on premium 250 GSM matte paper — fade-resistant and ready to display.'
                    ),
                    price=price,
                    discount_price=discount_price,
                    stock=random.choice([0, 25, 50, 80, 120]),
                    is_bestseller=random.random() < 0.3,
                    is_new_arrival=random.random() < 0.3,
                )
                product.image.save(
                    f'{product_name}.jpg',
                    make_placeholder_image(word, bg, accent),
                    save=False,
                )
                product.save()

        self.stdout.write(self.style.SUCCESS(
            f'Done. {Category.objects.count()} categories, {Product.objects.count()} products.'
        ))
