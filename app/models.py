from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=14, blank=True, null=True)    
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", default="avatars/user.png", blank=True, null=True)

    def __str__(self):
        return self.username


class Card(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="card")
    card_number = models.CharField(max_length=16, verbose_name="Karta raqami")
    balance = models.FloatField(default=0.0, verbose_name="Balans ($)")

    def __str__(self):
        return f"{self.user.username} - {self.card_number} {self.balance}"


class DepositRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', "Kutilmoqda"),
        ('approved', "Tasdiqlandi"),
        ('rejected', "Rad etildi"),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.Case)
    amount = models.FloatField(verbose_name="To'ldirish summasi")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.get_status_display()})"


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField()
    img = models.URLField()
    views_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='one_review_per_user_product'),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='review_rating_1_to_5'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.title} - {self.user.username} ({self.rating}/5)'


class ReviewLike(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='review_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['review', 'user'], name='one_like_per_user_review'),
        ]



class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', "Kutilmoqda (Admin tasdiqlanishi kutilmoqda)"),
        ('approved', "Tasdiqlandi"),
        ('rejected', "Rad etildi"),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ordders")
    address = models.TextField(verbose_name="Yetkazib berish manzili")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqam")
    total_price = models.FloatField(verbose_name="Umumiy summa")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False, verbose_name="To'langan")

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    price = models.FloatField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Banner(models.Model):
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kichik Sarlavha")
    image = models.URLField()
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")

    def __str__(self):
        return self.title
    