from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages




def index(request):
    active_products = Product.objects.filter(active_bool='pending')

    for product in active_products:
        #auction ends on the following Monday at 12:00 noon
        now = timezone.now()
        next_monday = now + timedelta((7 - now.weekday()) % 7)
        auction_end_time = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)

        # Calculate remaining time
        remaining_time = auction_end_time - now
        product.remaining_time = remaining_time

    return render(request, "auctions/index.html", {
        "a1": active_products,
    })




def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")




def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))




def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

from django.middleware.csrf import get_token




@login_required(login_url='login')
def create(request):
    if request.method == "POST":
        user = request.user
        token = get_token(request)  # Get the CSRF token for comparison
        print("CSRF Token:", token)

        # Get form fields
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        starting_bid = request.POST.get('starting_bid')
        image_url = request.POST.get('image_url')
        category_id = request.POST.get('category')

        # Ensure required fields are provided
        if not title or not desc or not starting_bid or not category_id:
            return render(request, 'auctions/create.html', {
                'error': 'Please fill in all required fields.',
                'categories': Category.objects.all()
            })

        # Try to fetch the Category instance
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return render(request, 'auctions/create.html', {
                'error': 'Selected category does not exist.',
                'categories': Category.objects.all()
            })
        # Create and save the Product instance
        product = Product(
            user=user,
            title=title,
            desc=desc,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category
        )
        product.save()
        print("Product saved:", product.title)
        return redirect('index')

    categories = Category.objects.all()
    return render(request, 'auctions/create.html', {'categories': categories})




@login_required(login_url='login')
def listingpage(request, bidid):
    # Fetch the product with 'pending' status by ID
    biddesc = get_object_or_404(Product, pk=bidid, active_bool='pending')

    # Fetch an active auction session
    auction_session, created = AuctionSession.objects.get_or_create(
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(days=1),  # Adjust end time as needed
        status='open'
    )

    # Ensure the product is added to AuctionProduct if not already there
    auction_product, auction_created = AuctionProduct.objects.get_or_create(
        auction=auction_session,
        product=biddesc,
        defaults={'start_bid': biddesc.starting_bid}
    )

    # Get all bids for the product and determine the highest bid or use starting bid
    Bid_present = Bid.objects.filter(product=biddesc)
    current_bid = Bid_present.aggregate(models.Max('bid_amount'))['bid_amount__max'] or biddesc.starting_bid

    return render(request, "auctions/listingpage.html", {
        "list": biddesc,
        "comments": biddesc.comments.all(),
        "present_bid": current_bid,
    })

@login_required(login_url='login')
def watchlistpage(request, username):
    list_ = watchlist.objects.filter(user = username)
    return render(request, "auctions/watchlist.html",{
        "user_watchlist" : list_,
    })




@login_required(login_url='login')
def addwatchlist(request):
    nid = request.GET["listid"]

    list_ = watchlist.objects.filter(user = request.user.username)

    for items in list_:
        if int(items.watch_list.id) == int(nid):
            return watchlistpage(request, request.user.username)

    newwatchlist = watchlist(watch_list = Product.objects.get(pk = nid), user = request.user.username)
    newwatchlist.save()

    messages.success(request, "Item added to watchlist")

    return listingpage(request, nid)




@login_required(login_url='login')
def deletewatchlist(request):
    rm_id = request.GET["listid"]
    list_ = watchlist.objects.get(pk = rm_id)

    messages.success(request, f"{list_.watch_list.title} is deleted from your watchlist.")
    list_.delete()

    return redirect("index")




# this function returns minimum bid required to place a user's bid
def minbid(min_bid, present_bid):
    for Bid_list in present_bid:
        if min_bid < int(Bid_list.bid):
            min_bid = int(Bid_list.bid)
    return min_bid




@login_required(login_url='login')
def bid(request):
    if request.method == "POST":
        bid_amnt = request.POST.get("bid_amnt")
        list_id = request.POST.get("list_d")
        if bid_amnt is None or list_id is None:
            messages.error(request, "Bid amount and listing ID are required.")
            return redirect("index")
        # Fetching existing bids for the product using the correct field
        Bid_present = Bid.objects.filter(product_id=list_id)
        startingbid = get_object_or_404(Product, pk=list_id)
        # Determine the minimum required bid
        min_req_bid = startingbid.starting_bid
        min_req_bid = minbid(min_req_bid, Bid_present)

        # Check if the bid amount is greater than the minimum required bid
        if int(bid_amnt) > int(min_req_bid):
            mybid = Bid(buyer=request.user, product=startingbid, bid_amount=bid_amnt)
            mybid.save()
            messages.success(request, "Bid Placed")
            return redirect("index")

        messages.warning(request, f"Sorry, {bid_amnt} is less. It should be more than {min_req_bid}$.")
    return redirect("listingpage", bidid=list_id)




@login_required(login_url='login')
def allcomments(request):
    comment = request.GET["comment"]
    username = request.user.username
    list_id = request.GET["listid"]
    new_comment = comments(user = username, comment = comment, listingid = list_id)
    new_comment.save()
    return listingpage(request, list_id)





@login_required(login_url='login')
def win_ner(request):
    bid_id = request.GET["listid"]
    Bid_present = Bid.objects.filter(listingid = bid_id)
    biddesc = Product.objects.get(pk = bid_id, active_bool = True)
    max_bid = minbid(biddesc.starting_bid, Bid_present)
    try:
        winner_object = Bid.objects.get(bid = max_bid, listingid = bid_id)
        winner_obj = Product.objects.get(id = bid_id)
        win = winner(bid_win_list = winner_obj, user = winner_object.user)
        winners_name = winner_object.user

    except:
        winner_obj = Product.objects.get(starting_bid = max_bid, id = bid_id)
        win = winner(bid_win_list = winner_obj, user = winner_obj.user)
        winners_name = winner_obj.user

    biddesc.active_bool = False
    biddesc.save()

    win.save()
    messages.success(request, f"{winners_name} won {win.bid_win_list.title}.")
    return redirect("index")




def winnings(request):
    try:
        your_win = winner.objects.filter(user = request.user.username)
    except:
        your_win = None

    return render(request, "auctions/winnings.html",{
        "user_winlist" : your_win,
    })




def Category_list(request):
    category_list = Category.objects.all()
    return render(request, "auctions/category.html", {"category_list": category_list})




def categories_details(request, category_id):
    # Fetch the category or return a 404 if not found
    category = get_object_or_404(Category, id=category_id)

    products = Product.objects.filter(category=category)

    context = {
        'category': category,
        'products': products,
        'error': None,
    }

    # Check if there are no products in the category
    if not products.exists():
        context['error'] = "No products found in this category."

    return render(request, 'auctions/categories_details.html', context)




@login_required(login_url='login')
def place_bid(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    bid_amount = request.GET.get('bid_amnt')

    if bid_amount:
        new_bid = Bid.objects.create(
            product=product,
            bidder=request.user,
            amount=bid_amount
        )
        return redirect('product_detail', product_id=product.id)
    return render(request, 'auctions/place_bid.html', {'product': product})

def confirm_bid(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    if request.user == bid.bidder:
        bid.bid_accepted = True
        bid.save()
    return redirect('product_detail', product_id=bid.product.id)





#function to handle selling the product
@login_required(login_url='login')
def sell_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Get the bids for the product, ordered by bid amount (highest first)
    bids = Bid.objects.filter(product=product).order_by('-bid_amount')

    if bids.exists():
        highest_bid = bids.first()# Get the highest bid
        product.active_bool = 'sold'
        product.sold_to = highest_bid.buyer
        product.save()

        # Create a payment record
        payment = payment(product=product, amount=highest_bid.bid_amount, buyer=highest_bid.buyer)
        payment.save()

        # Provide feedback to the user about the sale
        messages.success(request, f"Product sold to {highest_bid.buyer.username} for {highest_bid.bid_amount}$.")
        return redirect('payments')
    else:
        messages.warning(request, "No bids found for this product.")
        return redirect('index')





# payment
from . forms import PaymentForm
import razorpay

@login_required(login_url="login")
def payment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        amount = int(request.POST.get("amount"))*100

        #create razorpay client
        client = razorpay.Client(auth=('rzp_test_bgWyPGleNhovPs','VwdlUBiKUWk2BzVfE113gZRz'))

        #create order
        response_payment = client.order.create(dict(amount=amount,
                                                    currency = 'INR')
                                               )
        order_id = response_payment['id']
        order_status = response_payment['status']

        if order_status == "created":
            payment = payment(
                name=name,
                amount=amount,
                order_id=order_id
            )
            payment.save()
            response_payment['name']=name
            form = PaymentForm(request.POST or None)
            return render(request, "auctions/payment.html", {"form":form, "payment":response_payment})

    form = payment()
    return render(request, "auctions/payment.html", { 'form': form })




@login_required(login_url="login")
def payment_status(request):
    response = request.POST
    params_dict = {
        'razorpay_order_id': response['razorpay_order_id'],
        'razorpay_payment_id': response['razorpay_payment_id'],
        'razorpay_signature': response['razorpay_signature']
    }
    #client instance
    client = razorpay.Client(auth=('rzp_test_bgWyPGleNhovPs','VwdlUBiKUWk2BzVfE113gZRz'))
    try:
        status = client.utility.verify_payment_signature(params_dict)
        payment = payments.objects.get(order_id=response["razorpay_order_id"])
        payment.razorpay_payment_id = response["razorpay_payment_id"]
        payment.paid = True
        payment.save()
        return render(request, "auctions/payment_status.html", {'status':True})
    except:
        return render(request, 'payment_status.html',{'status':False})