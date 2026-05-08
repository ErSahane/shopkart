# ShopKart

ShopKart is a modern full-stack e-commerce web application built with Python, Django, SQLite, Bootstrap, and JavaScript. It includes secure authentication, email OTP verification, catalogue browsing, cart, wishlist, checkout, order tracking, PDF invoices, reviews, coupons, stock control, and a staff dashboard.

## Features

- User registration, login, logout, password reset, password change, and email OTP verification
- Responsive homepage with hero, categories, featured products, trending products, and search
- Product listing with category, price, search, sorting, pagination, and detail pages
- Cart, wishlist, checkout, coupons, COD, and demo online payment records
- Order history, order tracking, confirmation email, and downloadable PDF invoices
- User profile and address management
- Django admin plus custom staff dashboard with revenue, users, low stock, recent orders, and status analytics
- Reviews and average ratings
- CSRF protection, Django password hashing, ORM queries, form validation, and login-required pages

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_shopkart
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo admin:

- Username: `admin`
- Password: `Admin@12345`

## Payment Integration

The checkout creates real `Payment` records and supports Cash on Delivery plus a demo online gateway provider. To connect Razorpay or Stripe in production, install the provider SDK, add keys to environment variables, and replace the demo branch in `store.views.place_order` with provider order creation and webhook verification.

Supported environment variables:

- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `STRIPE_PUBLIC_KEY`
- `STRIPE_SECRET_KEY`
- `SHOPKART_SECRET_KEY`
- `SHOPKART_ALLOWED_HOSTS`

## Email

Development uses Django's console email backend. OTP, password reset, and order emails print to the terminal. For production, set `SHOPKART_EMAIL_BACKEND` and SMTP settings in `shopkart/settings.py`.

## Project Structure

```text
shopkart/          Django project settings and root URLs
store/             Commerce app: models, forms, views, admin, utilities
templates/         Reusable Django templates
static/            CSS and JavaScript assets
media/             Uploaded product/category images
requirements.txt   Python dependencies
```

## Deployment Notes

- Set `DEBUG=False` before production deployment.
- Configure `SHOPKART_SECRET_KEY`, `SHOPKART_ALLOWED_HOSTS`, static file hosting, media storage, SMTP, and a production database.
- Run `python manage.py collectstatic`.
- Use webhooks for real payment confirmation before marking online payments as paid.
