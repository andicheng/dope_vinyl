from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from .models import Product, Genre, Artist, Admin, Order
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import stripe
###################################### USER ####################################################

def home(request):
    return render(request, "dope_vinyl/home.html")

def front_allproducts(request):
    cart = request.session.get('cart', {})
    length = sum(cart.values())
    try:
        sort=request.POST['sort']
    except:
        sort='title'
    if request.method == 'POST':
        products = Product.objects.filter(title__contains=request.POST['search_title'])
    else:
        products = Product.objects.all().order_by(sort)
    paginator = Paginator(products,15)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    genres = Genre.objects.all()
    context = {
        'products' : products,
        'genres' : genres,
        'sort_current' : sort,
        'length': length,
    }
    return render(request, "dope_vinyl/front_allproducts.html", context)

def front_allproducts_cat(request, id):
    cart = request.session.get('cart', {})
    length = sum(cart.values())
    try:
        sort=request.POST['sort']
    except:
        sort='title'
    products = Product.objects.filter(genre=id)
    paginator = Paginator(products,15)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    genres = Genre.objects.filter(id=id)
    context = {
        'products' : products,
        'genres' : genres,
    }
    return render(request, "dope_vinyl/front_allproducts.html", context)

def front_productpage(request, id):
    cart = request.session.get('cart', {})
    length = sum(cart.values())

    product = Product.objects.get(id=id)
    similar_products = Product.objects.filter(genre=product.genre).exclude(id=product.id)

    context = {
        'product': product,
        'similar_products': similar_products,
        'length': length,
        }
    return render(request, "dope_vinyl/front_productpage.html", context)

def buy(request, id):
    cart = request.session.get('cart', {})

    product = Product.objects.get(id=id)
    product_id = str(product.id)

    if product_id not in cart:
        cart[product_id] = 1
        messages.success(request, "Item added to the cart")

    else:
        cart[product_id] += 1
        messages.success(request, "Item added again... you must really like this dope vinyl.")
    request.session['cart'] = cart

    return redirect('product_page', id=product.id)

def carts(request):
    cart = request.session.get('cart', {})
    length = sum(cart.values())

    cart_list = []
    sum_total = 0

    for product_id, quantity in cart.items():
            the_product = Product.objects.get(id=int(product_id))
            the_price = quantity * the_product.price
            cart_list.append([the_product, quantity, the_price])
            sum_total += the_price

    context = {
        'length': length,
        'cart_list': cart_list,
        'total': sum_total,
    }
    return render(request, "dope_vinyl/front_shoppingcart.html", context)

def billing_shipping(request):
   stripe.api_key = "sk_test_MtYKfrdjHXRPAAuSul1W5m5B"
   token = request.POST['stripeToken']
   try:
     charge = stripe.Charge.create(
         amount=1000,
         currency="usd",
         source=token,
         description="Example charge"
     )
   except stripe.error.CardError as e:
     # The card has been declined
     pass

   return redirect('/dashboard/orders')

###################################### ADMIN ###################################################
def admin(request):
    return render(request, "dope_vinyl/adminlogin.html")

def adminlogin(request):
    if request.method == "POST":
        admin = Admin.objects.login(request.POST)

        if not admin:
            messages.error(request, "Invalid login credentials!")
        else:
            request.session['logged_admin'] = admin.id
            return redirect('/dashboard/orders')
    return redirect('/admin')

### we put one admin into the DB's Admin table.
###     The login is: dope.vinyl.admin@gmail.com (all lowercase)
###     The password is: dope (all lowercase)
def adminlogout(request):
    if 'logged_admin' in request.session:
        request.session.pop('logged_admin')
    return redirect('/admin')

############################################### DASHBOARD #######################################
#ALL ORDERS ON ADMIN PAGE.
def orders(request):
    if 'logged_admin' not in request.session:
        messages.error(request, "Gotta login bro.")
        return redirect('/adminlogin')
    context = {
        'admin': Admin.objects.get(id=request.session['logged_admin'])
    }

    return render(request, 'dope_vinyl/dashboard_allorders.html', context)


#INDIVIDUAL ORDER ON ADMIN PAGE.
def show_orders(request):
    if 'logged_admin' not in request.session:
        messages.error(request, "Gotta login bro")
        return redirect('/adminlogin')

    context = {
        'admin': Admin.objects.get(id=request.session['logged_admin'])
    }
    return render(request, 'dope_vinyl/dashboard_allorders.html', context)

#ALL PRODUCTS ON ADMIN PAGE. CLICK ON ADD NEW PRODUCT TO TAKE YOU TO ADD/EDIT ROUTE.

def products(request):
    if 'logged_admin' not in request.session:
        messages.error(request, "Gotta login bro")
        return redirect('/adminlogin')
    all_products = Product.objects.all().order_by('-id')
    all_genres = Genre.objects.filter()

    context = {
        "all_products": all_products,
        "all_genres": all_genres
    }
    return render(request, 'dope_vinyl/dashboard_allproducts.html', context)

def products_add(request):
    if request.method == "POST":
        if request.POST['genre_new'] != "":
            artist_name = Artist.objects.create(name=request.POST['artist'])
            genre_type = Genre.objects.create(genre_type=request.POST['genre_new'])
            Product.objects.create(artist=artist_name, title=request.POST['title'],description=request.POST['description'],genre=genre_type, price=request.POST['price'], inventory=request.POST['inventory'], image=request.FILES['image'])

        elif request.POST['genre'] != "":
            artist_name = Artist.objects.create(name=request.POST['artist'])
            genre_type = Genre.objects.get(genre_type=request.POST['genre'])
            Product.objects.create(artist=artist_name, title=request.POST['title'],description=request.POST['description'],genre=genre_type, price=request.POST['price'], inventory=request.POST['inventory'], image=request.FILES['image'])
    return redirect("/dashboard/products")


def products_edit(request, id):
    if request.method == "POST":
        if request.POST['genre_new'] != "":
            genre_type = request.POST['genre_new']
            Product.objects.filter(id=id).update(title=request.POST['title'],description=request.POST['description'], price=request.POST['price'], inventory=request.POST['inventory'])

        elif request.POST['genre'] != "":
            genre_type = request.POST['genre']
            Product.objects.filter(id=id).update(title=request.POST['title'],description=request.POST['description'], price=request.POST['price'], inventory=request.POST['inventory'])

    return redirect("products")

def products_delete(request, id):
    Product.objects.get(id=id).delete()
    return redirect("/dashboard/products")
