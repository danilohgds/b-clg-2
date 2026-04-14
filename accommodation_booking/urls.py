"""
URL configuration for accommodation_booking project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accommodations.urls import hotel_urlpatterns, apartment_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accommodations/', include('accommodations.urls')),
    path('hotels/', include(hotel_urlpatterns)),
    path('apartments/', include(apartment_urlpatterns)),
    path('bookings/', include('bookings.urls')),
    # Voice notes nested under bookings
    path('bookings/<int:booking_id>/voice-notes/', include('voice_notes.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('documentation/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)