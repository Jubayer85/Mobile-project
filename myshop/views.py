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
from django.contrib.auth.models import User
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

from django.contrib.auth.decorators import login_required
from django.conf import settings

@login_required
def user_dashboard(request):
    user = request.user

    # User's orders (Order.customer = AUTH_USER_MODEL হলে)
    orders = Order.objects.filter(customer=user)

    context = {
        'user': user,
        'total_orders': orders.count(),
        'active_orders': orders.filter(
            status__in=['pending', 'processing', 'shipped']
        ).count(),
        'completed_orders': orders.filter(status='delivered').count(),
        'recent_orders': orders.order_by('-created_at')[:5],
    }

    return render(request, 'user_dashboard.html', context)

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

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product')

    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')

    # Stock check
    for item in items:
        if item.quantity > item.product.stock_quantity:
            messages.error(
                request,
                f"Not enough stock for {item.product.name}."
            )
            return redirect('cart_detail')

    if request.method == 'POST':
        user = request.user

        shipping_address = request.POST.get('shipping_address', '').strip()

        order = Order.objects.create(
            customer=user,                      # ✅ FIXED
            payment_method='cod',
            shipping_address=shipping_address,
            subtotal=sum(item.product.price * item.quantity for item in items),
            total_amount=sum(item.product.price * item.quantity for item in items),
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
            item.product.save(update_fields=['stock_quantity'])

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
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user      # ✅ FIX
    )
    return render(request, 'order_success.html', {'order': order})



@login_required
def order_history(request):
    orders = (
        Order.objects
        .filter(customer=request.user)
        .order_by('-created_at')
    )

    return render(request, 'order_history.html', {
        'orders': orders,
        'total_orders': orders.count(),
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user
    )
    return render(request, 'order_detail.html', {'order': order})

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
def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    # Calculate stats
    total_categories = Category.objects.count()
    total_subcategories = SubCategory.objects.count()
    total_brands = Brand.objects.count()
    
    # Get all data
    categories = Category.objects.all().prefetch_related('subcategories')
    subcategories = SubCategory.objects.select_related('category').all()
    brands = Brand.objects.all()
    
    context = {
        'page_title': 'Category Management',
        'total_categories': total_categories,
        'total_subcategories': total_subcategories,
        'total_brands': total_brands,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
    }
    return render(request, 'admin/manage_categories.html', context)

# Category CRUD Views
@login_required
@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'true'
        icon = request.POST.get('icon', 'fas fa-boxes')
        
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('manage_categories')
        
        category = Category.objects.create(
            name=name,
            description=description,
            is_active=is_active,
            icon=icon
        )
        messages.success(request, f'Category "{name}" added successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/add_category.html')

@login_required
@user_passes_test(is_admin)
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'true'
        icon = request.POST.get('icon', 'fas fa-boxes')
        
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('manage_categories')
        
        category.name = name
        category.description = description
        category.is_active = is_active
        category.icon = icon
        category.save()
        
        messages.success(request, f'Category "{name}" updated successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/edit_category.html', {'category': category})

@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': category,
        'object_type': 'category'
    })

@login_required
@user_passes_test(is_admin)
def toggle_category_status(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    
    status = "activated" if category.is_active else "deactivated"
    messages.success(request, f'Category "{category.name}" {status} successfully!')
    return redirect('manage_categories')

@login_required
@user_passes_test(is_admin)
def toggle_category_status(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.is_active = not category.is_active
        category.save()
        
        status = "activated" if category.is_active else "deactivated"
        message = f'Category "{category.name}" {status} successfully!'
        
        # If it's an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': message,
                'is_active': category.is_active
            })
        
        messages.success(request, message)
    
    return redirect('manage_categories')

# Alternative: Create a combined view that handles all category operations
@login_required
@user_passes_test(is_admin)
def category_actions(request, pk=None):
    """
    Combined view for category CRUD operations using HTMX
    """
    if request.method == 'GET' and not pk:
        # Get category list for HTMX requests
        categories = Category.objects.all()
        return render(request, 'admin/partials/category_list.html', {
            'categories': categories
        })
    
    if pk:
        category = get_object_or_404(Category, pk=pk)
        
        if request.method == 'GET':
            # Return category data for editing
            return JsonResponse({
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'is_active': category.is_active,
                'icon': category.icon,
                'image_url': category.image.url if category.image else ''
            })
        
        elif request.method == 'POST':
            # Update category
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'true'
            icon = request.POST.get('icon', 'fas fa-boxes')
            
            category.name = name
            category.description = description
            category.is_active = is_active
            category.icon = icon
            
            if 'image' in request.FILES:
                category.image = request.FILES['image']
            
            category.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Category updated successfully'
            })
        
        elif request.method == 'DELETE':
            # Delete category
            category.delete()
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })
    
    else:
        # Create new category
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'true'
            icon = request.POST.get('icon', 'fas fa-boxes')
            
            category = Category.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                icon=icon
            )
            
            if 'image' in request.FILES:
                category.image = request.FILES['image']
                category.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Category created successfully',
                'category_id': category.id
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Subcategory CRUD Views
@login_required
@user_passes_test(is_admin)
def add_subcategory(request):
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        is_active = request.POST.get('is_active') == 'true'
        
        if not name or not category_id:
            messages.error(request, 'Subcategory name and parent category are required.')
            return redirect('manage_categories')
        
        category = get_object_or_404(Category, pk=category_id)
        
        subcategory = SubCategory.objects.create(
            category=category,
            name=name,
            description=description,
            is_active=is_active
        )
        
        messages.success(request, f'Subcategory "{name}" added successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/add_subcategory.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def edit_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        is_active = request.POST.get('is_active') == 'true'
        
        if not name or not category_id:
            messages.error(request, 'Subcategory name and parent category are required.')
            return redirect('manage_categories')
        
        category = get_object_or_404(Category, pk=category_id)
        
        subcategory.name = name
        subcategory.description = description
        subcategory.category = category
        subcategory.is_active = is_active
        subcategory.save()
        
        messages.success(request, f'Subcategory "{name}" updated successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/edit_subcategory.html', {
        'subcategory': subcategory,
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def delete_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    if request.method == 'POST':
        subcategory_name = subcategory.name
        subcategory.delete()
        messages.success(request, f'Subcategory "{subcategory_name}" deleted successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': subcategory,
        'object_type': 'subcategory'
    })

@login_required
@user_passes_test(is_admin)
def toggle_subcategory_status(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    subcategory.is_active = not subcategory.is_active
    subcategory.save()
    
    status = "activated" if subcategory.is_active else "deactivated"
    messages.success(request, f'Subcategory "{subcategory.name}" {status} successfully!')
    return redirect('manage_categories')

# Brand CRUD Views
@login_required
@user_passes_test(is_admin)
def add_brand(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        tier = request.POST.get('tier', 'standard')
        website = request.POST.get('website')
        country = request.POST.get('country')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        is_active = request.POST.get('is_active') == 'true'
        is_featured = request.POST.get('is_featured') == 'true'
        show_in_brands = request.POST.get('show_in_brands') == 'true'
        logo = request.FILES.get('logo')
        
        if not name:
            messages.error(request, 'Brand name is required.')
            return redirect('manage_categories')
        
        try:
            # Create brand with only the fields that exist in your model
            brand_data = {
                'name': name,
                'description': description,
                'tier': tier,
                'website': website or None,
                'country': country or None,
                'meta_title': meta_title or None,
                'meta_description': meta_description or None,
                'is_active': is_active,
                'is_featured': is_featured,
                'show_in_brands': show_in_brands,
            }
            
            # Create brand instance
            brand = Brand(**brand_data)
            
            # Save to generate slug
            brand.save()
            
            # Add logo after saving (to handle image upload)
            if logo:
                brand.logo = logo
                brand.save()
            
            messages.success(request, f'Brand "{name}" added successfully!')
            return redirect('manage_categories')
            
        except Exception as e:
            messages.error(request, f'Error adding brand: {str(e)}')
            return redirect('manage_categories')
    
    # GET request - show form
    return render(request, 'admin/add_brand.html')

@login_required
@user_passes_test(is_admin)
def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        logo_initials = request.POST.get('logo_initials', name[:2].upper())
        tier = request.POST.get('tier', 'standard')
        is_active = request.POST.get('is_active') == 'true'
        category_ids = request.POST.getlist('categories')
        
        if not name:
            messages.error(request, 'Brand name is required.')
            return redirect('manage_categories')
        
        brand.name = name
        brand.description = description
        brand.logo_initials = logo_initials
        brand.tier = tier
        brand.is_active = is_active
        brand.save()
        
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            brand.categories.set(categories)
        else:
            brand.categories.clear()
        
        messages.success(request, f'Brand "{name}" updated successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/edit_brand.html', {
        'brand': brand,
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def delete_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        brand_name = brand.name
        brand.delete()
        messages.success(request, f'Brand "{brand_name}" deleted successfully!')
        return redirect('manage_categories')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': brand,
        'object_type': 'brand'
    })

@login_required
@user_passes_test(is_admin)
def toggle_brand_status(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.is_active = not brand.is_active
    brand.save()
    
    status = "activated" if brand.is_active else "deactivated"
    messages.success(request, f'Brand "{brand.name}" {status} successfully!')
    return redirect('manage_categories')


# ====================== FRONTEND VIEWS ======================

def category_products(request, slug):
    """View products by category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    subcategories = SubCategory.objects.filter(category=category, is_active=True)
    
    # Get brands available in this category
    brands = Brand.objects.filter(
        categories=category,
        is_active=True
    ).distinct()
    
    # Filtering logic
    selected_brands = request.GET.getlist('brand')
    selected_subcategories = request.GET.getlist('subcategory')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('q', '')
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        )
    
    # Apply brand filter
    if selected_brands:
        products = products.filter(brand__id__in=selected_brands)
    
    # Apply subcategory filter
    if selected_subcategories:
        products = products.filter(subcategory__id__in=selected_subcategories)
    
    # Apply price filter
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popular':
        # You might want to add a popularity field or use order count
        products = products.order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'brands': brands,
        'selected_brands': selected_brands,
        'selected_subcategories': selected_subcategories,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'search_query': search_query,
        'product_count': products.count(),
    }
    return render(request, 'products/category_products.html', context)

def subcategory_products(request, category_slug, subcategory_slug):
    """View products by subcategory"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(
        SubCategory, 
        slug=subcategory_slug, 
        category=category,
        is_active=True
    )
    
    # Get products in this subcategory
    products = Product.objects.filter(
        subcategory=subcategory,
        is_active=True
    )
    
    # Get other subcategories in same category
    other_subcategories = SubCategory.objects.filter(
        category=category,
        is_active=True
    ).exclude(id=subcategory.id)
    
    # Get brands available in this subcategory
    brands = Brand.objects.filter(
        products__subcategory=subcategory,
        is_active=True
    ).distinct()
    
    # Filtering logic (same as category_products)
    selected_brands = request.GET.getlist('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('q', '')
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        )
    
    # Apply brand filter
    if selected_brands:
        products = products.filter(brand__id__in=selected_brands)
    
    # Apply price filter
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popular':
        products = products.order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'products': products,
        'other_subcategories': other_subcategories,
        'brands': brands,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'search_query': search_query,
        'product_count': products.count(),
    }
    return render(request, 'products/subcategory_products.html', context)

def brand_products(request, slug):
    """View products by brand"""
    brand = get_object_or_404(Brand, slug=slug, is_active=True)
    
    # Get products for this brand
    products = Product.objects.filter(brand=brand, is_active=True)
    
    # Get categories where this brand has products
    categories = Category.objects.filter(
        products__brand=brand,
        is_active=True
    ).distinct()
    
    # Get subcategories where this brand has products
    subcategories = SubCategory.objects.filter(
        products__brand=brand,
        is_active=True
    ).distinct()
    
    # Filtering logic
    selected_categories = request.GET.getlist('category')
    selected_subcategories = request.GET.getlist('subcategory')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('q', '')
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter
    if selected_categories:
        products = products.filter(category__id__in=selected_categories)
    
    # Apply subcategory filter
    if selected_subcategories:
        products = products.filter(subcategory__id__in=selected_subcategories)
    
    # Apply price filter
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popular':
        products = products.order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Get other brands in same categories
    other_brands = Brand.objects.filter(
        categories__in=categories,
        is_active=True
    ).exclude(id=brand.id).distinct()[:10]
    
    context = {
        'brand': brand,
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
        'other_brands': other_brands,
        'selected_categories': selected_categories,
        'selected_subcategories': selected_subcategories,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'search_query': search_query,
        'product_count': products.count(),
    }
    return render(request, 'products/brand_products.html', context)

def product_detail(request, slug):
    """Product detail view"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:8]
    
    # Get other products from same brand
    same_brand_products = Product.objects.filter(
        brand=product.brand,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
        'same_brand_products': same_brand_products,
    }
    return render(request, 'products/product_detail.html', context)

def search_products(request):
    """Search products across all categories"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    brand_id = request.GET.get('brand', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'relevance')
    
    # Start with all active products
    products = Product.objects.filter(is_active=True)
    
    # Apply search query
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query) |
            Q(brand__name__icontains=query)
        )
    
    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Apply brand filter
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # Apply price filter
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:  # relevance (default)
        # You could implement more sophisticated relevance sorting
        products = products.order_by('-created_at')
    
    # Get all categories and brands for filters
    all_categories = Category.objects.filter(is_active=True)
    all_brands = Brand.objects.filter(is_active=True)
    
    # Get unique categories and brands from search results
    result_categories = Category.objects.filter(
        products__in=products,
        is_active=True
    ).distinct()
    
    result_brands = Brand.objects.filter(
        products__in=products,
        is_active=True
    ).distinct()
    
    context = {
        'products': products,
        'query': query,
        'all_categories': all_categories,
        'all_brands': all_brands,
        'result_categories': result_categories,
        'result_brands': result_brands,
        'selected_category': category_id,
        'selected_brand': brand_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'product_count': products.count(),
    }
    return render(request, 'products/search_results.html', context)
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

