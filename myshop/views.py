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
from .models import ( Product, Brand, Category,SubCategory,ProductImage,Cart, CartItem,Order, OrderItem, Customer, Wishlist)
from .forms import ProductForm, ProductImageFormSet
from .models import Order, OrderItem
from django.views.decorators.http import require_POST



# ====================== HOME ======================
def home(request):
    categories = Category.objects.filter(is_active=True)[:6]

    new_arrivals = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:8]

    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    )[:8]

    context = {
        'categories': categories,
        'new_arrivals': new_arrivals,
        'featured_products': featured_products,
    }

    return render(request, 'home.html', context)


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
    categories = Category.objects.filter(is_active=True)
    subcategories = SubCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
    }

    return render(request, 'admin/add_product.html', context)
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

def product_detail(request, slug):
    # ---------------------------
    # Get main product
    # ---------------------------
    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True
    )

    # ---------------------------
    # Related products (same brand)
    # ---------------------------
    related_products = Product.objects.filter(
        brand=product.brand,
        is_active=True
    ).exclude(id=product.id)[:4]

    # ---------------------------
    # Recently viewed products
    # ---------------------------
    recently_viewed = Product.objects.filter(
        is_active=True
    ).exclude(id=product.id).order_by('-created_at')[:6]

    # ---------------------------
    # Popular / Featured products
    # ---------------------------
    popular_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).exclude(id=product.id)[:6]

    # ---------------------------
    # Colors list
    # ---------------------------
    colors_list = []
    if product.colors:
        colors_list = [
            color.strip()
            for color in product.colors.split(',')
            if color.strip()
        ]

    # ---------------------------
    # Features list
    # ---------------------------
    features_list = []
    if product.features:
        features_list = [
            feature.strip()
            for feature in product.features.splitlines()
            if feature.strip()
        ]

    # ---------------------------
    # Discount calculation
    # ---------------------------
    discount_percent = 0
    discount_amount = 0

    if product.compare_price and product.compare_price > product.price:
        discount_amount = product.compare_price - product.price
        discount_percent = int(
            (discount_amount / product.compare_price) * 100
        )

    # ---------------------------
    # Stock status
    # ---------------------------
    if product.stock_quantity > 10:
        stock_status = "In Stock"
    elif product.stock_quantity > 0:
        stock_status = "Low Stock"
    else:
        stock_status = "Out of Stock"

    # ---------------------------
    # Specifications
    # ---------------------------
    specifications = {
        "display": product.display_size or '6.7" AMOLED',
        "ram": product.ram or "8GB",
        "storage": product.storage or "256GB",
        "processor": product.processor or "Snapdragon 8 Gen 3",
        "camera": product.camera or "50MP + 12MP + 12MP",
        "battery": product.battery_capacity or "5000 mAh",
        "os": product.os or "Android 14 / iOS 17",
        "connectivity": "5G, Wi-Fi 6, Bluetooth 5.3",
    }

    # ---------------------------
    # Performance metrics (UI only)
    # ---------------------------
    performance_metrics = [
        {"name": "Performance", "score": 9.2},
        {"name": "Camera", "score": 9.5},
        {"name": "Battery Life", "score": 8.8},
        {"name": "Display Quality", "score": 9.3},
        {"name": "Build Quality", "score": 9.0},
        {"name": "Software", "score": 8.7},
    ]

    # ---------------------------
    # Breadcrumb data
    # ---------------------------
    category = product.category
    subcategory = product.subcategory

    # ---------------------------
    # Warranty
    # ---------------------------
    warranty = product.warranty or "1 Year"

    # ---------------------------
    # Context
    # ---------------------------
    context = {
        "product": product,
        "category": category,
        "subcategory": subcategory,

        "related_products": related_products,
        "recently_viewed": recently_viewed,
        "popular_products": popular_products,

        "colors_list": colors_list,
        "features_list": features_list,

        "discount_percent": discount_percent,
        "discount_amount": discount_amount,

        "stock_status": stock_status,
        "specifications": specifications,
        "performance_metrics": performance_metrics,
        "warranty": warranty,
    }

    return render(request, "product_detail.html", context)


def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            # Here you would add wishlist logic
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to wishlist'
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def compare_product(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            # Here you would add comparison logic
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to comparison'
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# ====================== CART ======================
def cart_detail(request):
    cart_items = []
    total_items = 0
    total_price = 0

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)

        for item in cart.items.select_related('product'):
            product = item.product
            quantity = item.quantity

            cart_items.append({
                'id': item.id,
                'name': product.name,
                'slug': product.slug,
                'price': product.price,
                'image': product.image.url if product.image else '',
                'quantity': quantity,
                'subtotal': product.price * quantity,
                'stock_quantity': product.stock_quantity,  # ✅ FIX
                'max_allowed': min(product.stock_quantity, 10) if product.stock_quantity > 0 else 0
            })

            total_items += quantity
            total_price += product.price * quantity

    else:
        cart_data = request.session.get('cart', {})

        for product_id, item_data in cart_data.items():
            try:
                product = Product.objects.get(id=product_id)
                quantity = item_data.get('quantity', 1)

                cart_items.append({
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'price': product.price,
                    'image': product.image.url if product.image else '',
                    'quantity': quantity,
                    'subtotal': product.price * quantity,
                    'stock_quantity': product.stock_quantity,
                    'max_allowed': min(product.stock_quantity, 10) if product.stock_quantity > 0 else 0
                })

                total_items += quantity
                total_price += product.price * quantity

            except Product.DoesNotExist:
                continue

    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
        'is_cart_empty': len(cart_items) == 0,
    }

    return render(request, 'cart/cart_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product
            )
            
            if not item_created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            
            cart_item.save()
            messages.success(request, f'{product.name} added to cart!')
        else:
            # Session-based cart for guests
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                cart[product_id_str]['quantity'] += quantity
            else:
                cart[product_id_str] = {
                    'quantity': quantity,
                    'product_id': product_id
                }
            
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f'{product.name} added to cart!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart',
                'cart_count': get_cart_count(request),
            })
        
        return redirect('cart_detail')
    
    return redirect('product_detail', slug=product.slug)

def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    else:
        # Remove from session cart
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        if item_id_str in cart:
            del cart[item_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, 'Item removed from cart')
    
    return redirect('cart_detail')

def clear_cart(request):
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
    else:
        request.session['cart'] = {}
        request.session.modified = True
    
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart_detail')

def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            
            if request.user.is_authenticated:
                cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
                cart_item.quantity = quantity
                cart_item.save()
                
                # Get updated cart data
                cart = cart_item.cart
                item_subtotal = cart_item.product.selling_price * quantity
                cart_summary = {
                    'total_items': cart.total_items(),
                    'total_price': cart.total_price(),
                }
                
                response_data = {
                    'success': True,
                    'message': 'Cart updated successfully',
                    'item_id': item_id,
                    'item_quantity': quantity,
                    'item_price': cart_item.product.selling_price,
                    'item_subtotal': item_subtotal,
                    'cart_summary': cart_summary,
                }
            else:
                # Update session cart
                cart = request.session.get('cart', {})
                item_id_str = str(item_id)
                if item_id_str in cart:
                    cart[item_id_str]['quantity'] = quantity
                    request.session['cart'] = cart
                    request.session.modified = True
                    
                    # Calculate cart summary for session
                    total_items = sum(item['quantity'] for item in cart.values())
                    total_price = 0
                    for product_id, item_data in cart.items():
                        try:
                            product = Product.objects.get(id=product_id)
                            total_price += product.selling_price * item_data['quantity']
                        except Product.DoesNotExist:
                            continue
                    
                    response_data = {
                        'success': True,
                        'message': 'Cart updated successfully',
                        'item_id': item_id,
                        'item_quantity': quantity,
                        'item_price': cart[item_id_str].get('price', 0),
                        'item_subtotal': cart[item_id_str].get('price', 0) * quantity,
                        'cart_summary': {
                            'total_items': total_items,
                            'total_price': total_price,
                        },
                    }
                else:
                    response_data = {
                        'success': False,
                        'message': 'Item not found in cart',
                    }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
def get_cart_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart.total_items()
    else:
        cart = request.session.get('cart', {})
        return sum(item['quantity'] for item in cart.values())
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product')

    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')

    # ✅ Stock check
    for item in items:
        if item.quantity > item.product.stock_quantity:
            messages.error(
                request,
                f"Not enough stock for {item.product.name}"
            )
            return redirect('cart_detail')

    if request.method == 'POST':
        customer, _ = Customer.objects.get_or_create(user=request.user)

        subtotal = sum(
            item.product.price * item.quantity
            for item in items
        )

        order = Order.objects.create(
    customer=request.user,   # ✅ User instance
    payment_method='cod',
    shipping_address=request.POST.get('shipping_address', ''),
    subtotal=subtotal,
    total_amount=subtotal
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
        'total': sum(item.product.price * item.quantity for item in items),
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user      # ✅ FIX
    )
    return render(request, 'order_success.html', {'order': order})



def order_history(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check what field name your Order model has
    # If it has 'customer' field, use that
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Calculate counts
    total_orders = orders.count()
    active_orders = orders.filter(status__in=['pending', 'processing', 'shipped']).count()
    delivered_orders = orders.filter(status='delivered').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)
    
    context = {
        'orders': orders_page,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
    }
    
    return render(request, 'order_history.html', context)

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
    # Fix: Use 'customer' instead of 'customer__user'
    orders = Order.objects.select_related('customer').order_by('-created_at')
    
    # Optional: Add filtering and pagination
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get status counts for filter
    status_counts = {}
    for status_choice in Order.ORDER_STATUS:
        status_counts[status_choice[0]] = Order.objects.filter(status=status_choice[0]).count()
    
    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_counts': status_counts,
    }
    
    return render(request, 'admin/order_list.html', context)

@staff_member_required
def admin_user_list(request):
    users = User.objects.annotate(
        order_count=Count('orders')
    ).order_by('-date_joined')

    context = {
        'users': users
    }
    return render(request, 'admin/user_list.html', context)

@staff_member_required
def admin_order_detail(request, order_id):
    # ✅ FIX: customer select_related করুন (user নয়)
    order = get_object_or_404(
        Order.objects.select_related('customer'), 
        id=order_id
    )
    
    # Order items নিন (OrderItem model থেকে)
    items = order.items.all()
    
    # Handle status update
    if request.method == "POST":
        if 'status' in request.POST:
            new_status = request.POST.get("status")
            old_status = order.status
            
            if new_status != old_status:
                order.status = new_status
                order.save(update_fields=["status", "updated_at"])
                
                messages.success(
                    request, 
                    f'Order status updated from {old_status} to {new_status}'
                )
                
                return redirect('admin_order_detail', order_id=order_id)
    
    # Calculate item totals
    item_subtotal = sum(item.total_price for item in items)
    item_count = items.count()
    
    # Timeline data
    timeline = [
        {
            'title': 'Order Placed',
            'description': 'Customer placed the order',
            'date': order.created_at,
            'completed': True
        },
        {
            'title': 'Payment Confirmed',
            'description': 'Payment was successfully processed',
            'date': order.payment_date if hasattr(order, 'payment_date') else None,
            'completed': True if order.payment_method == 'online' else False
        },
        {
            'title': 'Order Processed',
            'description': 'Order is being prepared for shipping',
            'date': None,
            'completed': order.status in ['processing', 'shipped', 'delivered']
        },
        {
            'title': 'Order Shipped',
            'description': 'Order has been shipped to customer',
            'date': order.shipped_date if hasattr(order, 'shipped_date') else None,
            'completed': order.status in ['shipped', 'delivered']
        },
        {
            'title': 'Order Delivered',
            'description': 'Order has been delivered to customer',
            'date': order.delivered_date if hasattr(order, 'delivered_date') else None,
            'completed': order.status == 'delivered'
        }
    ]
    
    context = {
        "order": order,
        "items": items,
        "item_subtotal": item_subtotal,
        "item_count": item_count,
        "timeline": timeline,
        "status_choices": Order.ORDER_STATUS,
        "payment_methods": Order.PAYMENT_METHODS,
    }
    
    return render(request, "admin/order_detail.html", context)
    
    
        



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
        #description = request.POST.get('description')
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
                #'description': description,
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



def all_categories(request):
    """View all categories page"""
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True  # Only top-level categories
    ).prefetch_related(
        models.Prefetch(
            'subcategories',
            queryset=SubCategory.objects.filter(is_active=True)
        )
    ).annotate(
        product_count=Count('products', filter=models.Q(products__is_active=True))
    ).order_by('order', 'name')
    
    # Get featured brands
    featured_brands = Brand.objects.filter(
        is_active=True,
        is_featured=True
    )[:12]
    
    # Get featured products
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('brand', 'category')[:8]
    
    context = {
        'categories': categories,
        'featured_brands': featured_brands,
        'featured_products': featured_products,
    }
    
    return render(request, 'categories/all_categories.html', context)

# ====================== FRONTEND VIEWS ======================

def category_products(request, slug):
    """View products by category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products in this category
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).select_related('brand', 'category', 'subcategory')
    
    # FIX: Get brands through products
    # Method 1: Get brand IDs from products
    brand_ids = products.values_list('brand_id', flat=True).distinct()
    brands = Brand.objects.filter(
        id__in=brand_ids,
        is_active=True
    )
    
    # Method 2: Direct query (more efficient)
    # brands = Brand.objects.filter(
    #     products__category=category,
    #     products__is_active=True,
    #     is_active=True
    # ).distinct()
    
    # Annotate with product count for this category
    from django.db.models import Count, Q
    brands = brands.annotate(
        product_count_in_category=Count(
            'products', 
            filter=Q(products__category=category, products__is_active=True)
        )
    ).order_by('-product_count_in_category')
    
    # Rest of your code remains the same...
    subcategories = SubCategory.objects.filter(
        category=category,
        is_active=True
    )
    
    # Filtering logic
    selected_brands = request.GET.getlist('brand')
    selected_subcategories = request.GET.getlist('subcategory')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('q', '')
    
    # Apply filters...
    # ... rest of your filtering code
    
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


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Check if already in wishlist
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to wishlist',
                'wishlist_count': Wishlist.objects.filter(user=request.user).count()
            })
        
        return redirect('wishlist')
    return redirect('product_detail', slug=product.slug)

@login_required
def remove_from_wishlist(request, item_id):
    if request.method == 'POST':
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        wishlist_item.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Item removed from wishlist',
                'wishlist_count': Wishlist.objects.filter(user=request.user).count()
            })
        
        return redirect('wishlist')
    return redirect('wishlist')

# Context processor to get wishlist count
def wishlist_count(request):
    if request.user.is_authenticated:
        return {'wishlist_count': Wishlist.objects.filter(user=request.user).count()}
    return {'wishlist_count': 0}
