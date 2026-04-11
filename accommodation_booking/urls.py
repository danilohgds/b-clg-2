"""
URL configuration for accommodation_booking project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accommodations/', include('accommodations.urls')),
    path('bookings/', include('bookings.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('documentation/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] 