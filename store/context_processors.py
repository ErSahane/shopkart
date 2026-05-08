from .models import Cart, Category, Wishlist


def shopkart_globals(request):
    categories = Category.objects.filter(is_active=True)[:8]
    cart_count = 0
    wishlist_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.total_items
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return {'nav_categories': categories, 'cart_count': cart_count, 'wishlist_count': wishlist_count}
