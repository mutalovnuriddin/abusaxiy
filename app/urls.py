from django.urls import path
from .views import home_page, about_page, contact_page, product_page, product_search, product_detail, submit_review, toggle_review_like, login_view, register_view, logout_view, profile_view, cart_view, add_to_cart, remove_from_cart, decrease_cart, checkout_view, add_card_view, deposit_view, check_notifications


urlpatterns = [
    #Auth urls
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/<int:id>/', profile_view, name='profile'),

    #Main urls
    path('', home_page, name='home'),
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('product/', product_page, name='product'),
    path('product/search/', product_search, name='product_search'),
    path('product/<int:id>/', product_detail, name="product_detail"),
    path('product/<int:id>/review/', submit_review, name='submit_review'),
    path('review/<int:review_id>/like/', toggle_review_like, name='toggle_review_like'),
    path('api/check-notifications/', check_notifications, name='check_notifications'),

    #Cart urls
    path('cart/', cart_view, name="cart"),
    path('add-to-cart/<int:id>/', add_to_cart, name="add_to_cart"),
    path('remove-from-cart/<int:id>/', remove_from_cart, name="remove_from_cart"),
    path('decrease-cart/<int:id>/', decrease_cart, name="decrease_cart"),
    path('checkout/', checkout_view, name="checkout"),

    #Card urls
    path('add-card/', add_card_view, name="add_card"),
    path('deposit/', deposit_view, name='deposit')
]
