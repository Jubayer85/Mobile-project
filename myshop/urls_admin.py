from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path("manage-categories/", views.manage_categories, name="manage_categories"),

    path("category/<int:pk>/row/", views.category_row, name="category_row"),
    path("category/<int:pk>/edit/", views.category_edit_inline, name="category_edit"),
    path("category/<int:pk>/update/", views.category_update_inline, name="category_update"),
    path("category/<int:pk>/toggle/", views.category_toggle, name="category_toggle"),
    path("category/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
