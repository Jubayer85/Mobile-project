from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path("manage-categories/", views.manage_categories, name="manage_categories"),
   
    path("category/add/", views.add_category, name="add_category"),
    path("subcategory/add/", views.add_subcategory, name="add_subcategory"),
    path("brand/add/", views.add_brand, name="add_brand"),

    #path("category/list/", views.category_list, name="category_list"),
    #path("subcategory/list/", views.subcategory_list, name="subcategory_list"),
    #path("brand/list/", views.brand_list, name="brand_list"),
]
