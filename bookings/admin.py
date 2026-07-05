from django.contrib import admin
from .models import Event, Ticket, Booking

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'price')
    list_filter = ('date',)
    search_fields = ('title', 'location')
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'description', 'date', 'location')}),
        ('Details', {'fields': ('image', 'price', 'time')}),
    )

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'customer_name', 'is_verified')
    readonly_fields = ('qr_code',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'tickets', 'booking_date')
    list_filter = ('booking_date', 'event')
    search_fields = ('user__username', 'event__title')
    readonly_fields = ('booking_date',)
    date_hierarchy = 'booking_date'

# Digital ID and access log admin registrations removed