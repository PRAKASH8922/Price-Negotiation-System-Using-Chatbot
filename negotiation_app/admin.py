from django.contrib import admin
from .models import Category, Product, NegotiationHistory, CartItem, Order, OrderItem

# Registering models with admin customization to make them clear and detailed

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_offer', 'min_negotiation_price')
    list_filter = ('category', 'is_offer')
    search_fields = ('name', 'description')

class NegotiationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'offered_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'product__name')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(NegotiationHistory, NegotiationHistoryAdmin)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
