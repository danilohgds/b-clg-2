from rest_framework import serializers
from .models import Accommodation


class AccommodationSerializer(serializers.ModelSerializer):
    """Serializer for Accommodation model"""
    
    class Meta:
        model = Accommodation
        fields = ['id', 'name', 'description', 'price', 'location']
        read_only_fields = ['id']

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