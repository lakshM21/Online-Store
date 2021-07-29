from django.shortcuts import render, redirect
from django.http import HttpResponse
from . models import Product,Contact,Order,OrderUpdate
from math import ceil
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import json
from datetime import date
# from django.views.decorators.csrf import csrf_exempt
# from PayTm import Checksum
# MERCHANT_KEY ="kbzk1DSbJiV_03p5"

def index(request):

    allProds = []
    catprods = Product.objects.values('category','id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category = cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod,range(1,nSlides),nSlides])

    params = {'allProds':allProds }
    return render(request,'shop/index.html',params)

def searchMatch(query,item):
    '''RETURN TRUE ONLY QUERY MATCHES THE ITEM'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category','id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category = cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod)!=0:
            allProds.append([prod,range(1,nSlides),nSlides])
    params ={'allProds':allProds,'msg':"" }
    if len(allProds)==0 or len(query)<4:
        params = {'msg':"Please make sure to enter relevant search query "}
    return render(request,'shop/search.html',params)


def about(request):
    return render(request,'shop/about.html')

def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        thank= True
    return render(request,'shop/contact.html',{'thank':thank})

def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        print(orderId);
        email = request.POST.get('email', '')
        # return HttpResponse(f"{orderId} and {email}")
        try:
            order = Order.objects.filter(order_id=orderId,email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates =[]
                for item in update:
                    updates.append({'text':item.update_desc,'time':item.timestamp})
                    response = json.dumps({"status":"success","updates":updates,"itemsJson":order[0].items_json},default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request,'shop/tracker.html')



def productview(request,myid):
    # Fetch the product using id
    product = Product.objects.filter(id=myid)
    return render(request,'shop/prodview.html',{'product':product[0]})

def checkout(request):
    if request.method=="POST":
        items_json =  request.POST.get('itemsJson', '')
        print(items_json);
        name = request.POST.get('name', '')
        amount = request.POST.get('amount','')
        email = request.POST.get('email', '')
        address = request.POST.get('address1','') + " " + request.POST.get('address2','')
        city = request.POST.get('city','')
        state = request.POST.get('state','')
        zip_code = request.POST.get('zip_code','')
        phone = request.POST.get('phone', '')
        if(items_json != {}):
            order = Order(items_json=items_json,name=name,email=email,address=address,city=city,state=state,zip_code=zip_code,phone=phone,amount=amount,ordered_by=request.user)
            order.save()
            update = OrderUpdate(order_id = order.order_id ,update_desc="The order is placed")
            update.save()
            thank = True
            id = order.order_id 
            # param_dict = {
            #     'MID': 'WorldP64425807474247',
            #     'ORDER_ID': str(order.order_id),
            #     'TXN_AMOUNT': str(amount),
            #     'CUST_ID': 'email',
            #     'INDUSTRY_TYPE_ID': 'Retail',
            #     'WEBSITE': 'WEBSTAGING',
            #     'CHANNEL_ID': 'WEB',
            #     'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
                
            # }
            # param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
            return render(request,'shop/checkout.html',{'thank':thank,'id':id})
            #Request paytm to transfer the amount to your account after payment by user 
            # return render(request,'shop/paytm.html',{'param_dict': param_dict})
        else:
            params = { 'error': 'No Items in the Cart'}
            return render(request,'shop/checkout.html',params)
    params = { 'user': request.user }
    return render(request,'shop/checkout.html', params)

# @csrf_exempt
# def handlerequest(request):
#     # paytm will send you post request here
#     # return HttpResponse('done')
#     # pass
#     form = request.POST
#     response_dict = {}
#     for i in form.keys():
#         response_dict[i] = form[i]
#         if i == 'CHECKSUMHASH':
#             checksum = form[i]

#     verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
#     if verify:
#         if response_dict['RESPCODE'] == '01':
#             print('order successful')
#         else:
#             print('order was not successful because' + response_dict['RESPMSG'])
#     return render(request, 'shop/paymentstatus.html', {'response': response_dict})

def handleSignUp(request):
    if request.method == 'POST':
        #Get the parameters
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        #Check for erroneous inputs 
        if len(username) > 10:
            messages.error(request, "Username must be under 10 character")
            return redirect('ShopHome')
        if not username.isalnum():
            messages.error(request, "Username should only contain letters and numbers")
            return redirect('ShopHome')
        if pass1 != pass2:
            messages.error(request, "Password do not match")
            return redirect('ShopHome')

        #Create the users
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()
        messages.success(request, "Your Carting account has been successfully created")
        return redirect('ShopHome')

    else:
        return HttpResponse('404 - Not Allowed')

def HandleLogin(request):
    if request.method == 'POST':
        loginusername = request.POST['loginusername']
        loginpassword = request.POST['loginpassword']

        user = authenticate(username = loginusername,password = loginpassword)

        if user is not None:
            login(request, user)
            messages.success(request,'Successfully logged In')
            return redirect('ShopHome')

        else:
            messages.error(request,'Invalid credential, Please try again')
            return redirect('ShopHome')

    return HttpResponse('404 - Not Allowed')

def HandleLogout(request):
    logout(request)
    messages.success(request, 'Successfully logged Out')
    return redirect('ShopHome')

def your_products(request):

    products = [];
    print(request.user)
    products = Product.objects.filter(product_owner=request.user)
    params ={'uProds':products }
    return render(request, 'shop/your_products.html', params)

def your_orders(request):
    orders = [];
    orders = Order.objects.filter(ordered_by=request.user)
    
    p_orders = [v for v in orders];
    print(p_orders)    
    
    for i in range(len(p_orders)):
        p_orders[i].items_json = json.loads(p_orders[i].items_json)
        p_orders[i].items_json = list(p_orders[i].items_json)
        #p_orders[i].items_json['item_keys'] = list(p_orders[i].items_json)
        print(p_orders[i].items_json)
        print(type(p_orders[i].items_json))
        i = i+1
    # while(p_orders[i].items_json):
        
    #     
    #     if(not p_orders[i].items_json):
    #         break;
    #item1 = p_orders[0].items_json
    #print(item1.pr5)
    # if(i>0):
    #     i=0;
    params = { 'p_orders': p_orders } 
    return render(request, 'shop/your_orders.html', params)

def addProduct(request):
    if request.method == 'POST':
        pr_name = request.POST['pr_name']
        pr_category = request.POST['pr_category']
        pr_price = request.POST['pr_price']
        pr_desc = request.POST['pr_desc']
        pr_createDate = request.POST['pr_createDate']
        if(not pr_createDate):
            pr_createDate = date.today()
        pr_image = request.FILES['pr_image']
        print(pr_image)
        product = Product(product_name=pr_name, category=pr_category, price=pr_price, desc=pr_desc, pub_date=pr_createDate, image=pr_image,product_owner=request.user)
        product.save()
        messages.success(request, "New Product Added")
        return redirect('Your_Products')

def editProduct(request):
    if request.method == 'POST':
        pr_id = request.POST['pu_id']
        pr_name = request.POST['pu_name']
        pr_category = request.POST['pu_category']
        pr_price = request.POST['pu_price']
        pr_desc = request.POST['pu_desc']
        pr_createDate = request.POST['pu_createDate']
        if(not pr_createDate):
            pr_createDate = date.today()
        try:
            obj = Product.objects.get(pk=pr_id)
            obj.product_name = pr_name
            obj.category = pr_category
            obj.price = pr_price
            obj.desc = pr_desc
            obj.pub_date = pr_createDate
            obj.save()
        except Product.DoesNotExist:
            print("Product does not exists")
            messages.success(request, "Error Occures")

        messages.success(request, "Product Updated")
        return redirect('Your_Products')
