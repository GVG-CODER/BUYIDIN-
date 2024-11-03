# auctions/management/commands/finalize_auctions.py

from django.core.management.base import BaseCommand
from auctions.models import *
from django.utils import timezone

class Command(BaseCommand):
    help = 'Finalize ended auctions and sell products to the highest bidders'

    def handle(self, *args, **kwargs):
        ended_auctions = AuctionSession.objects.filter(end_time__lt=timezone.now())
        for auction in ended_auctions:
            highest_bid = auction.highest_bid()
            if highest_bid:
                product = auction.product
                product.active_bool = 'sold'
                product.save()
                self.stdout.write(f"Product '{product.title}' sold to {highest_bid.buyer.username} for {highest_bid.bid_amount}.")
            auction.delete()
