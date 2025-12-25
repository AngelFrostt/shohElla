# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('register/', views.RegisterViewSet.as_view({'post': 'create'}), name='register'),
    path('login/', views.CustomAuthToken.as_view(), name='login'),
    
    path('cart/', views.CartViewSet.as_view({'get': 'list'}), name='cart'),
    path('cart/add/', views.CartViewSet.as_view({'post': 'add_item'}), name='cart-add'),
    path('cart/remove/', views.CartViewSet.as_view({'delete': 'remove_item'}), name='cart-remove'),
    
    path('test/', views.test_view, name='test'),
    
    path('', include(router.urls)),
]