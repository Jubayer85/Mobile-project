from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Sum, F
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.db.models import Count
from django.utils.text import slugify
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings 
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import CategoryForm, SubCategoryForm, BrandForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ( Product, Brand, Category,SubCategory,ProductImage,Cart, CartItem,Order, OrderItem, Customer)
from .forms import ProductForm, ProductImageFormSet

# ====================== HOME ======================
def home(request):
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    new_arrivals = Product.objects.filter(
        is_active=True,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:8]

    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:8]

    brands = Brand.objects.all()   # ✅ safe

    return render(request, 'home.html', {
        'new_arrivals': new_arrivals,
        'featured_products': featured_products,
        'brands': brands,
    })



# ====================== AUTH ======================
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_redirect(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'profile.html')

# ====================== DASHBOARDS ======================
@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
def user_dashboard(request):
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer)
    
    return render(request, 'user_dashboard.html', {
        'total_orders': orders.count(),
        'active_orders': orders.filter(status__in=['pending', 'processing', 'shipped']).count(),
        'recent_orders': orders.order_by('-created_at')[:5]
    })

# ====================== PRODUCT ADMIN ======================
@staff_member_required
def admin_product_list(request):
    products = Product.objects.select_related('brand', 'category').order_by('-created_at')
    return render(request, 'admin_product_list.html', {'products': products})

@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

@staff_member_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated!')
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'edit_product.html', {
        'form': form,
        'product': product
    })

@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted!')
    return redirect('admin_product_list')

# ====================== PRODUCT DETAIL ======================
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    related_products = Product.objects.filter(
        brand=product.brand,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products
    })

# ====================== CART ======================
@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    
    total = sum(item.product.price * item.quantity for item in items)
    
    return render(request, 'cart.html', {
        'cart': cart,
        'items': items,
        'total': total
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if product.stock_quantity < 1:
        messages.warning(request, f"Sorry, {product.name} is out of stock.")
        return redirect('product_detail', slug=product.slug)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity >= product.stock_quantity:
            messages.warning(request, f"Maximum available quantity reached for {product.name}.")
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Added another {product.name} to cart.")
    else:
        messages.success(request, f"Added {product.name} to cart.")
    
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_detail')

@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, "Cart cleared.")
    return redirect('cart_detail')

# ====================== CHECKOUT ======================
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product')
    
    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')
    
    # Check stock
    for item in items:
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f"Not enough stock for {item.product.name}.")
            return redirect('cart_detail')
    
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            customer = Customer.objects.create(user=request.user)
        
        order = Order.objects.create(
            customer=customer,
            payment_method='cod',
            shipping_address=request.POST.get('shipping_address', ''),
            subtotal=sum(item.product.price * item.quantity for item in items),
            total_amount=sum(item.product.price * item.quantity for item in items)
        )
        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity
            )
            
            # Reduce stock
            item.product.stock_quantity -= item.quantity
            item.product.save()
        
        # Clear cart
        items.delete()
        
        messages.success(request, "Order placed successfully!")
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'checkout.html', {
        'cart': cart,
        'items': items,
        'total': sum(item.product.price * item.quantity for item in items)
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, 'order_success.html', {'order': order})



@login_required
def order_history(request):
    """User order history page"""
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    context = {
        'orders': orders,
        'total_orders': orders.count(),
    }
    
    return render(request, 'order_history.html', context)

# ====================== ADMIN ORDERS ======================
@staff_member_required
def admin_order_list(request):
    orders = Order.objects.select_related('customer__user').order_by('-created_at')
    return render(request, 'admin/order_list.html', {'orders': orders})



@staff_member_required
def admin_user_list(request):
    users = User.objects.annotate(
        total_orders=Count('customer__orders')
    ).order_by('-date_joined')

    return render(
        request,
        'admin/user_list.html',
        {'users': users}
    )


def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST.get("status")
        order.save(update_fields=["status"])

    context = {
        "order": order,
        "status_choices": Order.ORDER_STATUS,  # 🔴 এটা MUST
    }
    return render(request, "admin/order_detail.html", context)
    
    # Update status change form
    if request.method == 'POST' and 'status' in request.POST:
        new_status = request.POST.get('status')
        old_status = order.status
        
        if new_status != old_status:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            
            # Log status change
            messages.success(request, f'Order status updated from {old_status} to {new_status}')
            
            # Create notification/activity log
            from .models import OrderActivity
            OrderActivity.objects.create(
                order=order,
                user=request.user,
                activity_type='status_change',
                description=f'Status changed from {old_status} to {new_status}'
            )
            
            return redirect('admin_order_detail', order_id=order_id)
    
    context = {
        'order': order,
        'items': items,
        'item_total': item_total,
        'timeline': order_timeline,
        'STATUS_CHOICES': Order.ORDER_STATUS,
    }
    
    return render(request, 'admin/order_detail.html', context)
        



# ====================== HTMX CATEGORY/BRAND ======================
@staff_member_required
@require_http_methods(["POST"])
def add_category(request):
    name = request.POST.get('name', '').strip()
    if name:
        category = Category.objects.create(
            name=name,
            slug=name.lower().replace(' ', '-')
        )
        
        html = render_to_string('admin/partials/category_option.html', {
            'category': category
        })
        return HttpResponse(html)
    
    return HttpResponse(status=400)


@staff_member_required
@require_http_methods(["POST"])
def add_subcategory(request):
    name = request.POST.get("name")
    category_id = request.POST.get("category")

    if not name or not category_id:
        return HttpResponse(status=400)

    category = get_object_or_404(Category, id=category_id)

    subcategory = SubCategory.objects.create(
        name=name,
        category=category
    )

    return render(
        request,
        "admin/partials/subcategory_option.html",
        {"subcategory": subcategory}
    )


@staff_member_required
def load_subcategories(request):
    category_id = request.GET.get("category")

    subcategories = SubCategory.objects.filter(
        category_id=category_id
    ).order_by("name")

    html = render_to_string(
        "admin/partials/subcategory_options.html",
        {"subcategories": subcategories}
    )

    return HttpResponse(html)

@staff_member_required
@require_http_methods(["POST"])
def add_brand(request):
    name = request.POST.get('name', '').strip()
    if name:
        brand = Brand.objects.create(
            name=name,
            slug=name.lower().replace(' ', '-')
        )
        
        html = render_to_string('admin/partials/brand_option.html', {
            'brand': brand
        })
        return HttpResponse(html)
    
    return HttpResponse(status=400)



@staff_member_required
def add_category_modal(request):
    """Modal for adding category"""
    return render(request, 'admin/partials/add_category.html')




@staff_member_required
def subcategory_modal(request):
    categories = Category.objects.all()   # 🔴 THIS LINE IS MUST

    return render(
        request,
        "admin/partials/subcategory_modal.html",
        {
            "categories": categories
        }
    )

@staff_member_required
def add_brand_modal(request):
    """Modal for adding brand"""
    return render(request, 'admin/partials/add_brand.html')




def subcategory_products(request, slug):
    products = Product.objects.filter(subcategory__slug=slug, is_active=True)
    return render(request, 'product_list.html', {'products': products})

def brand_products(request, slug):
    products = Product.objects.filter(brand__slug=slug, is_active=True)
    return render(request, 'product_list.html', {'products': products})

def category_products(request, slug):
    products = Product.objects.filter(
        category__slug=slug,
        is_active=True
    ).select_related('category', 'brand')

    return render(request, 'product_list.html', {
        'products': products,
        'page_title': slug.replace('-', ' ').title()
    })




def category_products(request, slug):
    """Category-র সব প্রোডাক্ট"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products from this category and its subcategories
    subcategory_ids = category.subcategories.filter(is_active=True).values_list('id', flat=True)
    
    products_list = Product.objects.filter(
        Q(category=category) |  # Use Q instead of models.Q
        Q(subcategory__id__in=subcategory_ids),
        is_active=True
    ).distinct()
    
    # Pagination
    paginator = Paginator(products_list, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': products,
        'subcategories': category.subcategories.filter(is_active=True)
    }
    return render(request, 'products/product_list.html', context)

def subcategory_products(request, slug):
    """SubCategory-র প্রোডাক্ট"""
    subcategory = get_object_or_404(SubCategory, slug=slug, is_active=True)
    
    products_list = Product.objects.filter(
        subcategory=subcategory,
        is_active=True
    )
    
    # Pagination
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'subcategory': subcategory,
        'category': subcategory.category,
        'products': products
    }
    return render(request, 'products/product_list.html', context)



@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_categories(request):
    """Category, SubCategory and Brand management page"""
    categories = Category.objects.all().prefetch_related('subcategories', 'products')
    subcategories = SubCategory.objects.all().select_related('category')
    brands = Brand.objects.all().prefetch_related('products')
    
    context = {
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
    }
    return render(request, 'admin/manage_categories.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_category(request, category_id):
    """Edit an existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('manage_categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category'
    }
    return render(request, 'admin/edit_category.html', context)




@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_subcategory(request, subcategory_id):
    """Edit an existing subcategory"""
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            messages.success(request, 'SubCategory updated successfully!')
            return redirect('manage_categories')
    else:
        form = SubCategoryForm(instance=subcategory)
    
    context = {
        'form': form,
        'subcategory': subcategory,
        'title': 'Edit SubCategory'
    }
    return render(request, 'admin/edit_subcategory.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_brand(request, brand_id):
    """Edit an existing brand"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand updated successfully!')
            return redirect('manage_categories')
    else:
        form = BrandForm(instance=brand)
    
    context = {
        'form': form,
        'brand': brand,
        'title': 'Edit Brand'
    }
    return render(request, 'admin/edit_brand.html', context)

def categories(request):
    """
    Admin categories management view
    """
    # শুধুমাত্র admin/user access দিতে চাইলে
    if not request.user.is_staff:
        return redirect('home')
    
    categories = Category.objects.all()
    return render(request, 'admin/categories.html', {'categories': categories})

# Placeholder views for footer links
def shop_all(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'products/shop_all.html', {'products': products})
def brand_list(request):
    brands = Brand.objects.all()
    return render(request, 'brands/brand_list.html', {'brands': brands})
def new_arrivals(request):
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:20]
    return render(request, 'products/new_arrivals.html', {'products': products})

def best_sellers(request):
    # You'll need to implement logic for best sellers
    products = Product.objects.filter(is_active=True)[:20]
    return render(request, 'products/best_sellers.html', {'products': products})

def apple_products(request):
    try:
        apple_brand = Brand.objects.get(name__icontains='apple')
        products = Product.objects.filter(brand=apple_brand, is_active=True)
    except Brand.DoesNotExist:
        products = Product.objects.none()
    return render(request, 'products/apple_products.html', {'products': products})

def gaming_phones(request):
    products = Product.objects.filter(
        is_active=True,
        category__name__icontains='gaming'
    )
    return render(request, 'products/gaming_phones.html', {'products': products})

def special_offers(request):
    products = Product.objects.filter(
        is_active=True,
        discount_price__isnull=False
    )
    return render(request, 'products/special_offers.html', {'products': products})

# Information pages
def contact_us(request):
    """Handle contact form submission and display contact page"""
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        # Basic validation
        if not all([first_name, last_name, email, subject, message_text]):
            messages.error(request, 'Please fill in all required fields.')
        elif len(message_text) < 20:
            messages.error(request, 'Message must be at least 20 characters long.')
        else:
            # Create email message
            full_name = f"{first_name} {last_name}"
            email_subject = f"Contact Form: {subject}"
            email_message = f"""
            New Contact Form Submission:
            
            Name: {full_name}
            Email: {email}
            Phone: {phone}
            Subject: {subject}
            
            Message:
            {message_text}
            
            ---
            This message was sent from your website contact form.
            """
            
            try:
                # Send email (configure email settings in settings.py)
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL] if hasattr(settings, 'CONTACT_EMAIL') else [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                
                # Success message
                messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
                
                # Clear form by redirecting
                return redirect('contact_us')
                
            except Exception as e:
                # Log error and show message
                print(f"Email sending error: {e}")
                messages.error(request, 'There was an error sending your message. Please try again later.')
    
    # For GET requests or after POST with errors
    return render(request, 'pages/contact.html')

def faq(request):
    return render(request, 'pages/faq.html')

def shipping_policy(request):
    return render(request, 'pages/shipping_policy.html')

def return_policy(request):
    return render(request, 'pages/return_policy.html')

def privacy_policy(request):
    return render(request, 'pages/privacy_policy.html')

def terms_conditions(request):
    return render(request, 'pages/terms_conditions.html')

def warranty_policy(request):
    return render(request, 'pages/warranty_policy.html')

def track_order(request):
    return render(request, 'pages/track_order.html')

def newsletter_subscribe(request):
    # Simple implementation
    if request.method == 'POST':
        email = request.POST.get('email')
        # Save to database or send to email service
        return HttpResponse('Subscribed successfully!', status=200)
    return HttpResponse('Method not allowed', status=405)

