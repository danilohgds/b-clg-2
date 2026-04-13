from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from accommodations.models import Hotel, Apartment
from .models import Booking


class ApartmentOverlapModelTests(TestCase):
    """Test apartment booking overlap validation at model level"""

    def setUp(self):
        self.apartment = Apartment.objects.create(
            name="Test Apt",
            price=Decimal("100.00"),
            location="City",
            bedrooms=2
        )
        # Existing booking: March 10-15
        self.existing = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Existing Guest"
        )

    def test_same_dates_rejected(self):
        """Booking with exact same dates rejected"""
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                accommodation=self.apartment,
                start_date=date(2024, 3, 10),
                end_date=date(2024, 3, 15),
                guest_name="New Guest"
            )

    def test_overlap_start_rejected(self):
        """Booking overlapping start of existing rejected"""
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                accommodation=self.apartment,
                start_date=date(2024, 3, 8),
                end_date=date(2024, 3, 12),
                guest_name="New Guest"
            )

    def test_overlap_end_rejected(self):
        """Booking overlapping end of existing rejected"""
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                accommodation=self.apartment,
                start_date=date(2024, 3, 13),
                end_date=date(2024, 3, 18),
                guest_name="New Guest"
            )

    def test_contained_within_rejected(self):
        """Booking fully within existing rejected"""
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                accommodation=self.apartment,
                start_date=date(2024, 3, 11),
                end_date=date(2024, 3, 14),
                guest_name="New Guest"
            )

    def test_containing_existing_rejected(self):
        """Booking containing existing rejected"""
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                accommodation=self.apartment,
                start_date=date(2024, 3, 5),
                end_date=date(2024, 3, 20),
                guest_name="New Guest"
            )

    def test_adjacent_after_allowed(self):
        """Booking starting on existing end_date allowed (checkout=checkin)"""
        booking = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 15),  # Same as existing end_date
            end_date=date(2024, 3, 20),
            guest_name="New Guest"
        )
        self.assertIsNotNone(booking.id)

    def test_adjacent_before_allowed(self):
        """Booking ending on existing start_date allowed"""
        booking = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 5),
            end_date=date(2024, 3, 10),  # Same as existing start_date
            guest_name="New Guest"
        )
        self.assertIsNotNone(booking.id)

    def test_non_overlapping_allowed(self):
        """Completely separate dates allowed"""
        booking = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 5),
            guest_name="New Guest"
        )
        self.assertIsNotNone(booking.id)


class HotelOverlapModelTests(TestCase):
    """Test that hotels ALLOW overlapping bookings"""

    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            price=Decimal("150.00"),
            location="City",
            room_count=50
        )
        self.existing = Booking.objects.create(
            accommodation=self.hotel,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Guest 1"
        )

    def test_overlapping_allowed_for_hotel(self):
        """Hotels allow overlapping bookings"""
        booking = Booking.objects.create(
            accommodation=self.hotel,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Guest 2"
        )
        self.assertIsNotNone(booking.id)

    def test_multiple_overlapping_allowed(self):
        """Hotels allow many overlapping bookings"""
        for i in range(10):
            Booking.objects.create(
                accommodation=self.hotel,
                start_date=date(2024, 3, 10),
                end_date=date(2024, 3, 15),
                guest_name=f"Guest {i+2}"
            )
        self.assertEqual(Booking.objects.filter(accommodation=self.hotel).count(), 11)


class BookingAPIOverlapTests(APITestCase):
    """Test overlap validation via API"""

    def setUp(self):
        self.apartment = Apartment.objects.create(
            name="API Apt",
            price=Decimal("100.00"),
            location="City",
            bedrooms=1
        )
        Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Existing"
        )

    def test_api_rejects_overlapping_apartment_booking(self):
        """POST /bookings/ returns 400 for overlapping apartment booking"""
        data = {
            "accommodation_id": self.apartment.id,
            "start_date": "2024-03-12",
            "end_date": "2024-03-18",
            "guest_name": "API Guest"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already booked', str(response.data).lower())

    def test_api_allows_adjacent_booking(self):
        """POST /bookings/ allows adjacent booking"""
        data = {
            "accommodation_id": self.apartment.id,
            "start_date": "2024-03-15",
            "end_date": "2024-03-20",
            "guest_name": "Adjacent Guest"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class BookingAPIBasicTests(APITestCase):
    """Test basic booking API functionality"""

    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            price=Decimal("150.00"),
            location="City",
            room_count=50
        )

    def test_create_booking(self):
        """POST /bookings/ creates a booking"""
        data = {
            "accommodation_id": self.hotel.id,
            "start_date": "2024-03-01",
            "end_date": "2024-03-05",
            "guest_name": "John Doe"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)

    def test_list_bookings(self):
        """GET /bookings/ returns all bookings"""
        Booking.objects.create(
            accommodation=self.hotel,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 5),
            guest_name="Guest"
        )
        response = self.client.get('/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_end_date_must_be_after_start_date(self):
        """Rejects booking where end_date <= start_date"""
        data = {
            "accommodation_id": self.hotel.id,
            "start_date": "2024-03-10",
            "end_date": "2024-03-05",
            "guest_name": "Guest"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_accommodation_id(self):
        """Rejects booking with non-existent accommodation"""
        data = {
            "accommodation_id": 99999,
            "start_date": "2024-03-01",
            "end_date": "2024-03-05",
            "guest_name": "Guest"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_shows_accommodation_type(self):
        """Booking response includes accommodation_type"""
        data = {
            "accommodation_id": self.hotel.id,
            "start_date": "2024-03-01",
            "end_date": "2024-03-05",
            "guest_name": "Guest"
        }
        response = self.client.post('/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['accommodation_type'], 'hotel')


class BookingUpdateTests(APITestCase):
    """Test booking update scenarios"""

    def setUp(self):
        self.apartment = Apartment.objects.create(
            name="Test Apt",
            price=Decimal("100.00"),
            location="City",
            bedrooms=1
        )
        self.booking1 = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Guest 1"
        )
        self.booking2 = Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 20),
            end_date=date(2024, 3, 25),
            guest_name="Guest 2"
        )

    def test_update_own_dates_allowed(self):
        """Can update a booking's own dates without conflict"""
        response = self.client.put(f'/bookings/{self.booking1.id}/', {
            "accommodation_id": self.apartment.id,
            "start_date": "2024-03-11",
            "end_date": "2024-03-16",
            "guest_name": "Guest 1 Updated"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_to_overlap_rejected(self):
        """Cannot update booking to overlap with another"""
        response = self.client.put(f'/bookings/{self.booking1.id}/', {
            "accommodation_id": self.apartment.id,
            "start_date": "2024-03-18",
            "end_date": "2024-03-22",
            "guest_name": "Guest 1"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
