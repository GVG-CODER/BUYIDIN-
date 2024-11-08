from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("auctions/<int:bidid>", views.listingpage, name="listingpage"),
    path("watchlist/<str:username>/", views.watchlistpage, name = "watchlistpage"),
    path("added", views.addwatchlist, name = "addwatchlist"),
    path("delete", views.deletewatchlist, name = "deletewatchlist"),
    path("bidlist", views.bid, name="bid"),
    path("comments", views.allcomments, name="allcomments"),
    path("win_ner", views.win_ner, name="win_ner"),
    path("winnings", views.winnings, name="winnings"),
    path("categories/<int:category_id>/", views.categories_details, name="categories_details"),
    path("categorie", views.Category_list, name="cat"),
    path('sell_now/<int:product_id>/', views.sell_now, name='sell_now'),
    path("payment",views.payment, name="payment"),
    path("payment_status",views.payment_status, name="payment_status")
]

