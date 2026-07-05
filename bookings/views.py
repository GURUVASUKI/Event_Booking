from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Event, Ticket, Booking
from django.core.mail import send_mail
from django.conf import settings

import uuid
import logging
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def home(request):
    # Fetch 3 events for the attractive home hero section
    events = Event.objects.all().order_by('date')[:3]
    return render(request, 'bookings/index.html', {'events': events})

def about(request):
    return render(request, 'bookings/about.html')

def contact(request):
    return render(request, 'bookings/contact.html')

# def event_list(request):
#     events = Event.objects.all()
#     return render(request, 'bookings/event.html', {'events': events})

@login_required 
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # If the user submitted the form in book_event.html
    if request.method == 'POST':
        num_tickets = int(request.POST.get('num_tickets', 1))
        selected_seats = request.POST.get('selected_seats', '')
        
        # Create the booking record
        booking = Booking.objects.create(
            user=request.user,
            event=event,
            tickets=num_tickets
        )
        
        # Create individual ticket records for each ticket booked
        for i in range(num_tickets):
            ticket_id = f"{event.id}-{booking.id}-{i+1}-{uuid.uuid4().hex[:6]}"
            Ticket.objects.create(
                event=event,
                customer_name=request.user.first_name or request.user.username,
                ticket_id=ticket_id
            )
        
        # Store booking ID and selected seats in session for payment processing
        request.session['booking_id'] = booking.id
        request.session['selected_seats'] = selected_seats
        
        # Redirect to payment page
        return redirect('payment', booking_id=booking.id)
    
    # If GET request, show the booking form
    return render(request, 'bookings/book_event.html', {'event': event})


@login_required
def payment(request, booking_id):
    """Payment gateway page for processing bookings"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    event = booking.event
    selected_seats = request.session.get('selected_seats', '')
    
    # Ensure price is valid
    if not event.price or event.price == 0:
        messages.warning(request, 'Warning: Event price is not set. Please contact support.')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'stripe')
        
        # Calculate totals - ensure price is treated as float
        event_price = float(event.price) if event.price else 0.00
        subtotal = event_price * booking.tickets
        
        # Process payment based on method
        # Note: In production, integrate with actual payment gateway
        try:
            # Here you would integrate with actual payment gateway
            # For now, we'll simulate successful payment
            
            # Send confirmation email
            subject = f"Payment Confirmation - {event.title}"
            message = f"""
Hello {request.user.first_name or request.user.username},

Thank you for completing your payment!

Payment Details:
- Event: {event.title}
- Number of Tickets: {booking.tickets}
- Payment Method: {payment_method.capitalize()}
- Amount Paid: ${subtotal:.2f}
- Booking Reference: {booking.id}

Event Information:
- Date: {event.date.strftime('%B %d, %Y')}
- Time: {event.time.strftime('%I:%M %p') if event.time else 'TBD'}
- Location: {event.location}

Your tickets have been generated and sent to your email.

Best regards,
Event Booking Team
            """
            
            if request.user.email:
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email])
                except Exception as e:
                    logger.error(f"Payment confirmation email failed: {str(e)}")
            
            # Clear session data
            request.session.pop('booking_id', None)
            request.session.pop('selected_seats', None)
            
            messages.success(request, 'Payment successful! Your tickets have been sent to your email.')
            return redirect('success_page', booking_id=booking.id)
            
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            messages.error(request, 'Payment processing failed. Please try again.')
            return render(request, 'bookings/payment.html', {
                'booking': booking,
                'selected_seats': selected_seats,
                'ticket_subtotal': f"{subtotal:.2f}",
                'processing_fee': '0.00',
                'total_amount': f"{subtotal:.2f}"
            })
    
    # Calculate processing fee based on payment method
    event_price = float(event.price) if event.price else 0.00
    subtotal = event_price * booking.tickets
    processing_fee = round(subtotal * 0.029 + 0.30, 2)  # Default Stripe fee
    total_amount = round(subtotal + processing_fee, 2)
    
    context = {
        'booking': booking,
        'selected_seats': selected_seats,
        'ticket_subtotal': f"{subtotal:.2f}",
        'processing_fee': f"{processing_fee:.2f}",
        'total_amount': f"{total_amount:.2f}"
    }
    
    return render(request, 'bookings/payment.html', context)


@login_required
def success_page(request, booking_id):
    """Success page after payment completion"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    tickets = Ticket.objects.filter(event=booking.event)
    
    context = {
        'booking': booking,
        'event': booking.event,
        'tickets': tickets
    }
    
    return render(request, 'bookings/success.html', context)

    # If the user just clicked "Book Your Spot", show the confirmation/form page
    return render(request, 'bookings/book_event.html', {'event': event})

def verify_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    context = {
        'ticket': ticket,
        'already_verified': ticket.is_verified
    }
    if not ticket.is_verified:
        ticket.is_verified = True
        ticket.save()
    return render(request, 'bookings/verify.html', context)



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        email = request.POST.get('email', '')
        
        # Validate email
        if not email:
            messages.error(request, 'Email is required!')
            return render(request, 'registration/register.html', {'form': form})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered!')
            return render(request, 'registration/register.html', {'form': form})
        
        if form.is_valid():
            user = form.save()
            user.email = email
            user.save()
            
            # Send confirmation email
            subject = "Welcome to EventPass - Registration Confirmation"
            message = f"""
Hello {user.username},

Thank you for registering with EventPass!

Your registration is complete and your account is now active.

Account Details:
- Username: {user.username}
- Email: {user.email}

You can now login and start booking tickets for exciting events!

Login here: http://127.0.0.1:8000/login/

Best regards,
EventPass Team
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Registration successful! Check your email for confirmation.')
            except Exception as e:
                messages.warning(request, f'Registration successful! Email confirmation could not be sent: {str(e)}')
                logger.error(f"Registration email failed for {user.email}: {str(e)}")
            
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


def event_list(request):
    events = Event.objects.all()[:10]  # Limit to 10 events for better display
    return render(request, 'bookings/event.html', {'events': events})


def qr_scanner(request):
    """Render a QR scanner page that uses the webcam to scan ticket QR codes locally."""
    return render(request, 'bookings/qr_scan.html')