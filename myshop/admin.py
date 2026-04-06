from django.contrib import admin
from .models import Product
from .models import (
    Brand,
    Category,
    Product,
    ProductImage,
    Customer,
    Order,
    OrderItem,
    Cart,
    CartItem,
)

# ======================================================
# Product Image Inline
# ======================================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


# ======================================================
# Product Admin
# ======================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'is_active', 'stock_quantity', 'is_featured']
    list_filter = ['is_active', 'is_featured', 'brand', 'category']
    list_editable = ['is_active', 'stock_quantity', 'price']  # Optional: quick edit
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    ordering = ('-created_at',)


# ======================================================
# Brand Admin
# ======================================================
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'show_in_brands', 'is_featured', 'tier')
    list_filter = ('is_active', 'show_in_brands', 'is_featured', 'tier')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ======================================================
# Category Admin
# ======================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ======================================================
# Product Image Admin
# ======================================================
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'created_at')
    list_filter = ('created_at',)


# ======================================================
# Customer Admin
# ======================================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__username', 'user__email')


# ======================================================
# Order Admin
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'customer',
        'status',
        'total_amount',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__user__username')


# ======================================================
# Order Item Admin
# ======================================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product_name',
        'quantity',
        'total_price',
    )
    search_fields = ('product_name',)
    list_filter = ('order',)


# ======================================================
# Cart Item Inline (inside Cart)
# ======================================================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product', 'quantity', 'subtotal')
    raw_id_fields = ('product',)

    def subtotal(self, obj):
        return f"৳{obj.subtotal()}"
    subtotal.short_description = 'Subtotal'


# ======================================================
# Cart Admin
# ======================================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'item_count',
        'cart_total',
        'created_at',
        'updated_at',
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

    def cart_total(self, obj):
        return f"৳{obj.total_price()}"
    cart_total.short_description = 'Total'


# ======================================================
# Cart Item Admin (ONLY ONE REGISTRATION)
# ======================================================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'cart',
        'product',
        'quantity',
        'subtotal',
        'added_at',
    )
    list_filter = ('added_at', 'cart__user')
    search_fields = ('product__name', 'cart__user__username')
    readonly_fields = ('subtotal', 'added_at')
    raw_id_fields = ('product', 'cart')

    def subtotal(self, obj):
        return f"৳{obj.subtotal()}"
    subtotal.short_description = 'Subtotal'
