from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.urls import path, include




urlpatterns = [
    # Public pages
    path('admin-dashboard/', include('myshop.urls_admin')),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login-redirect/', views.login_redirect, name='login_redirect'),
    path('profile/', views.profile, name='profile'),
    #path('apple-products/', views.apple_products, name='apple_products'),
    #path('brand/oppo/', views.oppo_products, name='oppo_products'),

    # User dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_history, name='order_history'),
    
   

    # Custom Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/products/', views.admin_product_list, name='admin_product_list'),
    path('admin-dashboard/add-product/', views.add_product, name='add_product'),
    path('admin-dashboard/edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('admin-dashboard/delete-product/<int:pk>/', views.delete_product, name='delete_product'),
    path('admin-dashboard/order_list/', views.admin_order_list, name='admin_order_list'),
    path('admin-dashboard/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-dashboard/user_list/', views.admin_user_list, name='admin_user_list'),
   # path('admin/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Product details
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_products, name='subcategory_products'),
    #path('subcategory/<slug:slug>/', views.subcategory_products, name='subcategory_products'),
    #path('brand/<slug:slug>/', views.brand_products, name='brand_products'),
    path('categories/', views.all_categories, name='all_categories'),
    path('admin-dashboard/toggle-product-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
     path('admin-dashboard/duplicate-product/<int:product_id>/', views.duplicate_product, name='duplicate_product'),


# PBrand URLs
    path('brands/', views.all_brands, name='admin_brand_list'),
    path('brands/<slug:slug>/', views.brand_products, name='brand_products'),
    path('brands/<slug:slug>/filter/', views.brand_products_filter, name='brand_products_filter'),
    
    # Product URLs
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
   # path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout and Orders
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    

    # wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # NEW: Footer required URLs
    path('shop/', views.shop_all, name='shop_all'),
    path('brands/', views.brand_list, name='brand_list'),
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('best-sellers/', views.best_sellers, name='best_sellers'),
    path('apple-products/', views.apple_products, name='apple_products'),
    path('gaming-phones/', views.gaming_phones, name='gaming_phones'),
    path('special-offers/', views.special_offers, name='special_offers'),
    path('contact/', views.contact_us, name='contact_us'),
    path('faq/', views.faq, name='faq'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('warranty-policy/', views.warranty_policy, name='warranty_policy'),
    path('track-order/', views.track_order, name='track_order'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

  


   

    # Sound equipment URLs (Fixed typo: equopment → equipment)
   # path("sound/sound-equipment/", views.sound_equipment, name="sound_equipment"),
    #path("sound/airpods/", views.airpods, name="airpods"),
    #path("sound/speakers/", views.speakers, name="speakers"),
   # path("sound/wireless-headphones/", views.wireless_headphones, name="wireless_headphones"),
    #path("sound/wired-headphones/", views.wired_headphones, name="wired_headphones"),

    # Phones URLs - Support both old and new names
   # path("phones/", views.phones, name="phones"),
    #path("phones/samsung/", views.samsung_phones, name="samsung"),  # Old name
    #path("phones/samsung-phones/", views.samsung_phones, name="samsung_phones"),  # New name
    #path("phones/iphone/", views.iphone_phones, name="iphone"),  # Old name
    #path("phones/iphone-phones/", views.iphone_phones, name="iphone_phones"),  # New name


    # Apple Products
   # path("apple/", views.apple_products_page, name="apple_products_page"),

    # Category based URLs (if needed separately)
    #path('category/samsung/', views.samsung_category, name='samsung_category'),
    #path('category/iphone/', views.iphone_category, name='iphone_category'),
]

# Media files (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)