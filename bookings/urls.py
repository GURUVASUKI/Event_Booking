from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('events/', views.event_list, name='event_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/<str:ticket_id>/', views.verify_ticket, name='verify_ticket'),
    path('scan-qr/', views.qr_scanner, name='qr_scanner'),
    path('book/<int:event_id>/', views.book_ticket, name='book_ticket'),
    path('payment/<int:booking_id>/', views.payment, name='payment'),
    path('success/<int:booking_id>/', views.success_page, name='success_page'),
    
    
]