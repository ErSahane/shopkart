from decimal import Decimal

import razorpay
import json
import hmac
import hashlib
from django.conf import settings
from .utils import send_whatsapp_order
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import render

from .forms import AddressForm, CheckoutForm, OTPForm, RegisterForm, ReviewForm, SearchForm, UserProfileForm
from .models import Address, Cart, CartItem, Category, Coupon, Order, OrderItem, Payment, Product, Review, Wishlist
from .utils import create_and_send_otp, generate_invoice_pdf, send_order_confirmation




def cart_for(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def home(request):
    categories = Category.objects.filter(is_active=True)[:8]
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    trending = Product.objects.filter(is_active=True, is_trending=True).select_related('category')[:8]
    latest = Product.objects.filter(is_active=True).select_related('category')[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured or latest,
        'trending_products': trending or latest,
    })


def product_list(request):
    form = SearchForm(request.GET)
    products = Product.objects.filter(is_active=True).select_related('category').annotate(review_count=Count('reviews')).order_by('-is_featured', '-created_at')
    categories = Category.objects.filter(is_active=True)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort = form.cleaned_data.get('sort')
        if q:
            products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
        if category:
            products = products.filter(category__slug=category)
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'newest':
            products = products.order_by('-created_at')
        elif sort == 'rating':
            products = products.annotate(avg_rating=Sum('reviews__rating') / Count('reviews')).order_by('-avg_rating')
    page = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(request, 'store/product_list.html', {'page_obj': page, 'categories': categories, 'form': form})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    review_form = ReviewForm()
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related,
        'review_form': review_form,
        'user_review': user_review,
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.email = form.cleaned_data['email']
            user.save()
            create_and_send_otp(user)
            request.session['pending_user_id'] = user.id
            messages.success(request, 'We sent an OTP to your email. Check the console email backend while developing.')
            return redirect('verify_email')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def verify_email(request):
    user_id = request.session.get('pending_user_id')
    user = get_object_or_404(User, pk=user_id) if user_id else None
    if not user:
        messages.error(request, 'Please register first.')
        return redirect('register')
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid() and hasattr(user, 'email_otp'):
            otp = user.email_otp
            if otp.code == form.cleaned_data['code'] and otp.is_valid():
                otp.is_verified = True
                otp.save()
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, 'Email verified. Welcome to ShopKart.')
                return redirect('home')
            messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPForm()
    return render(request, 'registration/verify_email.html', {'form': form})


@login_required
def cart_view(request):
    return render(request, 'store/cart.html', {'cart': cart_for(request.user)})


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    qty = max(int(request.POST.get('quantity', 1)), 1)
    item, created = CartItem.objects.get_or_create(cart=cart_for(request.user), product=product, defaults={'quantity': qty})
    if not created:
        item.quantity = min(item.quantity + qty, max(product.stock, 1))
        item.save()
    messages.success(request, f'{product.name} added to cart.')
    return redirect(request.POST.get('next') or product.get_absolute_url())


@login_required
@require_POST
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    qty = int(request.POST.get('quantity', 1))
    if qty <= 0:
        item.delete()
    else:
        item.quantity = min(qty, max(item.product.stock, 1))
        item.save()
    return redirect('cart')


@login_required
@require_POST
def remove_cart_item(request, item_id):
    get_object_or_404(CartItem, pk=item_id, cart__user=request.user).delete()
    return redirect('cart')


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'items': items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, 'Removed from wishlist.')
    else:
        messages.success(request, 'Saved to wishlist.')
    return redirect(request.POST.get('next') or 'wishlist')


@login_required
def checkout(request):

    cart = cart_for(request.user)

    if not cart.items.exists():
        messages.info(request, 'Your cart is empty.')
        return redirect('products')

    addresses = request.user.addresses.all()

    address_form = AddressForm()
    checkout_form = CheckoutForm()

    # Razorpay Client
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Razorpay Order Create
    payment_data = {
        "amount": int(cart.subtotal * 100),
        "currency": "INR",
        "payment_capture": 1
    }

    razorpay_order = client.order.create(data=payment_data)

    return render(request, 'store/checkout.html', {

        'cart': cart,
        'addresses': addresses,
        'address_form': address_form,
        'checkout_form': checkout_form,

        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': payment_data["amount"],

        # IMPORTANT
        'razorpay_order_id': razorpay_order['id'],
    })


@login_required
@require_POST
@transaction.atomic

def place_order(request):

    cart = cart_for(request.user)

    if not cart.items.select_for_update().exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    address_id = request.POST.get('address_id')

    address = request.user.addresses.filter(
        pk=address_id
    ).first()

    if not address:

        address_form = AddressForm(request.POST)

        if address_form.is_valid():

            address = address_form.save(commit=False)

            address.user = request.user

            address.save()

        else:

            messages.error(
                request,
                'Please enter a valid shipping address.'
            )

            return redirect('checkout')

    subtotal = cart.subtotal

    coupon = None

    discount = Decimal('0')

    coupon_code = request.POST.get(
        'coupon_code',
        ''
    ).strip()

    if coupon_code:

        coupon = Coupon.objects.filter(
            code__iexact=coupon_code
        ).first()

        if coupon and coupon.can_apply():

            discount = (
                subtotal *
                Decimal(coupon.discount_percent) /
                Decimal('100')
            )

        else:

            messages.warning(
                request,
                'Coupon could not be applied.'
            )

            coupon = None

    shipping = (
        Decimal('0')
        if subtotal >= Decimal('999')
        else Decimal('79')
    )

    total = subtotal - discount + shipping

    # =========================
    # RAZORPAY VERIFICATION
    # =========================

    payment_status = 'pending'

    razorpay_payment_id = ''

    razorpay_order_id = ''

    razorpay_signature = ''

    if request.POST.get('payment_method') == 'gateway':

        razorpay_payment_id = request.POST.get(
            'razorpay_payment_id'
        )

        razorpay_order_id = request.POST.get(
            'razorpay_order_id'
        )

        razorpay_signature = request.POST.get(
            'razorpay_signature'
        )

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        try:

            client.utility.verify_payment_signature({

                'razorpay_order_id':
                razorpay_order_id,

                'razorpay_payment_id':
                razorpay_payment_id,

                'razorpay_signature':
                razorpay_signature

            })

            payment_status = 'paid'

        except:

            messages.error(
                request,
                'Payment verification failed'
            )

            return redirect('checkout')

    # =========================
    # CREATE ORDER
    # =========================

    order = Order.objects.create(

        user=request.user,

        address=address,

        payment_method=request.POST.get(
            'payment_method',
            'cod'
        ),

        subtotal=subtotal,

        discount=discount,

        shipping_fee=shipping,

        total=total,

        coupon=coupon,
    )

    # =========================
    # SAVE ORDER ITEMS
    # =========================

    for item in cart.items.select_related('product'):

        if item.product.stock < item.quantity:

            messages.error(
                request,
                f'{item.product.name} has only {item.product.stock} left.'
            )

            transaction.set_rollback(True)

            return redirect('cart')

        OrderItem.objects.create(

            order=order,

            product=item.product,

            product_name=item.product.name,

            price=item.product.price,

            quantity=item.quantity
        )

        item.product.stock = (
            F('stock') - item.quantity
        )

        item.product.save(
            update_fields=['stock']
        )

    # =========================
    # SAVE PAYMENT
    # =========================

    Payment.objects.create(

        order=order,

        provider='cod'
        if order.payment_method == 'cod'
        else 'razorpay',

        amount=order.total,

        status=payment_status
        if order.payment_method == 'gateway'
        else 'pending',

        transaction_id=
        razorpay_payment_id
        if order.payment_method == 'gateway'
        else '',

        razorpay_order_id=
        razorpay_order_id
        if order.payment_method == 'gateway'
        else '',

        razorpay_payment_id=
        razorpay_payment_id
        if order.payment_method == 'gateway'
        else '',

        razorpay_signature=
        razorpay_signature
        if order.payment_method == 'gateway'
        else '',
    )

    # =========================
    # CLEAR CART
    # =========================

    cart.items.all().delete()

    # =========================
    # SEND EMAIL + WHATSAPP
    # =========================

    send_order_confirmation(order)

    send_whatsapp_order(order)

    messages.success(
        request,
        f'Order {order.order_number} placed successfully.'
    )

    return redirect(
        'order_detail',
        order_number=order.order_number
    )
@login_required
def orders(request):
    return render(request, 'store/orders.html', {'orders': request.user.orders.prefetch_related('items')})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def invoice(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number, user=request.user)
    return FileResponse(generate_invoice_pdf(order), as_attachment=True, filename=f'{order.order_number}.pdf')


@login_required
def profile(request):
    profile_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    addresses = request.user.addresses.all()
    orders_qs = request.user.orders.all()[:5]
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    return render(request, 'store/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'address_form': AddressForm(),
        'addresses': addresses,
        'orders': orders_qs,
    })


@login_required
@require_POST
def save_address(request):
    form = AddressForm(request.POST)
    if form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        if address.is_default:
            request.user.addresses.update(is_default=False)
        address.save()
        messages.success(request, 'Address saved.')
    else:
        messages.error(request, 'Please fix the address form.')
    return redirect(request.POST.get('next') or 'profile')


@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review, _ = Review.objects.update_or_create(user=request.user, product=product, defaults=form.cleaned_data)
        messages.success(request, 'Thanks for reviewing this product.')
    return redirect(product.get_absolute_url())


@staff_member_required
def dashboard(request):
    revenue = Order.objects.exclude(status='cancelled').aggregate(total=Sum('total'))['total'] or 0
    context = {
        'total_orders': Order.objects.count(),
        'total_users': User.objects.count(),
        'total_revenue': revenue,
        'low_stock': Product.objects.filter(stock__lte=5).order_by('stock')[:8],
        'recent_orders': Order.objects.select_related('user').prefetch_related('items')[:8],
        'status_counts': Order.objects.values('status').annotate(count=Count('id')),
    }
    return render(request, 'store/admin_dashboard.html', context)


@staff_member_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES):
        order.status = status
        order.save(update_fields=['status'])
        messages.success(request, 'Order status updated.')
    return redirect('dashboard')


def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)




def payment_success(request):
    return render(request, 'store/success.html')

@require_POST
@csrf_exempt
def razorpay_webhook(request):

    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    received_signature = request.headers.get(
        'X-Razorpay-Signature'
    )

    body = request.body.decode('utf-8')

    generated_signature = hmac.new(

        bytes(webhook_secret, 'utf-8'),

        bytes(body, 'utf-8'),

        hashlib.sha256

    ).hexdigest()

    # VERIFY WEBHOOK SIGNATURE
    if generated_signature != received_signature:

        return JsonResponse({
            'status': 'invalid signature'
        }, status=400)

    data = json.loads(body)

    event = data.get('event')

    # ==========================
    # PAYMENT SUCCESS
    # ==========================

    if event == 'payment.captured':

        payment_entity = data['payload']['payment']['entity']

        razorpay_payment_id = payment_entity['id']

        try:

            payment = Payment.objects.get(
                razorpay_payment_id=razorpay_payment_id
            )

            payment.status = 'paid'

            payment.save()

            order = payment.order

            order.status = 'confirmed'

            order.save()

        except Payment.DoesNotExist:

            pass

    # ==========================
    # PAYMENT FAILED
    # ==========================

    elif event == 'payment.failed':

        payment_entity = data['payload']['payment']['entity']

        razorpay_payment_id = payment_entity['id']

        try:

            payment = Payment.objects.get(
                razorpay_payment_id=razorpay_payment_id
            )

            payment.status = 'failed'

            payment.save()

            order = payment.order

            order.status = 'cancelled'

            order.save()

        except Payment.DoesNotExist:

            pass

    return JsonResponse({
        'status': 'ok'
    })
