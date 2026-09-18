from django.contrib import admin
from .models import Product, Banner, CustomUser, Order, OrderItem, Card, DepositRequest, Notification, Review, ReviewLike
# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__title', 'user__username', 'comment']


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['user', 'card_number', 'balance']


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at']
    list_filter = ['status']

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'approved':
                card, created = Card.objects.get_or_create(user=obj.user, defaults={'card_number': '8600000000000000'})
                card.balance += obj.amount
                card.save()
                
                Notification.objects.create(
                    user=obj.user,
                    title="Balansingiz to'ldirildi! 💰",
                    message=f"Hisobingizga ${obj.amount} muvaffaqiyatli o'tkazildi."
                )
            elif obj.status == 'rejected':
                Notification.objects.create(
                    user=obj.user,
                    title="To'lov so'rovi rad etildi ❌",
                    message=f"${obj.amount} summasidagi to'lov so'rovingiz rad etildi."
                )
        super().save_model(request, obj, form, change)


class OrderItemLine(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone', 'total_price', 'status', 'is_paid', 'created_at']
    list_filter = ['status', 'is_paid']

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'approved':
                user_card = getattr(obj.user, 'card', None)
                if user_card and user_card.balance >= obj.total_price:
                    user_card.balance -= obj.total_price
                    user_card.save()
                    obj.is_paid = True
                    # Bildirishnoma yaratish
                    Notification.objects.create(
                        user=obj.user,
                        title="Buyurtmangiz tasdiqlandi! ✅",
                        message=f"#{obj.id} raqamli buyurtmangiz admin tomonidan tasdiqlandi. Hisobingizdan ${obj.total_price} yechildi."
                    )
            elif obj.status == 'rejected':
                Notification.objects.create(
                    user=obj.user,
                    title="Buyurtmangiz rad etildi ❌",
                    message=f"#{obj.id} raqamli buyurtmangiz admin tomonidan rad etildi."
                )
        super().save_model(request, obj, form, change)



