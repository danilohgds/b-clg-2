from django.contrib import admin
from .models import Accommodation


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'price']
    list_filter = ['location']
    search_fields = ['name', 'location'] 