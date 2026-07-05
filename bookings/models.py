from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from django.conf import settings



class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='event_images/')
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, default='Venue TBD')

    def __str__(self):
        return self.title


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    ticket_id = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    # ADD THIS FIELD:
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return f"{self.customer_name} - {self.event.title}"

    # ADD THIS METHOD to generate the QR code automatically
    def save(self, *args, **kwargs):
        if not self.qr_code:  # Only generate if it doesn't exist
            # 1. Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"http://127.0.0.1:8000/verify/{self.ticket_id}/")
            qr.make(fit=True)

            # 2. Create the image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 3. Save it to a buffer so Django can handle it as a file
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            fname = f'qr-{self.ticket_id}.png'
            
            self.qr_code.save(fname, File(buffer), save=False)
            
        super().save(*args, **kwargs)


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    tickets = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"