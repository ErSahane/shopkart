from django.contrib import admin

from .models import Address, Cart, CartItem, Category, Coupon, EmailOTP, Order, OrderItem, Payment, Product, Review, Wishlist


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'is_featured', 'is_trending')
    list_filter = ('category', 'is_active', 'is_featured', 'is_trending')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_method', 'total', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email')
    inlines = [OrderItemInline]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('user', 'total_items', 'subtotal')


admin.site.site_header = 'ShopKart Admin'
admin.site.site_title = 'ShopKart Admin'
admin.site.index_title = 'Commerce management'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Address)
admin.site.register(Cart, CartAdmin)
admin.site.register(Wishlist)
admin.site.register(Coupon)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(EmailOTP)

# Register your models here.
