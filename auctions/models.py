from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class User(AbstractUser):
    pass

class Category(models.Model):
    category = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.category

class AuctionSession(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=[('scheduled', 'Scheduled'), ('open', 'Open'), ('closed', 'Closed')], default='scheduled')

    def __str__(self):
        return f"Auction session from {self.start_time} to {self.end_time}"

class Product(models.Model):
    title = models.CharField(max_length=64)
    desc = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    image_url = models.CharField(max_length=228, blank=True, null=True)
    sold_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    active_bool = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('withdrawn', 'Withdrawn'), ('sold', 'Sold')], default='pending')

    def __str__(self):
        return self.title

class AuctionProduct(models.Model):
    auction = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, related_name='auction_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='auction_products')
    start_bid = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('auction', 'product')

    def __str__(self):
        return f"{self.product.title} in Auction {self.auction.id}"

class Bid(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='Bid')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Bid')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(default=timezone.now)
    response_deadline = models.DateTimeField(null=True, blank=True)
    bid_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Bid of {self.bid_amount} by {self.buyer.username} on {self.product.title}"

class Transaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_transactions')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    auction_session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE)
    status_info = models.CharField(max_length=10, choices=[('PENDING', 'Pending'), ('WITHDRAWN', 'Withdrawn'), ('SOLD', 'Sold')], default='PENDING')

    def __str__(self):
        return f"Transaction for {self.product.title}"


class comments(models.Model):
    listingid = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.product.title}"

class watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_list')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='watchlist_items')

    def __str__(self):
        return f"{self.user.username}'s watchlist item: {self.product.title}"


class winner(models.Model):
    bid_win_list = models.ForeignKey(Product, on_delete = models.CASCADE)
    user = models.CharField(max_length=64, default = None)

class payments(models.Model):
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    paid = models.BooleanField(default=False)