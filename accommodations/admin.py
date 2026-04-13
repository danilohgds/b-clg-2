from django.contrib import admin
from .models import Accommodation, Hotel, Apartment


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'price', 'accommodation_type']
    list_filter = ['location', 'accommodation_type']
    search_fields = ['name', 'location']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'price', 'room_count', 'star_rating']
    list_filter = ['location', 'star_rating']
    search_fields = ['name', 'location']


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'price', 'bedrooms', 'floor_number']
    list_filter = ['location', 'bedrooms']
    search_fields = ['name', 'location']