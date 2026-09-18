import requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F
from django.http import JsonResponse


from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import Product, Banner, CustomUser, OrderItem, Order, Card, DepositRequest, Notification, Review, ReviewLike

# Create your views here.

#Auth view

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz")
            return redirect('home')

    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})



def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Xush kelibsiz {user.username}!")
                return redirect('home')
        else:
            messages.error(request, "Login yoki Parol noto'g'ri")

    else:
        form = LoginForm()
    return render(request, 'login.html', {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz")
    return redirect('login')


#home viwe


def home_page(request):
    banner = Banner.objects.filter(is_active=True)
    products = Product.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True),
    ).order_by('-id')[:3]

    context = {
        'products': products,
        'banners': banner
    }
    
    return render(request, 'index.html', context)


def about_page(request):
    return render(request, 'about.html')


def contact_page(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not name or not email or not message_text:
            messages.error(request, 'Iltimos, barcha maydonlarni to‘ldiring.')
            return redirect('contact')

        TOKEN = settings.TELEGRAM_BOT_TOKEN
        CHAT_ID = settings.TELEGRAM_CHAT_ID

        if not TOKEN or not CHAT_ID:
            messages.error(request, 'Xabar xizmati hozircha sozlanmagan.')
            return redirect('contact')

        text = (
            f'📩 **Yangi xabar!**\n\n'
            f'👤 **Ism:** {name}\n'
            f'📧 **Email:** {email}\n'
            f'💬 **Xabar:** {message_text}'
        )

        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown',
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.ok:
                messages.success(request, 'Xabaringiz yuborildi! Tez orada siz bilan bog‘lanamiz.')
            else:
                messages.error(request, 'Xabarni yuborishda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.')
        except requests.exceptions.RequestException as e:
            print(f'Xatolik yuz berdi: {e}')
            messages.error(request, 'Xabarni yuborishda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.')

        return redirect('contact')

    return render(request, 'contact.html')


def product_page(request):
    product_list = Product.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True),
    ).order_by('-id')
    pagination = Paginator(product_list, 6)

    page_number = request.GET.get('page')

    try:
        products = pagination.get_page(page_number)
    except PageNotAnInteger:
        products = pagination.get_page(1)
    except EmptyPage:
        products = pagination.get_page(pagination.num_pages)

    context = {
        'products': products
    }

    return render(request, 'products.html', context)


def product_search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(title__icontains=query).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True),
    ).order_by('-id')[:30]

    return JsonResponse({
        'products': [
            {
                'id': product.id,
                'title': product.title,
                'price': product.price,
                'description': product.description,
                'img': product.img,
                'views_count': product.views_count,
                'avg_rating': product.avg_rating or 0,
                'review_count': product.review_count,
            }
            for product in products
        ]
    })



def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    session_key = f'viwed_product_{product.id}'

    if not request.session.get(session_key, False):
        Product.objects.filter(id=id).update(views_count=F('views_count') + 1)

        request.session[session_key] = True

        product.refresh_from_db()

    reviews = Review.objects.filter(product=product).select_related('user').annotate(
        like_count=Count('likes')
    )
    review_summary = reviews.aggregate(average=Avg('rating'), count=Count('id'))
    can_review = request.user.is_authenticated and OrderItem.objects.filter(
        order__user=request.user,
        order__status='approved',
        order__is_paid=True,
        product=product,
    ).exists()
    user_review = reviews.filter(user=request.user).first() if request.user.is_authenticated else None
    liked_review_ids = set(ReviewLike.objects.filter(
        user=request.user,
        review__product=product,
    ).values_list('review_id', flat=True)) if request.user.is_authenticated else set()
    related_products = Product.objects.exclude(id=id).order_by('-id')[:3]
    
    context = {
        'product': product,
        'related_products': related_products
        , 'reviews': reviews
        , 'average_rating': review_summary['average'] or 0
        , 'review_count': review_summary['count']
        , 'can_review': can_review
        , 'user_review': user_review
        , 'liked_review_ids': liked_review_ids
    }

    return render(request, 'product_detail.html', context)


@login_required
def submit_review(request, id):
    if request.method != 'POST':
        return redirect('product_detail', id=id)

    product = get_object_or_404(Product, id=id)
    eligible = OrderItem.objects.filter(
        order__user=request.user,
        order__status='approved',
        order__is_paid=True,
        product=product,
    ).exists()
    if not eligible:
        messages.error(request, 'Sharh qoldirish uchun avval ushbu mahsulotni sotib olishingiz kerak.')
        return redirect('product_detail', id=id)

    try:
        rating = int(request.POST.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0

    if rating not in range(1, 6):
        messages.error(request, 'Iltimos, 1 dan 5 gacha baho tanlang.')
        return redirect('product_detail', id=id)

    Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={'rating': rating, 'comment': request.POST.get('comment', '').strip()},
    )
    messages.success(request, 'Rahmat, sharhingiz qabul qilindi!')
    return redirect('product_detail', id=id)


@login_required
def toggle_review_like(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        like, created = ReviewLike.objects.get_or_create(review=review, user=request.user)
        if not created:
            like.delete()
    return redirect('product_detail', id=review.product_id)




def add_to_cart(request, id):
    cart = request.session.get('cart', {})
    product_id_str = str(id)
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')



def decrease_cart(request, id):
    cart = request.session.get('cart', {})
    product_id_str = str(id)
    if product_id_str in cart:
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        else:
            del cart[product_id_str]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')


def remove_from_cart(request, id):
    cart = request.session.get('cart', {})
    product_id_str = str(id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_quantity = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()
        if product:
            item_total = product.price * quantity
            total_price += item_total
            total_quantity += quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })

    cart_product_ids = [int(pid) for pid in cart.keys()]
    recommended_products = Product.objects.exclude(id__in=cart_product_ids).order_by('-id')[:4]

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity,
        'recommended_products': recommended_products
    }
    return render(request, 'cart.html', context)


@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')

    if not hasattr(request.user, 'card'):
        messages.warning(request, "Xarid qilish uchun avval profilingizda karta qo'shing!")
        return redirect('profile', id=request.user.id)

    user_card = request.user.card
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()
        if product:
            item_total = product.price * quantity
            total_price += item_total
            cart_items.append({'product': product, 'quantity': quantity, 'item_total': item_total})

    if user_card.balance < total_price:
        messages.error(request, f"Hisobingizda pul yetarli emas! Balans: ${user_card.balance}. Kerakli summa: ${total_price}.")
        return redirect('profile', id=request.user.id)

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        # Buyurtma kutilmoqda (pending) holatida yaratiladi
        order = Order.objects.create(
            user=request.user,
            address=address,
            phone=phone,
            total_price=total_price,
            status='pending',
            is_paid=False
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['product'].price,
                quantity=item['quantity']
            )

        request.session['cart'] = {}
        request.session.modified = True

        return render(request, 'order_success.html', {'order': order})

    context = {'cart_items': cart_items, 'total_price': total_price}
    return render(request, 'checkout.html', context)


@login_required
def add_card_view(request):
    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        card, created = Card.objects.get_or_create(user=request.user)
        card.card_number = card_number
        card.save()
        messages.success(request, "Karta muvaffaqiyatli qo'shildi")

    return redirect('profile', id=request.user.id)


@login_required
def deposit_view(request):

    if request.method == "POST":
        amount = float(request.POST.get('amount', 0))
        if amount > 0:
            DepositRequest.objects.create(user=request.user, amount=amount)
            messages.info(request, "Balansni to'ldirish so'rovi adminga yuborildi. Tasdiqlashni kuting!")

    return redirect('profile', id=request.user.id)



@login_required
def profile_view(request, id):
    user = get_object_or_404(CustomUser, id=id)
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if request.user.id != user.id:
        return redirect('profile', id=request.user.id)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile', id=user.id)
    else:
        form = ProfileUpdateForm(instance=user)

    context = {
        'form': form,
        'user': user,
        'orders': user_orders
    }

    return render(request, 'profile.html', context)


@login_required
def check_notifications(request):
    unread_notification = Notification.objects.filter(user=request.user, is_read=False)

    data = []
    for notif in unread_notification:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'created_at': notif.created_at.strftime("%H:%M")
        })

        notif.is_read = True
        notif.save()

    return JsonResponse({'notifications': data})