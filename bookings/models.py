from django.db import models
from django.core.exceptions import ValidationError
from accommodations.models import Accommodation


class Booking(models.Model):
    """Booking model"""
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    guest_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'booking'
        indexes = [
            models.Index(
                fields=['accommodation', 'start_date', 'end_date'],
                name='booking_availability_idx'
            ),
        ]

    def __str__(self):
        return f"{self.guest_name} - {self.accommodation.name} ({self.start_date} to {self.end_date})"

    def clean(self):
        super().clean()
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")
        self._validate_no_overlap_for_apartments()

    def _validate_no_overlap_for_apartments(self):
        """Apartments cannot have overlapping bookings"""
        if not self.accommodation_id:
            return

        # Only validate apartments
        if self.accommodation.accommodation_type != 'apartment':
            return

        # Find overlapping bookings: A.start < B.end AND A.end > B.start
        overlapping = Booking.objects.filter(
            accommodation_id=self.accommodation_id,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(pk=self.pk)

        if overlapping.exists():
            conflict = overlapping.first()
            raise ValidationError(
                f"This apartment is already booked from {conflict.start_date} to {conflict.end_date}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)