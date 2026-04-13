from rest_framework import serializers
from .models import Accommodation, Hotel, Apartment


class AccommodationSerializer(serializers.ModelSerializer):
    """Serializer for base Accommodation model"""

    class Meta:
        model = Accommodation
        fields = ['id', 'name', 'description', 'price', 'location', 'accommodation_type']
        read_only_fields = ['id', 'accommodation_type']

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value

    def validate_location(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Location must be at least 2 characters")
        return value


class HotelSerializer(AccommodationSerializer):
    """Serializer for Hotel model"""

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'description', 'price', 'location',
                  'accommodation_type', 'room_count', 'star_rating']
        read_only_fields = ['id', 'accommodation_type']


class ApartmentSerializer(AccommodationSerializer):
    """Serializer for Apartment model"""

    class Meta:
        model = Apartment
        fields = ['id', 'name', 'description', 'price', 'location',
                  'accommodation_type', 'bedrooms', 'floor_number']
        read_only_fields = ['id', 'accommodation_type']