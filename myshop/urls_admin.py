from django.urls import path
from . import views

#app_name = 'admin_dashboard'

urlpatterns = [
    
    # Category Management
    path('admin-dashboard/manage-categories/', views.manage_categories, name='manage_categories'),
    
    # Category CRUD URLs
    path('admin-dashboard/categories/add/', views.add_category, name='add_category'),
    path('admin-dashboard/categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('admin-dashboard/categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('admin-dashboard/categories/<int:pk>/toggle-status/', views.toggle_category_status, name='toggle_category_status'),
    
    # Subcategory CRUD URLs
    path('admin-dashboard/subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('admin-dashboard/subcategories/<int:pk>/edit/', views.edit_subcategory, name='edit_subcategory'),
    path('admin-dashboard/subcategories/<int:pk>/delete/', views.delete_subcategory, name='delete_subcategory'),
    path('admin-dashboard/subcategories/<int:pk>/toggle-status/', views.toggle_subcategory_status, name='toggle_subcategory_status'),
    
    # Brand CRUD URLs
    path('admin-dashboard/brands/add/', views.add_brand, name='add_brand'),
    path('admin-dashboard/brands/<int:pk>/edit/', views.edit_brand, name='edit_brand'),
    path('admin-dashboard/brands/<int:pk>/delete/', views.delete_brand, name='delete_brand'),
    path('admin-dashboard/brands/<int:pk>/toggle-status/', views.toggle_brand_status, name='toggle_brand_status'),



]
