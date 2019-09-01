from django.shortcuts import render
from django.views.generic import TemplateView

# Paystack state
from paystack.views import payment_state

# Create your views here.

class PayOrder(TemplateView):
    """ Test payment view."""
    template_name = 'store/payorder.html'


class PaymentSuccess(TemplateView):
    """Land here on successful payment verification."""

    template_name = 'paystack/success-page.html'


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        state = [payment_state.p_event, payment_state.p_payment_date, payment_state.p_reference, payment_state.p_email, payment_state.p_json_body]
        context['paystate'] = state
        # print(payment_state.p_event, payment_state.p_payment_date, payment_state.p_reference, payment_state.p_email, payment_state.p_json_body)
        return context
