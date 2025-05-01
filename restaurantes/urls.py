from django.urls import path
from . import views

urlpatterns = [
    path('mis/', views.mis_restaurantes, name='mis_restaurantes'),
    path('crear-payment-intent-restaurante/', views.crear_payment_intent_restaurante, name='crear_payment_intent_restaurante'),
]
