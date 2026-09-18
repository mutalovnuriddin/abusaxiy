from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Card, CustomUser, DepositRequest, Notification, Order, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'img']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


@staff_member_required(login_url='/admin/login/')
def dashboard_view(request):
    order_totals = Order.objects.filter(status='approved').aggregate(total=Sum('total_price'))
    deposit_totals = DepositRequest.objects.filter(status='approved').aggregate(total=Sum('amount'))

    context = {
        'user_count': CustomUser.objects.filter(is_active=True, is_staff=False).count(),
        'product_count': Product.objects.count(),
        'order_count': Order.objects.count(),
        'pending_order_count': Order.objects.filter(status='pending').count(),
        'pending_deposit_count': DepositRequest.objects.filter(status='pending').count(),
        'approved_order_total': order_totals['total'] or 0,
        'approved_deposit_total': deposit_totals['total'] or 0,
        'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:6],
        'recent_deposits': DepositRequest.objects.select_related('user').order_by('-created_at')[:6],
        'popular_products': Product.objects.order_by('-views_count', '-id')[:5],
    }
    return render(request, 'dashboard/dashboard.html', context)


@staff_member_required(login_url='/admin/login/')
def order_list_view(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if search:
        orders = orders.filter(Q(user__username__icontains=search) | Q(phone__icontains=search))
    if status in {'pending', 'approved', 'rejected'}:
        orders = orders.filter(status=status)

    return render(request, 'dashboard/orders.html', {
        'orders': orders,
        'search': search,
        'selected_status': status,
    })


@staff_member_required(login_url='/admin/login/')
def order_detail_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product'),
        id=order_id,
    )
    return render(request, 'dashboard/order_detail.html', {'order': order})


@staff_member_required(login_url='/admin/login/')
@require_http_methods(['POST'])
def order_status_view(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update().select_related('user'), id=order_id)

        if order.status != 'pending':
            messages.warning(request, 'Bu buyurtma allaqachon ko‘rib chiqilgan.')
            return redirect('dashboard:order_detail', order_id=order.id)

        action = request.POST.get('action')
        if action == 'approve':
            card = Card.objects.select_for_update().filter(user=order.user).first()
            if not card or card.balance < order.total_price:
                messages.error(request, 'Foydalanuvchi balansida yetarli mablag‘ mavjud emas.')
                return redirect('dashboard:order_detail', order_id=order.id)

            card.balance -= order.total_price
            card.save(update_fields=['balance'])
            order.status = 'approved'
            order.is_paid = True
            order.save(update_fields=['status', 'is_paid'])
            Notification.objects.create(
                user=order.user,
                title='Buyurtmangiz tasdiqlandi!',
                message=f'#{order.id} raqamli buyurtmangiz tasdiqlandi. Hisobingizdan ${order.total_price} yechildi.',
            )
            messages.success(request, f'#{order.id} buyurtma tasdiqlandi.')
        elif action == 'reject':
            order.status = 'rejected'
            order.save(update_fields=['status'])
            Notification.objects.create(
                user=order.user,
                title='Buyurtmangiz rad etildi',
                message=f'#{order.id} raqamli buyurtmangiz admin tomonidan rad etildi.',
            )
            messages.success(request, f'#{order.id} buyurtma rad etildi.')
        else:
            messages.error(request, 'Noma’lum amal.')

    return redirect('dashboard:order_detail', order_id=order.id)


@staff_member_required(login_url='/admin/login/')
def deposit_list_view(request):
    deposits = DepositRequest.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if search:
        deposits = deposits.filter(Q(user__username__icontains=search))
    if status in {'pending', 'approved', 'rejected'}:
        deposits = deposits.filter(status=status)

    return render(request, 'dashboard/deposits.html', {
        'deposits': deposits,
        'search': search,
        'selected_status': status,
    })


@staff_member_required(login_url='/admin/login/')
@require_http_methods(['POST'])
def deposit_status_view(request, deposit_id):
    with transaction.atomic():
        deposit = get_object_or_404(
            DepositRequest.objects.select_for_update().select_related('user'),
            id=deposit_id,
        )

        if deposit.status != 'pending':
            messages.warning(request, 'Bu depozit so‘rovi allaqachon ko‘rib chiqilgan.')
            return redirect('dashboard:deposits')

        action = request.POST.get('action')
        if action == 'approve':
            card, created = Card.objects.select_for_update().get_or_create(
                user=deposit.user,
                defaults={'card_number': '8600000000000000'},
            )
            card.balance += deposit.amount
            card.save(update_fields=['balance'])
            deposit.status = 'approved'
            deposit.save(update_fields=['status'])
            Notification.objects.create(
                user=deposit.user,
                title='Balansingiz to‘ldirildi!',
                message=f'Hisobingizga ${deposit.amount} muvaffaqiyatli qo‘shildi.',
            )
            messages.success(request, f'${deposit.amount} depozit tasdiqlandi.')
        elif action == 'reject':
            deposit.status = 'rejected'
            deposit.save(update_fields=['status'])
            Notification.objects.create(
                user=deposit.user,
                title='Depozit so‘rovi rad etildi',
                message=f'${deposit.amount} summasidagi depozit so‘rovingiz rad etildi.',
            )
            messages.success(request, 'Depozit so‘rovi rad etildi.')
        else:
            messages.error(request, 'Noma’lum amal.')

    return redirect('dashboard:deposits')


@staff_member_required(login_url='/admin/login/')
def product_list_view(request):
    products = Product.objects.order_by('-id')
    search = request.GET.get('q', '').strip()
    if search:
        products = products.filter(title__icontains=search)
    return render(request, 'dashboard/products.html', {'products': products, 'search': search})


@staff_member_required(login_url='/admin/login/')
def product_form_view(request, product_id=None):
    product = get_object_or_404(Product, id=product_id) if product_id else None
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mahsulot muvaffaqiyatli saqlandi.')
        return redirect('dashboard:products')
    return render(request, 'dashboard/product_form.html', {'form': form, 'product': product})


@staff_member_required(login_url='/admin/login/')
@require_http_methods(['POST'])
def product_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Mahsulot o‘chirildi.')
    return redirect('dashboard:products')