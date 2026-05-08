from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from store.models import Category, Coupon, Product


class Command(BaseCommand):
    help = 'Create demo categories, products, coupon, and an admin user.'

    def handle(self, *args, **options):
        categories = ['Mobiles', 'Electronics', 'Fashion', 'Home', 'Beauty', 'Sports']
        category_objs = {name: Category.objects.get_or_create(name=name)[0] for name in categories}
        products = [
            ('Aurora X1 Smartphone', 'Mobiles', 24999, 31999, 18, True, True),
            ('SonicPods Pro', 'Electronics', 2999, 4999, 32, True, True),
            ('Velocity Running Shoes', 'Sports', 3499, 5299, 14, True, False),
            ('Cotton Everyday Hoodie', 'Fashion', 1899, 2499, 25, False, True),
            ('AeroBlend Mixer Grinder', 'Home', 4499, 5999, 9, True, False),
            ('GlowCare Skin Kit', 'Beauty', 1299, 1999, 40, False, True),
            ('NovaBook Air Laptop', 'Electronics', 64999, 78999, 6, True, True),
            ('Smart LED Desk Lamp', 'Home', 1599, 2199, 4, False, False),
            ('TrailMaster Backpack', 'Fashion', 2199, 2999, 11, False, True),
            ('FitPulse Smartwatch', 'Electronics', 6999, 9999, 20, True, True),
        ]
        for name, category, price, mrp, stock, featured, trending in products:
            Product.objects.update_or_create(
                name=name,
                defaults={
                    'category': category_objs[category],
                    'description': f'{name} delivers dependable quality, modern design, and strong value for everyday shopping.',
                    'price': Decimal(price),
                    'compare_at_price': Decimal(mrp),
                    'stock': stock,
                    'is_featured': featured,
                    'is_trending': trending,
                    'is_active': True,
                },
            )
        Coupon.objects.update_or_create(code='WELCOME10', defaults={'discount_percent': 10, 'is_active': True})
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@shopkart.local', 'Admin@12345')
        self.stdout.write(self.style.SUCCESS('ShopKart demo data ready. Admin: admin / Admin@12345'))
