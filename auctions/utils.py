from django.core.mail import send_mail
from .models import Bid

def send_notification(product):
    # obtaining highest bid
    highest_bid = Bid.objects.filter(product=product).order_by('-amount').first()
    if highest_bid:
        user = highest_bid.buyer
        message = f"Congratulations! You are the highest bidder for '{product.title}'. Please complete the payment to secure the item."
        # Send email notification
        send_mail(
            'Auction Notification - Highest Bidder',
            message,
            'buyidin.service@gmail.com',
            [user.email],
            fail_silently=False,
        )
        return True
    else:
        print("No bids found for this product.")
        return False