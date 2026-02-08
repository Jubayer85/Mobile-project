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
<<<<<<< HEAD
from django.conf import settings
from django.db import models
import random
import string

=======
from decimal import Decimal
>>>>>>> 0df83f8121a1e35b066fb1e694931f552883af37


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
    TIER_CHOICES = [
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('budget', 'Budget'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    #description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='standard')
    website = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_in_brands = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Remove logo_initials if you don't have it in your model
    # logo_initials = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            counter = 1
            original_slug = self.slug
            
            while Brand.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        
        super().save(*args, **kwargs)
    
    def get_tier_display(self):
        return dict(self.TIER_CHOICES).get(self.tier, self.tier)


class Product(models.Model):
    # ==================== RELATIONS ====================
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

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # ==================== BASIC INFO ====================
    name = models.CharField(
        max_length=200,
        verbose_name="Product Name"
    )
    
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        db_index=True,
        verbose_name="URL Slug"
    )
    
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Stock Keeping Unit",
        help_text="Unique product identifier"
    )
    
    # ==================== PRICING ====================
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Selling Price",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Compare/Original Price",
        help_text="Original price to show discount"
    )
    
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cost Price",
        help_text="Purchase price for profit calculation"
    )
    
    # ==================== SPECIFICATIONS ====================
    # Performance
    ram = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="RAM"
    )
    
    storage = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Storage"
    )
    
    processor = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Processor"
    )
    
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Operating System"
    )
    
    # Display
    display_size = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Display Size"
    )
    
    display_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Display Type",
        help_text="e.g., AMOLED, IPS LCD"
    )
    
    refresh_rate = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Refresh Rate",
        help_text="e.g., 120Hz, 90Hz"
    )
    
    resolution = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Resolution",
        help_text="e.g., 2400x1080 pixels"
    )
    
    # Camera
    camera = models.TextField(
        blank=True,
        verbose_name="Camera Setup",
        help_text="e.g., 50MP + 12MP + 12MP"
    )
    
    front_camera = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Front Camera"
    )
    
    video_recording = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Video Recording"
    )
    
    # Battery & Connectivity
    battery_capacity = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Battery Capacity"
    )
    
    charging_speed = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Charging Speed"
    )
    
    network = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Network",
        help_text="e.g., 5G, 4G LTE"
    )
    
    sim_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="SIM Type"
    )
    
    # Dimensions & Build
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Dimensions"
    )
    
    weight = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Weight"
    )
    
    build_material = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Build Material"
    )
    
    colors = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Available Colors",
        help_text="Comma separated list of colors"
    )
    
    # ==================== DESCRIPTIONS ====================
    description = models.TextField(
        blank=True,
        verbose_name="Product Description"
    )
    
    features = models.TextField(
        blank=True,
        verbose_name="Key Features",
        help_text="One feature per line"
    )
    
    whats_in_box = models.TextField(
        blank=True,
        verbose_name="What's in the Box",
        help_text="List of items included"
    )
    
    # ==================== MEDIA ====================
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name="Main Product Image"
    )
    
    # You can create a separate ProductImage model for gallery
    # class ProductImage(models.Model):
    #     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    #     image = models.ImageField(upload_to='products/gallery/')
    #     is_default = models.BooleanField(default=False)
    #     created_at = models.DateTimeField(auto_now_add=True)
    
    # ==================== INVENTORY ====================
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Quantity"
    )
    
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name="Low Stock Threshold"
    )
    
    allow_backorder = models.BooleanField(
        default=False,
        verbose_name="Allow Backorder"
    )
    
    # ==================== STATUS ====================
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Product is visible to customers"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured",
        help_text="Show in featured products section"
    )
    
    is_new = models.BooleanField(
        default=False,
        verbose_name="New Arrival",
        help_text="Mark as new product"
    )
    
    is_best_seller = models.BooleanField(
        default=False,
        verbose_name="Best Seller"
    )
    
    # ==================== WARRANTY & SUPPORT ====================
    warranty = models.CharField(
        max_length=100,
        blank=True,
        default="1 Year",
        verbose_name="Warranty Period"
    )
    
    warranty_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Warranty Type",
        help_text="e.g., Manufacturer, Seller"
    )
    
    return_policy = models.CharField(
        max_length=200,
        blank=True,
        default="7 Days Return Policy",
        verbose_name="Return Policy"
    )
    
    # ==================== SEO & METADATA ====================
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Meta Title"
    )
    
    meta_description = models.TextField(
        blank=True,
        verbose_name="Meta Description"
    )
    
    meta_keywords = models.TextField(
        blank=True,
        verbose_name="Meta Keywords",
        help_text="Comma separated keywords"
    )
    
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Product Tags",
        help_text="Comma separated tags for filtering"
    )
    
    # ==================== RATING & REVIEWS ====================
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name="Average Rating"
    )
    
    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Reviews"
    )
    
    total_sold = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Sold"
    )
    
    # ==================== TIMESTAMPS ====================
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Published At"
    )

    # ==================== METHODS ====================
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Auto-generate SKU if not provided
        if not self.sku:
            # Generate SKU from brand, category, and timestamp
            brand_code = self.brand.name[:3].upper() if self.brand else "PRO"
            category_code = self.category.name[:3].upper() if self.category else "GEN"
            timestamp = str(int(time.time()))[-6:]
            self.sku = f"{brand_code}-{category_code}-{timestamp}"
        
        # Set published_at if product is being activated
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.brand.name if self.brand else 'No Brand'}"
    
    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount, 1)
        return 0
    
    def get_discount_amount(self):
        """Calculate discount amount"""
        if self.compare_price and self.compare_price > self.price:
            return self.compare_price - self.price
        return 0
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    def is_low_stock(self):
        """Check if product is low in stock"""
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    def get_stock_status(self):
        """Get stock status text"""
        if self.stock_quantity == 0:
            return "Out of Stock"
        elif self.stock_quantity <= self.low_stock_threshold:
            return "Low Stock"
        else:
            return "In Stock"
    
    def get_colors_list(self):
        """Convert colors string to list"""
        if self.colors:
            return [color.strip() for color in self.colors.split(',')]
        return []
    
    def get_features_list(self):
        """Convert features text to list"""
        if self.features:
            return [feature.strip() for feature in self.features.split('\n') if feature.strip()]
        return []
    
    def get_tags_list(self):
        """Convert tags string to list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def get_absolute_url(self):
        """Get absolute URL for product"""
        from django.urls import reverse
        return reverse('product_detail', kwargs={'slug': self.slug})
    
    @property
    def display_price(self):
        """Get display price with currency symbol"""
        return f"৳{self.price:,}"
    
    @property
    def display_compare_price(self):
        """Get display compare price with currency symbol"""
        if self.compare_price:
            return f"৳{self.compare_price:,}"
        return None
    
    @property
    def thumbnail_url(self):
        """Get thumbnail URL"""
        if self.image:
            return self.image.url
        return "/static/images/product-placeholder.jpg"

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



# =========================
# ORDER
# =========================
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

    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='pending'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)

    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------- utils ----------
    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        return "ORD-" + ''.join(random.choices(string.digits, k=8))

    def update_totals(self):
        items = self.items.all()
        subtotal = sum(item.total_price for item in items)
        self.subtotal = subtotal
        self.total_amount = subtotal
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
        
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-added_at']