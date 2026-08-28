"""
Thin wrapper around the razorpay Python SDK.

In TEST MODE (keys starting with rzp_test_...), no real money moves — you can
simulate a successful or failed payment using Razorpay's test card numbers,
documented at https://razorpay.com/docs/payments/payments/test-card-upi-details/
"""
import razorpay
from django.conf import settings


def get_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount_rupees, receipt):
    """Amount must be sent to Razorpay in paise (smallest currency unit)."""
    client = get_client()
    amount_paise = int(round(amount_rupees * 100))
    return client.order.create({
        'amount': amount_paise,
        'currency': settings.CURRENCY,
        'receipt': receipt,
        'payment_capture': 1,  # auto-capture the payment once authorized
    })


def verify_payment_signature(params_dict):
    """Returns True if the signature Razorpay sent back is genuine.
    params_dict needs: razorpay_order_id, razorpay_payment_id, razorpay_signature
    """
    client = get_client()
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
