from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from decimal import Decimal
import json

from .models import Category, Product, NegotiationHistory, CartItem, Order, OrderItem

# Helper function to check if the logged-in user is an admin/staff member
def is_admin(user):
    return user.is_authenticated and user.is_staff

# ==========================================
# 1. CUSTOMER AUTHENTICATION VIEWS
# ==========================================

# User Registration View
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the form errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# User Login View
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                # Redirect admins directly to custom admin panel
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('home')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# User Logout View
def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out successfully.")
    return redirect('home')


# ==========================================
# 2. CATALOGUE & SEARCH VIEWS
# ==========================================

# Home Page: List Products and Categories
def home_view(request):
    categories = Category.objects.all()
    selected_category_id = request.GET.get('category')
    
    # Filter by category if requested
    if selected_category_id:
        selected_category = get_object_or_404(Category, id=selected_category_id)
        products = Product.objects.filter(category=selected_category)
    else:
        products = Product.objects.all()
        selected_category = None
        
    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
    }
    return render(request, 'home.html', context)

# Product Search View
def search_view(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        products = Product.objects.all()
        
    context = {
        'products': products,
        'query': query,
        'categories': categories,
    }
    return render(request, 'home.html', context)

# Product Details View with Chatbot Interface
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Check if this user has already negotiated a price for this product in their current session
    negotiated_price_key = f"negotiated_price_{product.id}"
    negotiated_price = request.session.get(negotiated_price_key, None)
    
    context = {
        'product': product,
        'negotiated_price': negotiated_price,
    }
    return render(request, 'product_detail.html', context)


# ==========================================
# 3. CHATBOT NEGOTIATION VIEW (AJAX ENDPOINT)
# ==========================================

def negotiate_price_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'fail', 'message': 'Only POST method is allowed.'}, status=400)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'fail',
            'message': 'Hello there! Please Log In first before we start negotiating prices. Thank you!'
        })

    product = get_object_or_404(Product, pk=pk)
    
    try:
        data = json.loads(request.body)
        user_offer = Decimal(str(data.get('offer', 0)))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'status': 'fail', 'message': 'Invalid offer format.'}, status=400)

    # Rule 1: Offer products cannot be negotiated.
    if product.is_offer:
        response_text = f"Sorry, the product '{product.name}' is already on a promotional discount offer. The price of ${product.price} is fixed and cannot be negotiated further."
        
        # Log negotiation attempt in database
        NegotiationHistory.objects.create(
            user=request.user,
            product=product,
            offered_price=user_offer,
            status='Rejected',
            bot_response=response_text
        )
        return JsonResponse({
            'status': 'fail',
            'message': response_text
        })

    # Rule 2: Minimum negotiation price comparison.
    min_price = product.min_negotiation_price
    
    # Offer is accepted
    if user_offer >= min_price:
        # Validate that the offer isn't unreasonably higher than original price (just check if it's accepted)
        effective_price = user_offer if user_offer < product.price else product.price
        
        response_text = f"Deal! I accept your offer of ${effective_price:.2f}. I have updated your buy button. You can add it to your cart at this negotiated price!"
        
        # Save in user's session so cart knows to use the discount
        request.session[f"negotiated_price_{product.id}"] = float(effective_price)
        
        # Log negotiation history
        NegotiationHistory.objects.create(
            user=request.user,
            product=product,
            offered_price=effective_price,
            status='Accepted',
            bot_response=response_text
        )
        return JsonResponse({
            'status': 'success',
            'message': response_text,
            'negotiated_price': f"{effective_price:.2f}"
        })
    
    # Offer is rejected
    else:
        # Counter-offer with the lowest acceptable price
        response_text = f"Sorry, your offer of ${user_offer:.2f} is too low. The absolute lowest price we can accept for this product is ${min_price:.2f}."
        
        # Log negotiation history
        NegotiationHistory.objects.create(
            user=request.user,
            product=product,
            offered_price=user_offer,
            status='Rejected',
            bot_response=response_text
        )
        return JsonResponse({
            'status': 'fail',
            'message': response_text
        })


# ==========================================
# 4. SHOPPING CART VIEWS
# ==========================================

# Display Cart Items
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Compute totals
    subtotal = sum(item.get_total_price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
    }
    return render(request, 'cart.html', context)

# Add to Cart View (handles regular or negotiated price)
@login_required
def cart_add_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Check if the user negotiated a price for this product
    session_key = f"negotiated_price_{product.id}"
    negotiated_price = request.session.get(session_key, None)
    
    # Retrieve or create a CartItem
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        
    # Apply negotiated price if it was stored in the session
    if negotiated_price is not None:
        cart_item.negotiated_price = Decimal(str(negotiated_price))
        # Clear negotiated price from session after adding to cart
        del request.session[session_key]
        
    cart_item.save()
    messages.success(request, f"'{product.name}' added to your cart!")
    
    # Handle instant checkout / Buy Now
    if request.GET.get('buy_now') == 'true':
        return redirect('cart')
        
    return redirect('home')

# Update Cart Item Quantity
@login_required
def cart_update_view(request, pk):
    cart_item = get_object_or_404(CartItem, id=pk, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated.")
    else:
        cart_item.delete()
        messages.info(request, "Item removed from cart.")
    return redirect('cart')

# Delete Cart Item
@login_required
def cart_delete_view(request, pk):
    cart_item = get_object_or_404(CartItem, id=pk, user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')


# ==========================================
# 5. CHECKOUT & ORDERS VIEWS
# ==========================================

# Checkout & Buy Now
@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('home')
        
    # Compute total
    total_amount = sum(item.get_total_price for item in cart_items)
    
    # Create the Order
    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        status='Ordered'
    )
    
    # Create the OrderItems
    for item in cart_items:
        # Determine the price at purchase (negotiated or normal)
        purchase_price = item.negotiated_price if item.negotiated_price is not None else item.product.price
        
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=purchase_price
        )
        
    # Empty the cart
    cart_items.delete()
    
    messages.success(request, f"Order placed successfully! Order ID: #{order.id}")
    return redirect('order_history')

# Customer Order History View
@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})


# ==========================================
# 6. CUSTOM ADMIN DASHBOARD VIEWS
# ==========================================

# Dashboard Summary
@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    products = Product.objects.all().order_by('-id')
    categories = Category.objects.all()
    orders_count = Order.objects.count()
    negotiations_count = NegotiationHistory.objects.count()
    
    context = {
        'products': products,
        'categories': categories,
        'orders_count': orders_count,
        'negotiations_count': negotiations_count,
    }
    return render(request, 'admin_dashboard.html', context)

# View All Client Orders
@user_passes_test(is_admin, login_url='login')
def admin_orders_view(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_orders.html', {'orders': orders})

# View All Chatbot Negotiations
@user_passes_test(is_admin, login_url='login')
def admin_negotiations_view(request):
    negotiations = NegotiationHistory.objects.all().order_by('-created_at')
    return render(request, 'admin_negotiations.html', {'negotiations': negotiations})

# Custom Admin Product: Add Product
@user_passes_test(is_admin, login_url='login')
def admin_product_add(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = Decimal(request.POST.get('price'))
        is_offer = request.POST.get('is_offer') == 'on'
        min_price = Decimal(request.POST.get('min_negotiation_price'))
        image_url = request.POST.get('image_url') or 'https://via.placeholder.com/300x200'

        Product.objects.create(
            category=category,
            name=name,
            description=description,
            price=price,
            is_offer=is_offer,
            min_negotiation_price=min_price,
            image_url=image_url
        )
        messages.success(request, f"Product '{name}' added successfully!")
        return redirect('admin_dashboard')
        
    return render(request, 'admin_product_form.html', {'categories': categories, 'action': 'Add'})

# Custom Admin Product: Edit Product
@user_passes_test(is_admin, login_url='login')
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = Decimal(request.POST.get('price'))
        product.is_offer = request.POST.get('is_offer') == 'on'
        product.min_negotiation_price = Decimal(request.POST.get('min_negotiation_price'))
        product.image_url = request.POST.get('image_url') or product.image_url

        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('admin_dashboard')
        
    return render(request, 'admin_product_form.html', {'product': product, 'categories': categories, 'action': 'Edit'})

# Custom Admin Product: Delete Product
@user_passes_test(is_admin, login_url='login')
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted successfully!")
    return redirect('admin_dashboard')

# Custom Admin Category: Manage Categories
@user_passes_test(is_admin, login_url='login')
def admin_categories(request):
    categories = Category.objects.all().order_by('-id')
    return render(request, 'admin_categories.html', {'categories': categories})

# Custom Admin Category: Add Category
@user_passes_test(is_admin, login_url='login')
def admin_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        Category.objects.create(name=name, description=description)
        messages.success(request, f"Category '{name}' created successfully!")
        return redirect('admin_categories')
        
    return render(request, 'admin_category_form.html', {'action': 'Add'})

# Custom Admin Category: Edit Category
@user_passes_test(is_admin, login_url='login')
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        messages.success(request, f"Category '{category.name}' updated successfully!")
        return redirect('admin_categories')
        
    return render(request, 'admin_category_form.html', {'category': category, 'action': 'Edit'})

# Custom Admin Category: Delete Category
@user_passes_test(is_admin, login_url='login')
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    messages.success(request, f"Category '{name}' deleted successfully!")
    return redirect('admin_categories')
