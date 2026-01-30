from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Sum, F  # ✅ FIXED
import os
from django.core.cache import cache


class Category(models.Model):
    """
    Main product categories (e.g., Phone, Laptop, Tablet)
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, default='fas fa-folder')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def active_subcategories(self):
        return self.subcategories.filter(is_active=True)
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class SubCategory(models.Model):
    """
    Sub-categories under main categories (e.g., Apple, Samsung, Oppo under Phone)
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, default='fas fa-folder')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Sub Categories"
        ordering = ['order', 'name']
        unique_together = ['name', 'category']
    
    def __str__(self):
        return f"{self.category.name} > {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while SubCategory.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)
        
        # Clear cache
        cache.delete('navbar_categories')
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    subcategory = models.ForeignKey(   # ✅ ADD THIS
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(blank=True, db_index=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    ram = models.CharField(max_length=50, blank=True)
    storage = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='gallery',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='products/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


from django.conf import settings
from django.db import models

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)

    # ✅ FIX HERE
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    shipping_address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        import random, string
        return "ORD-" + ''.join(random.choices(string.digits, k=8))

    def update_totals(self):
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.total_amount = self.subtotal
        self.save(update_fields=['subtotal', 'total_amount'])



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.order.update_totals()

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart ({self.user.username})"
    
    def total_items(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    def total_price(self):
        total = self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        return total
    
    def is_empty(self):
        return not self.items.exists()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def subtotal(self):
        return self.product.price * self.quantity


# =============== SIGNALS ===============

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)
        Customer.objects.create(user=instance)


@receiver(post_save, sender=CartItem)
def update_cart_on_item_change(sender, instance, **kwargs):
    if instance.cart:
        instance.cart.updated_at = timezone.now()
        instance.cart.save(update_fields=['updated_at'])


@receiver(post_delete, sender=CartItem)
def update_cart_on_item_delete(sender, instance, **kwargs):
    if instance.cart:
        instance.cart.updated_at = timezone.now()
        instance.cart.save(update_fields=['updated_at'])
