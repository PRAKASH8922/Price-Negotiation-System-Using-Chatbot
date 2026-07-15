from django.db import models
from django.contrib.auth.models import User

# 1. Product Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# 2. Product Model
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # Normal retail price
    is_offer = models.BooleanField(default=False) # True if product is on promotional offer (non-negotiable)
    min_negotiation_price = models.DecimalField(max_digits=10, decimal_places=2) # Secret minimum price bot will accept
    image_url = models.CharField(max_length=500, default='https://via.placeholder.com/300x200') # Placeholder url for easy setup

    def __str__(self):
        return f"{self.name} (${self.price})"

# 3. Negotiation History Model (to save all chatbot negotiations)
class NegotiationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    offered_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Accepted', 'Accepted'), ('Rejected', 'Rejected')])
    bot_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - Offered: ${self.offered_price} ({self.status})"

# 4. Cart Item Model (stores cart items, including negotiated prices if applicable)
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Overridden price if bot accepted offer

    @property
    def get_total_price(self):
        # Use negotiated price if available, otherwise fallback to regular product price
        effective_price = self.negotiated_price if self.negotiated_price is not None else self.product.price
        return effective_price * self.quantity

    def __str__(self):
        price_str = f"${self.negotiated_price} (Negotiated)" if self.negotiated_price else f"${self.product.price}"
        return f"{self.user.username}'s Cart - {self.product.name} x {self.quantity} @ {price_str}"

# 5. Order Model (finalized checkout order)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Ordered')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"

# 6. Order Item Model (individual products inside an order)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # Saves the actual price purchased at (negotiated or normal)

    def __str__(self):
        return f"Order #{self.order.id} Item - {self.product.name} x {self.quantity}"
