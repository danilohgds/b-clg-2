from django.db import models


class Accommodation(models.Model):
    """Accommodation model"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)

    class Meta:
        db_table = 'accommodation'

    def __str__(self):
        return self.name 