from django.urls import path
from . import views

urlpatterns = [
    # Customer facing paths
    path('', views.home_view, name='home'),
    path('search/', views.search_view, name='search'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('negotiate/<int:pk>/', views.negotiate_price_view, name='negotiate_price'),
    
    # Auth paths
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Shopping cart paths
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:pk>/', views.cart_update_view, name='cart_update'),
    path('cart/delete/<int:pk>/', views.cart_delete_view, name='cart_delete'),
    
    # Checkout & Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.order_history_view, name='order_history'),
    
    # Custom admin dashboard paths
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/product/add/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/product/edit/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/product/delete/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/category/add/', views.admin_category_add, name='admin_category_add'),
    path('admin-panel/category/edit/<int:pk>/', views.admin_category_edit, name='admin_category_edit'),
    path('admin-panel/category/delete/<int:pk>/', views.admin_category_delete, name='admin_category_delete'),
    path('admin-panel/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin-panel/negotiations/', views.admin_negotiations_view, name='admin_negotiations'),
]
