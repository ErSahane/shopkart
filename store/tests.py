from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cart, CartItem, Category, Product


class StoreSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'StrongPass123')
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Demo Phone',
            description='A reliable demo product.',
            price=Decimal('999.00'),
            stock=5,
            is_active=True,
        )

    def test_home_and_product_pages_render(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertContains(self.client.get(reverse('products')), 'Demo Phone')
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)

    def test_add_to_cart_requires_login_then_adds_item(self):
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        self.client.post(reverse('add_to_cart', args=[self.product.id]), {'quantity': 2})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 2)
