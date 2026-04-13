from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Accommodation(models.Model):
    """Base accommodation model"""
    ACCOMMODATION_TYPES = [
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    accommodation_type = models.CharField(
        max_length=20,
        choices=ACCOMMODATION_TYPES,
        blank=True,
        default=''
    )

    class Meta:
        db_table = 'accommodation'

    def __str__(self):
        return self.name


class Hotel(Accommodation):
    """Hotel - allows overlapping bookings (multiple rooms)"""
    room_count = models.PositiveIntegerField(default=1)
    star_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'hotel'

    def save(self, *args, **kwargs):
        self.accommodation_type = 'hotel'
        super().save(*args, **kwargs)


class Apartment(Accommodation):
    """Apartment - does NOT allow overlapping bookings"""
    bedrooms = models.PositiveSmallIntegerField(default=1)
    floor_number = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'apartment'

    def save(self, *args, **kwargs):
        self.accommodation_type = 'apartment'
        super().save(*args, **kwargs)