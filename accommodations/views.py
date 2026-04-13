from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from datetime import date, timedelta
from .models import Accommodation, Hotel, Apartment
from .serializers import AccommodationSerializer, HotelSerializer, ApartmentSerializer


# =============================================================================
# Base Accommodation Views (deprecated for creation)
# =============================================================================

class AccommodationListCreateView(generics.ListCreateAPIView):
    """List all accommodations. Creation is deprecated - use /hotels/ or /apartments/"""
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer

    @extend_schema(
        summary="List all accommodations",
        description="Get a list of all accommodations (hotels and apartments)",
        tags=["Accommodations"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create accommodation (DEPRECATED)",
        description="Deprecated. Use POST /hotels/ or POST /apartments/ instead.",
        tags=["Accommodations"],
        deprecated=True
    )
    def post(self, request, *args, **kwargs):
        return Response(
            {"error": "Direct accommodation creation is deprecated. Use /hotels/ or /apartments/ instead."},
            status=status.HTTP_400_BAD_REQUEST
        )


class AccommodationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an accommodation"""
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer

    @extend_schema(
        summary="Get accommodation by ID",
        description="Retrieve a specific accommodation by its ID",
        tags=["Accommodations"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update accommodation",
        description="Update a specific accommodation",
        tags=["Accommodations"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Delete accommodation",
        description="Delete a specific accommodation",
        tags=["Accommodations"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# =============================================================================
# Hotel Views
# =============================================================================

class HotelListCreateView(generics.ListCreateAPIView):
    """List all hotels or create a new hotel"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer

    @extend_schema(summary="List all hotels", tags=["Hotels"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a new hotel", tags=["Hotels"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class HotelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a hotel"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer

    @extend_schema(summary="Get hotel by ID", tags=["Hotels"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update hotel", tags=["Hotels"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Delete hotel", tags=["Hotels"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# =============================================================================
# Apartment Views
# =============================================================================

class ApartmentListCreateView(generics.ListCreateAPIView):
    """List all apartments or create a new apartment"""
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer

    @extend_schema(summary="List all apartments", tags=["Apartments"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a new apartment", tags=["Apartments"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ApartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an apartment"""
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer

    @extend_schema(summary="Get apartment by ID", tags=["Apartments"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update apartment", tags=["Apartments"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Delete apartment", tags=["Apartments"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# =============================================================================
# Availability View
# =============================================================================

class NextAvailableDateView(APIView):
    """Get the next available date for an accommodation"""

    @extend_schema(
        summary="Get next available date",
        description="Find the next available booking date for an accommodation",
        tags=["Availability"],
        parameters=[
            OpenApiParameter(
                name='from_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start searching from this date (default: today)',
                required=False
            ),
            OpenApiParameter(
                name='max_days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Maximum days to search ahead (default: 90)',
                required=False
            ),
        ],
        responses={200: dict}
    )
    def get(self, request, pk):
        # Get accommodation
        try:
            accommodation = Accommodation.objects.get(pk=pk)
        except Accommodation.DoesNotExist:
            return Response(
                {"error": "Accommodation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse parameters
        from_date_str = request.query_params.get('from_date')
        if from_date_str:
            try:
                from_date = date.fromisoformat(from_date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            from_date = date.today()

        max_days = int(request.query_params.get('max_days', 90))
        search_end = from_date + timedelta(days=max_days)

        # Hotels are always "available" (multiple rooms)
        if accommodation.accommodation_type == 'hotel':
            return Response({
                "accommodation_id": accommodation.id,
                "accommodation_name": accommodation.name,
                "accommodation_type": "hotel",
                "search_from": str(from_date),
                "next_available_date": str(from_date),
                "available_until": None,
                "days_until_available": 0,
                "message": "Hotels accept concurrent bookings for different rooms"
            })

        # For apartments: find gaps in bookings
        from bookings.models import Booking

        bookings = Booking.objects.filter(
            accommodation_id=pk,
            end_date__gt=from_date,
            start_date__lt=search_end
        ).order_by('start_date')

        result = self._find_availability(from_date, search_end, bookings)

        return Response({
            "accommodation_id": accommodation.id,
            "accommodation_name": accommodation.name,
            "accommodation_type": accommodation.accommodation_type or "generic",
            "search_from": str(from_date),
            **result
        })

    def _find_availability(self, from_date, search_end, bookings):
        """Find next available date from bookings list"""
        if not bookings.exists():
            return {
                "next_available_date": str(from_date),
                "available_until": str(search_end),
                "days_until_available": 0,
                "message": "Available immediately"
            }

        current_date = from_date

        for booking in bookings:
            if current_date < booking.start_date:
                # Found a gap before this booking
                return {
                    "next_available_date": str(current_date),
                    "available_until": str(booking.start_date),
                    "days_until_available": (current_date - from_date).days
                }
            # Move past this booking
            current_date = max(current_date, booking.end_date)

        # Check after all bookings
        if current_date <= search_end:
            return {
                "next_available_date": str(current_date),
                "available_until": str(search_end),
                "days_until_available": (current_date - from_date).days
            }

        # No availability found
        return {
            "next_available_date": None,
            "available_until": None,
            "days_until_available": None,
            "message": f"No availability found within {(search_end - from_date).days} days"
        }