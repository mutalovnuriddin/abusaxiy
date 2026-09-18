from django.urls import path

from .admin_views import (
    dashboard_view,
    deposit_list_view,
    deposit_status_view,
    order_detail_view,
    order_list_view,
    order_status_view,
    product_delete_view,
    product_form_view,
    product_list_view,
)


app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_view, name='home'),
    path('orders/', order_list_view, name='orders'),
    path('orders/<int:order_id>/', order_detail_view, name='order_detail'),
    path('orders/<int:order_id>/status/', order_status_view, name='order_status'),
    path('deposits/', deposit_list_view, name='deposits'),
    path('deposits/<int:deposit_id>/status/', deposit_status_view, name='deposit_status'),
    path('products/', product_list_view, name='products'),
    path('products/new/', product_form_view, name='product_new'),
    path('products/<int:product_id>/edit/', product_form_view, name='product_edit'),
    path('products/<int:product_id>/delete/', product_delete_view, name='product_delete'),
]