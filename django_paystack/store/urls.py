from django.urls import path
from .views import PayOrder, PaymentSuccess

app_name = 'store'

urlpatterns = [
    path('', PayOrder.as_view(), name='payorder'),
    path('pay_success/', PaymentSuccess.as_view(), name='paysuccess'),
]
