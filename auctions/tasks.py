from celery import shared_task #as a decorator
from django.utils import timezone
from datetime import timedelta
from .models import AuctionSession, Product, Bid
from .utils import send_notification  # Importing a utility function to handling notifications

@shared_task
def start_auction_session():
    start_time = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=2)
    AuctionSession.objects.create(start_time=start_time, end_time=end_time)

@shared_task
def end_auction_session():
    session = AuctionSession.objects.filter(end_time__lte=timezone.now()).last()
    if session:
        products = Product.objects.filter(auction_session=session, sold=False)
        for product in products:
            highest_bid = product.Bid.order_by('-amount').first()
            if highest_bid:
                product.highest_bidder = highest_bid.bidder
                product.save()
                highest_bid.response_deadline = timezone.now() + timedelta(minutes=15)
                highest_bid.save()
                notify_bidder(highest_bid.id)

@shared_task
def notify_bidder(bid_id):
    bid = Bid.objects.get(id=bid_id)
    send_notification(bid.bidder, f"Congratulations! You are the highest bidder for {bid.product.title}. Please confirm within 15 minutes.")
    check_response.apply_async((bid_id,), countdown=900)#checking response for 15 min.

@shared_task
def check_response(bid_id):
    bid = Bid.objects.get(id=bid_id)
    if bid and not bid.bid_accepted:
        # Offer product to next highest bidder if initial highest bidder hasn't responded.
        next_highest_bid = Bid.objects.filter(product=bid.product, bid_accepted=False).exclude(id=bid_id).order_by('-amount').first()
        if next_highest_bid:
            notify_bidder(next_highest_bid.id)
        else:
            bid.product.sold = True
            bid.product.save()