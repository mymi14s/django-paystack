import json, hmac, hashlib
from django.shortcuts import redirect, reverse
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.views.generic import RedirectView, TemplateView
# Create your views here.
from . import settings, signals, utils
from .signals import payment_verified
from .utils import load_lib
from .models import PaymentHistory


def verify_payment(request, order):
    amount = request.GET.get('amount')
    txrf = request.GET.get('trxref')
    PaystackAPI = load_lib()
    paystack_instance = PaystackAPI()
    response = paystack_instance.verify_payment(txrf, amount=int(amount))
    if response[0]:
        payment_verified.send(
            sender=PaystackAPI,
            ref=txrf,
            amount=int(amount) / 100,
            order=order)
        return redirect(
            reverse('paystack:successful_verification', args=[order]))
    return redirect(reverse('paystack:failed_verification', args=[order]))


class FailedView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        if settings.PAYSTACK_FAILED_URL == 'paystack:failed_page':
            return reverse(settings.PAYSTACK_FAILED_URL)
        return settings.PAYSTACK_FAILED_URL


def success_redirect_view(request, order_id):
    url = settings.PAYSTACK_SUCCESS_URL
    if url == 'paystack:success_page':
        url = reverse(url)
    return redirect(url, permanent=True)


def failure_redirect_view(request, order_id):
    url = settings.PAYSTACK_FAILED_URL
    if url == 'paystack:failed_page':
        url = reverse(url)
    return redirect(url, permanent=True)


class SuccessView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        if not settings.PAYSTACK_SUCCESS_URL:
            return reverse('paystack:success_page')
        return settings.PAYSTACK_SUCCESS_URL


# def webhook_view(request):
#     # ensure that all parameters are in the bytes representation
#     PaystackAPI = load_lib()
#     paystack_instance = PaystackAPI()
#     signature = request.META['HTTP_X_PAYSTACK_SIGNATURE']
#     paystack_instance.webhook_api.verify(
#         signature, request.body, full_auth=True)
#     # digest = utils.generate_digest(request.body)
#     # if digest == signature:
#     #     payload = json.loads(request.body)
#     #     signals.event_signal.send(
#     #         sender=request, event=payload['event'], data=payload['data'])
#     return JsonResponse({'status': "Success"})

# p_event, p_payment_date, p_reference, p_email, p_json_body = None, None, None, None, None
def payment_state():
    """ Keep patment information state. """
    p_event = None
    p_payment_date = None
    p_reference = None
    p_email = None
    p_json_body = None


def update_payment(json_body):
    """Update payment status based on data from json_body."""
    event = json_body['event']
    ndata = json_body['data']
    reference = ndata['reference']
    email = ndata['customer']['email']
    payment_date = ndata['paid_at']
    if event == 'charge.success':
        # status = 'paid'
        # payment_date = ndata['paid_at']
        # # payment_user = model.objects.filter(
        #             reference=reference).update(
        #             status=status, payment_date=payment_date
        #             )
        PaymentHistory.objects.create(
            email=email,
            reference=reference, data=json_body
        )


        payment_state.p_event = event
        payment_state.p_payment_date = payment_date
        payment_state.p_reference = reference
        payment_state.p_email = email
        payment_state.p_json_body = json_body

    else:
        # status = str(event.replace('charge.', ''))
        # payment_date = ndata['paid_at']
        # # payment_user = model.objects.filter(
        #     reference=reference).update(
        #     status=status, payment_date=payment_date
        #     )
        PaymentHistory.objects.create(
            email=email,
            reference=reference, data=json_body
        )
        payment_state.p_event = event
        payment_state.p_payment_date = payment_date
        payment_state.p_reference = reference
        payment_state.p_email = email
        payment_state.p_json_body = json_body

@require_POST
@csrf_exempt
def webhook_endpoint(request):
    """
    The function takes an http request object
    containing the json data from paystack webhook client.
    Django's http request and response object was used
    for this example.
    """
    paystack_sk = settings.PAYSTACK_SECRET_KEY# "sk_fromthepaystackguys"
    json_body = json.loads(request.body)
    computed_hmac = hmac.new(
        bytes(paystack_sk, 'utf-8'),
    str.encode(request.body.decode('utf-8')),
        digestmod=hashlib.sha512
        ).hexdigest()
    if 'HTTP_X_PAYSTACK_SIGNATURE' in request.META:
        if request.META['HTTP_X_PAYSTACK_SIGNATURE'] == computed_hmac:
            # print(request.META)

            update_payment(json_body) #
            payload = json_body
            signals.event_signal.send(
                sender=request, event=payload['event'], data=payload['data'])
            return HttpResponse(status=200)
    # Not successful
    update_payment(json_body)
    payload = json_body
    signals.event_signal.send(
        sender=request, event=payload['event'], data=payload['data'])
    # print('failed\n', json_body)
    return HttpResponse(status=400) #non 200

# event, payment_date, reference, json_body = update_payment
# print(event, payment_date, reference, json_body)
