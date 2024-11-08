from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PaymentForm



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
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        image_url = request.POST.get('image_url')
        category_id = request.POST.get('category')

        # Validate required fields
        if not title or not desc or not category_id:
            return render(request, 'auctions/create.html', {
                'error': 'Please fill in all required fields.',
                'categories': Category.objects.all()
            })

        # Validate starting_bid
        starting_bid = request.POST.get('starting_bid')
        try:
            starting_bid = float(starting_bid)
        except (ValueError, TypeError):
            return render(request, 'auctions/create.html', {
                'error': 'Starting bid must be a valid number.',
                'categories': Category.objects.all()
            })

        # Fetch the Category instance
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

        try:
            product.save()
            print("Product saved:", product.title)
            return redirect('index')
        except Exception as e:
            print("Error saving product:", e)
            return render(request, 'auctions/create.html', {
                'error': 'An error occurred while saving the product.',
                'categories': Category.objects.all()
            })

    categories = Category.objects.all()
    return render(request, 'auctions/create.html', {'categories': categories})




@login_required(login_url='login')
def listingpage(request, bidid):
    biddesc = get_object_or_404(Product, pk=bidid, active_bool='pending')

    auction_session, created = AuctionSession.objects.get_or_create(
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(days=1),
        defaults={'status': 'open'}
    )

    auction_product, auction_created = AuctionProduct.objects.get_or_create(
        auction=auction_session,
        product=biddesc,
        defaults={'start_bid': biddesc.starting_bid}
    )

    Bid_present = Bid.objects.filter(product=biddesc)
    current_bid = Bid_present.aggregate(models.Max('bid_amount'))['bid_amount__max'] or biddesc.starting_bid

    # Fetch comments related to the product
    product_comments = comments.objects.filter(listingid=biddesc)

    product_ids = [biddesc.id]
    return render(request, "auctions/listingpage.html", {
        "list": biddesc,
        "comments": product_comments,
        "present_bid": current_bid,
        "product_ids": product_ids
    })




@login_required(login_url='login')
def watchlistpage(request, username):
    user = get_object_or_404(User, username=username)
    list_ = watchlist.objects.filter(user = user)
    print(f"the list is {list_}")
    return render(request, "auctions/watchlist.html",{
        "user_watchlist" : list_,
        "user": user,
    })




@login_required(login_url='login')
def addwatchlist(request):
    nid = request.POST.get("listid")

    if not nid:
        messages.error(request, "List ID was not provided.")
        return redirect('listingpage', bidid=nid)
    existing_watchlist = watchlist.objects.filter(user=request.user)
    print(existing_watchlist)
    for item in existing_watchlist:
        if item.product.id == int(nid):
            messages.info(request, "This item is already in your watchlist.")
            return redirect('listingpage', bidid=nid)

    new_watchlist = watchlist(product=Product.objects.get(pk=nid), user=request.user)
    new_watchlist.save()

    messages.success(request, "Item added to watchlist.")

    return redirect('listingpage', bidid=nid)




@login_required(login_url='login')
def deletewatchlist(request):
    rm_id = request.GET["listid"]
    list_ = watchlist.objects.get(pk = rm_id)

    messages.success(request, f"{list_.product.title} is deleted from your watchlist.")
    list_.delete()

    return redirect("index")




# this function returns minimum bid required to place a user's bid
def minbid(min_bid, present_bid):
    for bid in present_bid:
        if min_bid < int(bid.bid_amount):
            min_bid = int(bid.bid_amount)
    return min_bid


@login_required(login_url='login')
def bid(request):
    if request.method == "POST":
        bid_amnt = request.POST.get("bid_amnt")
        list_id = request.POST.get("list_d")
        if bid_amnt is None or list_id is None:
            messages.error(request, "Bid amount and listing ID are required.")
            return redirect("index")
        Bid_present = Bid.objects.filter(product_id=list_id)
        startingbid = get_object_or_404(Product, pk=list_id)
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
    if request.method == "POST":
        comment_text = request.POST.get("comment")
        list_id = request.POST.get("listid")
        product = get_object_or_404(Product, id=list_id)

        new_comment = comments(user=request.user, comment=comment_text, listingid=product)

        new_comment.save()

        return redirect('listingpage', bidid=product.id)
    return redirect('listingpage', bidid=list_id)


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
from django.conf import settings
from .forms import PaymentForm
import razorpay
@login_required(login_url="login")
def payment(request):
    form = PaymentForm()
    payment_data = None

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            amount = int(form.cleaned_data.get("amount")) * 100

            # Create Razorpay client using credentials from settings
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

            # Attempt to create an order in Razorpay
            try:
                response_payment = client.order.create({"amount": amount, "currency": "INR"})
                order_id = response_payment['id']
                order_status = response_payment['status']

                if order_status == "created":
                    payment_instance = payments(
                        name=name,
                        amount=amount // 100,
                        order_id=order_id
                    )
                    payment_instance.save()

                    payment_data = response_payment
                    payment_data['name'] = name
                    payment_data['key'] = settings.RAZORPAY_KEY_ID

            except Exception as e:
                print(f"Error creating Razorpay order: {e}")

    return render(request, "auctions/payment.html", {"form": form, "payment": payment_data})




@login_required(login_url="login")
def payment_status(request):
    if request.method == "POST":
        response = request.POST

        if 'razorpay_order_id' in response and 'razorpay_payment_id' in response and 'razorpay_signature' in response:
            params_dict = {
                'razorpay_order_id': response['razorpay_order_id'],
                'razorpay_payment_id': response['razorpay_payment_id'],
                'razorpay_signature': response['razorpay_signature']
            }

            # Initializing Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

            try:
                # Verify the payment signature
                client.utility.verify_payment_signature(params_dict)

                # Retrieve the payment record from the database and update its status
                payment = get_object_or_404(payments, order_id=params_dict['razorpay_order_id'])
                payment.razorpay_payment_id = params_dict['razorpay_payment_id']
                payment.paid = True
                payment.save()

                # Render a success message on successful payment verification
                return render(request, "auctions/payment_status.html", {'status': True})

            except razorpay.errors.SignatureVerificationError:
                print("Error: Signature verification failed.")
                return render(request, "auctions/payment_status.html", {'status': False, 'error_message': 'Signature verification failed. Please try again.'})

            except Exception as e:
                print(f"Error occurred during payment processing: {e}")
                return render(request, "auctions/payment_status.html", {'status': False, 'error_message': 'An error occurred during payment processing. Please contact support.'})

        else:
            print("Error: Missing payment information in the callback response.")
            return render(request, "auctions/payment_status.html", {'status': False, 'error_message': 'Incomplete payment data received. Please try again.'})

    return render(request, "auctions/payment_status.html", {'status': False, 'error_message': 'Invalid request method.'})