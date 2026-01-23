from .models import Cart
from .models import Category, Brand, Product

def cart_context(request):
    cart_count = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = sum(item.quantity for item in cart.items.all())

    return {
        'cart_count': cart_count
    }




def navbar_data(request):
    return {
        "nav_categories": Category.objects.filter(is_active=True)
            .prefetch_related(
                'subcategories'
            ),
        "nav_brands": Brand.objects.filter(is_active=True),
    }