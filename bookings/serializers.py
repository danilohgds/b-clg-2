from rest_framework import serializers
from .models import Booking
from accommodations.models import Accommodation


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    accommodation_id = serializers.IntegerField(write_only=True)
    accommodation = serializers.StringRelatedField(read_only=True)
    accommodation_type = serializers.CharField(source='accommodation.accommodation_type', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'accommodation_id', 'accommodation', 'accommodation_type',
                  'start_date', 'end_date', 'guest_name']
        read_only_fields = ['id', 'accommodation', 'accommodation_type']

    def validate_accommodation_id(self, value):
        """Validate accommodation exists"""
        if not Accommodation.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid accommodation ID")
        return value

    def validate_guest_name(self, value):
        """Validate guest name length"""
        if len(value) < 2:
            raise serializers.ValidationError("Guest name must be at least 2 characters")
        return value

    def validate(self, data):
        """Cross-field validation including overlap check"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})

        # Check overlap for apartments
        accommodation_id = data.get('accommodation_id')
        if accommodation_id and start_date and end_date:
            self._validate_apartment_overlap(accommodation_id, start_date, end_date)

        return data

    def _validate_apartment_overlap(self, accommodation_id, start_date, end_date):
        """Check apartment booking overlap"""
        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)
        except Accommodation.DoesNotExist:
            return

        if accommodation.accommodation_type != 'apartment':
            return

        # Exclude self when updating
        instance_pk = self.instance.pk if self.instance else None

        overlapping = Booking.objects.filter(
            accommodation_id=accommodation_id,
            start_date__lt=end_date,
            end_date__gt=start_date
        ).exclude(pk=instance_pk)

        if overlapping.exists():
            conflict = overlapping.first()
            raise serializers.ValidationError({
                "non_field_errors": [
                    f"This apartment is already booked from {conflict.start_date} to {conflict.end_date}"
                ]
            })

    def create(self, validated_data):
        """Create booking with accommodation"""
        accommodation_id = validated_data.pop('accommodation_id')
        accommodation = Accommodation.objects.get(id=accommodation_id)
        return Booking.objects.create(accommodation=accommodation, **validated_data)

    def update(self, instance, validated_data):
        """Update booking"""
        if 'accommodation_id' in validated_data:
            accommodation_id = validated_data.pop('accommodation_id')
            instance.accommodation = Accommodation.objects.get(id=accommodation_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance