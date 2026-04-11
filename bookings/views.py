from rest_framework import generics
from drf_spectacular.utils import extend_schema
from .models import Booking
from .serializers import BookingSerializer


class BookingListCreateView(generics.ListCreateAPIView):
    """List all bookings or create a new booking"""
    queryset = Booking.objects.select_related('accommodation').all()
    serializer_class = BookingSerializer

    @extend_schema(
        summary="List all bookings",
        description="Get a list of all bookings",
        tags=["Bookings"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new booking",
        description="Create a new booking for an accommodation",
        tags=["Bookings"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a booking"""
    queryset = Booking.objects.select_related('accommodation').all()
    serializer_class = BookingSerializer

    @extend_schema(
        summary="Get booking by ID",
        description="Retrieve a specific booking by its ID",
        tags=["Bookings"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update booking",
        description="Update a specific booking",
        tags=["Bookings"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Delete booking",
        description="Delete a specific booking",
        tags=["Bookings"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs) 