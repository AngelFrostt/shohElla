# accounts/views.py - СОХРАНИТЕ ЭТОТ КОД В БЛОКНОТЕ с кодировкой UTF-8
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from api.models import Product, Cart, CartItem

# Регистрация
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# Вход
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

# Выход
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')

# Профиль
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

# Корзина
@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'accounts/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total': total
    })

# Добавить в корзину
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} добавлен в корзину!')
    return redirect('home')

# Обновить корзину
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        elif action == 'delete':
            cart_item.delete()
            messages.info(request, 'Товар удален из корзины')
            return redirect('cart')
    
    return redirect('cart')

# Очистить корзину
@login_required
def clear_cart(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        messages.info(request, 'Корзина очищена')
    
    return redirect('cart')

# Create your views here.
