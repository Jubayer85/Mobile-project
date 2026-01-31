from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    
    path('admin-dashboard/manage-categories/', views.manage_categories, name='manage_categories'),
   # Category URLs
    path('admin-dashboard/add/', views.add_category, name='add_category'),
    path('admin-dashboard/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('admin-dashboard/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('admin-dashboard/categories/<int:pk>/toggle-status/', views.toggle_category_status, name='toggle_category_status'),
    
    # Subcategory URLs
    path('admin-dashboard/add/', views.add_subcategory, name='add_subcategory'),
    path('admin-dashboard/<int:pk>/edit/', views.edit_subcategory, name='edit_subcategory'),
    path('admin-dashboard/<int:pk>/delete/', views.delete_subcategory, name='delete_subcategory'),
    path('admin-dashboard/<int:pk>/toggle-status/', views.toggle_subcategory_status, name='toggle_subcategory_status'),
    
    # Brand URLs
    path('admin-dashboard/add/', views.add_brand, name='add_brand'),
    path('admin-dashboard/<int:pk>/edit/', views.edit_brand, name='edit_brand'),
    path('admin-dashboard/<int:pk>/delete/', views.delete_brand, name='delete_brand'),
    path('admin-dashboard/<int:pk>/toggle-status/', views.toggle_brand_status, name='toggle_brand_status'),





    #path("category/add/", views.add_category, name="add_category"),
    #path("subcategory/add/", views.add_subcategory, name="add_subcategory"),
    #path("brand/add/", views.add_brand, name="add_brand"),
    #path('admin-dashboard/<int:pk>/delete/', views.delete_category, name='delete_category'),

    #path("category/list/", views.category_list, name="category_list"),
    #path("subcategory/list/", views.subcategory_list, name="subcategory_list"),
    #path("brand/list/", views.brand_list, name="brand_list"),
]
