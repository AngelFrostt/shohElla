from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse

from .forms import RegisterForm, UserUpdateForm, PasswordChangeFormCustom
from api.models import Product, Category, Cart, CartItem, Order, OrderItem

def home_view(request):
    """Главная страница"""
    latest_products = Product.objects.all().order_by('-created_at')[:6]
    categories = Category.objects.all()
    return render(request, 'shop/index.html', {
        'latest_products': latest_products,
        'categories': categories,
    })

def products_view(request):
    """Страница всех товаров"""
    all_products = Product.objects.all()
    categories = Category.objects.all()
    
    category_id = request.GET.get('category')
    if category_id:
        all_products = all_products.filter(category_id=category_id)
    
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        all_products = all_products.order_by('price')
    elif sort == 'price_desc':
        all_products = all_products.order_by('-price')
    elif sort == 'new':
        all_products = all_products.order_by('-created_at')
    
    return render(request, 'shop/products.html', {
        'products': all_products,
        'categories': categories,
    })

def cart_view(request):
    """Страница корзины"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            total = sum(item.product.price * item.quantity for item in cart_items)
        except Cart.DoesNotExist:
            cart_items = []
            total = 0
    else:
        cart_items = []
        total = 0
    
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })

@login_required
def checkout_view(request):
    """Страница оформления заказа"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        if not cart_items:
            messages.warning(request, 'Ваша корзина пуста')
            return redirect('cart')
        
        total = sum(item.product.price * item.quantity for item in cart_items)
    except Cart.DoesNotExist:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart')
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        
        if not shipping_address:
            messages.error(request, 'Пожалуйста, укажите адрес доставки')
            return redirect('checkout')
        
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=total,
                    shipping_address=shipping_address,
                    status='pending'
                )
                
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                
                cart.items.all().delete()
                
                messages.success(request, f'Заказ #{order.id} успешно оформлен!')
                return redirect('profile')
        
        except Exception as e:
            messages.error(request, f'Произошла ошибка при оформлении заказа: {str(e)}')
            return redirect('checkout')
    
    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })

@login_required
def profile_view(request):
    """Страница личного кабинета"""
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    user_form = UserUpdateForm(instance=user)
    password_form = PasswordChangeFormCustom(user)
    
    active_tab = request.GET.get('tab', 'orders')
    
    context = {
        'user': user,
        'orders': orders,
        'user_form': user_form,
        'password_form': password_form,
        'active_tab': active_tab,
    }
    
    return render(request, 'shop/profile.html', context)

@login_required
def update_profile_view(request):
    """Обновление данных пользователя"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Данные профиля успешно обновлены!')
        else:
            for error in user_form.errors.values():
                messages.error(request, error)
        
        return redirect(reverse('profile') + '?tab=profile')
    
    return redirect('profile')

@login_required
def change_password_view(request):
    """Изменение пароля"""
    if request.method == 'POST':
        password_form = PasswordChangeFormCustom(request.user, request.POST)
        
        if password_form.is_valid():
            user = request.user
            new_password = password_form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('home')
        else:
            for error in password_form.errors.values():
                messages.error(request, error)
        
        return redirect(reverse('profile') + '?tab=password')
    
    return redirect('profile')

@login_required
def update_cart_item_view(request, item_id):
    """Изменение количества товара в корзине"""
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f'Количество товара "{cart_item.product.name}" увеличено до {cart_item.quantity}')
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                    messages.success(request, f'Количество товара "{cart_item.product.name}" уменьшено до {cart_item.quantity}')
                else:
                    cart_item.delete()
                    messages.success(request, f'Товар "{cart_item.product.name}" удален из корзины')
            elif action == 'set':
                quantity = int(request.POST.get('quantity', 1))
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                    messages.success(request, f'Количество товара "{cart_item.product.name}" изменено на {quantity}')
                else:
                    cart_item.delete()
                    messages.success(request, f'Товар "{cart_item.product.name}" удален из корзины')
        
    except CartItem.DoesNotExist:
        messages.error(request, 'Товар не найден в корзине')
    
    return redirect('cart')


@login_required
def remove_from_cart_view(request, item_id):
    """Удаление товара из корзины"""
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'Товар "{product_name}" удален из корзины')
    except CartItem.DoesNotExist:
        messages.error(request, 'Товар не найден в корзине')
    
    return redirect('cart')


@login_required
def clear_cart_view(request):
    """Очистка всей корзины"""
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            messages.success(request, 'Корзина очищена')
        except Cart.DoesNotExist:
            messages.info(request, 'Корзина уже пуста')
    
    return redirect('cart')


@login_required
def order_detail_view(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })

def login_view(request):
    """Страница входа"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'shop/login.html')

def register_view(request):
    """Страница регистрации"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'shop/register.html', {'form': form})

def logout_view(request):
    """Выход из системы"""
    auth_logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')

def about_view(request):
    """Страница "О нас" """
    return render(request, 'shop/about.html')

def contacts_view(request):
    """Страница "Контакты" """
    return render(request, 'shop/contacts.html')

@login_required
def add_to_cart_view(request, product_id):
    """Добавление товара в корзину"""
    try:
        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'Товар "{product.name}" добавлен в корзину!')
    except Product.DoesNotExist:
        messages.error(request, 'Товар не найден!')
    
    return redirect('products')