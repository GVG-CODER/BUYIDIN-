from django.contrib import admin
from .models import *

class auction(admin.ModelAdmin):
    list_display = ("id", "user", "active_bool", "title", "desc", "starting_bid", "image_url", "category")

class watchl(admin.ModelAdmin):
    list_display = ("id", "user")
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'product', 'bid_amount', 'bid_time', 'bid_accepted')

class comme(admin.ModelAdmin):
    list_display = ("id", "user", "comment", "listingid")

class win(admin.ModelAdmin):
    list_display = ("id", "user", "bid_win_list")

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category')


# Register your models here.
admin.site.register(Product, auction)
admin.site.register(Bid, BidAdmin)
admin.site.register(comments, comme)
admin.site.register(watchlist, watchl)
admin.site.register(winner, win)
admin.site.register(Transaction)
admin.site.register(AuctionProduct)
admin.site.register(payments)
admin.site.register(Category, CategoryAdmin)