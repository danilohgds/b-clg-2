from django.urls import path
from .views import AccommodationListCreateView, AccommodationDetailView

urlpatterns = [
    path('', AccommodationListCreateView.as_view(), name='accommodation-list-create'),
    path('<int:pk>/', AccommodationDetailView.as_view(), name='accommodation-detail'),
]