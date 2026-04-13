from django.urls import path
from .views import (
    AccommodationListCreateView, AccommodationDetailView,
    HotelListCreateView, HotelDetailView,
    ApartmentListCreateView, ApartmentDetailView,
    NextAvailableDateView
)

urlpatterns = [
    # Base accommodations (list only, creation deprecated)
    path('', AccommodationListCreateView.as_view(), name='accommodation-list-create'),
    path('<int:pk>/', AccommodationDetailView.as_view(), name='accommodation-detail'),
    path('<int:pk>/next-available/', NextAvailableDateView.as_view(), name='next-available-date'),
]

hotel_urlpatterns = [
    path('', HotelListCreateView.as_view(), name='hotel-list-create'),
    path('<int:pk>/', HotelDetailView.as_view(), name='hotel-detail'),
]

apartment_urlpatterns = [
    path('', ApartmentListCreateView.as_view(), name='apartment-list-create'),
    path('<int:pk>/', ApartmentDetailView.as_view(), name='apartment-detail'),
]