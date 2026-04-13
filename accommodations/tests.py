from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Accommodation, Hotel, Apartment
from bookings.models import Booking


class HotelModelTests(TestCase):
    """Test Hotel model"""

    def test_create_hotel_sets_type(self):
        """Hotel automatically sets accommodation_type to 'hotel'"""
        hotel = Hotel.objects.create(
            name="Test Hotel",
            price=Decimal("150.00"),
            location="Downtown",
            room_count=50
        )
        self.assertEqual(hotel.accommodation_type, 'hotel')

    def test_hotel_has_specific_fields(self):
        """Hotel has room_count and star_rating"""
        hotel = Hotel.objects.create(
            name="Luxury Hotel",
            price=Decimal("300.00"),
            location="Beach",
            room_count=100,
            star_rating=5
        )
        self.assertEqual(hotel.room_count, 100)
        self.assertEqual(hotel.star_rating, 5)

    def test_hotel_appears_in_accommodation_queryset(self):
        """Hotels accessible via Accommodation.objects"""
        Hotel.objects.create(name="Hotel A", price=100, location="City", room_count=20)
        self.assertEqual(Accommodation.objects.filter(accommodation_type='hotel').count(), 1)


class ApartmentModelTests(TestCase):
    """Test Apartment model"""

    def test_create_apartment_sets_type(self):
        """Apartment automatically sets accommodation_type to 'apartment'"""
        apt = Apartment.objects.create(
            name="Cozy Studio",
            price=Decimal("80.00"),
            location="Midtown",
            bedrooms=1
        )
        self.assertEqual(apt.accommodation_type, 'apartment')

    def test_apartment_has_specific_fields(self):
        """Apartment has bedrooms and floor_number"""
        apt = Apartment.objects.create(
            name="Penthouse",
            price=Decimal("250.00"),
            location="High Rise",
            bedrooms=3,
            floor_number=25
        )
        self.assertEqual(apt.bedrooms, 3)
        self.assertEqual(apt.floor_number, 25)


class HotelAPITests(APITestCase):
    """Test Hotel API endpoints"""

    def test_list_hotels(self):
        """GET /hotels/ returns only hotels"""
        Hotel.objects.create(name="Hotel A", price=100, location="City", room_count=20)
        Apartment.objects.create(name="Apt A", price=80, location="Town", bedrooms=2)

        response = self.client.get('/hotels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Hotel A")

    def test_create_hotel(self):
        """POST /hotels/ creates a hotel"""
        data = {
            "name": "New Hotel",
            "price": "200.00",
            "location": "Beach",
            "room_count": 30,
            "star_rating": 4
        }
        response = self.client.post('/hotels/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Hotel.objects.count(), 1)
        self.assertEqual(response.data['accommodation_type'], 'hotel')

    def test_get_hotel_detail(self):
        """GET /hotels/{id}/ returns hotel details"""
        hotel = Hotel.objects.create(name="Hotel X", price=150, location="Park", room_count=40)

        response = self.client.get(f'/hotels/{hotel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['room_count'], 40)

    def test_update_hotel(self):
        """PUT /hotels/{id}/ updates hotel"""
        hotel = Hotel.objects.create(name="Old Name", price=100, location="City", room_count=10)

        response = self.client.put(f'/hotels/{hotel.id}/', {
            "name": "New Name",
            "price": "150.00",
            "location": "City",
            "room_count": 20
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hotel.refresh_from_db()
        self.assertEqual(hotel.name, "New Name")

    def test_delete_hotel(self):
        """DELETE /hotels/{id}/ deletes hotel"""
        hotel = Hotel.objects.create(name="Delete Me", price=100, location="City", room_count=10)

        response = self.client.delete(f'/hotels/{hotel.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Hotel.objects.count(), 0)


class ApartmentAPITests(APITestCase):
    """Test Apartment API endpoints"""

    def test_list_apartments(self):
        """GET /apartments/ returns only apartments"""
        Hotel.objects.create(name="Hotel A", price=100, location="City", room_count=20)
        Apartment.objects.create(name="Apt A", price=80, location="Town", bedrooms=2)

        response = self.client.get('/apartments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Apt A")

    def test_create_apartment(self):
        """POST /apartments/ creates an apartment"""
        data = {
            "name": "New Apartment",
            "price": "100.00",
            "location": "Downtown",
            "bedrooms": 2,
            "floor_number": 5
        }
        response = self.client.post('/apartments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Apartment.objects.count(), 1)
        self.assertEqual(response.data['accommodation_type'], 'apartment')


class AccommodationDeprecationTests(APITestCase):
    """Test that POST /accommodations/ is deprecated"""

    def test_post_accommodations_deprecated(self):
        """POST /accommodations/ returns 400"""
        data = {
            "name": "Test",
            "price": "100.00",
            "location": "City"
        }
        response = self.client.post('/accommodations/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('deprecated', response.data['error'].lower())

    def test_get_accommodations_still_works(self):
        """GET /accommodations/ still returns all accommodations"""
        Hotel.objects.create(name="Hotel", price=100, location="City", room_count=10)
        Apartment.objects.create(name="Apt", price=80, location="Town", bedrooms=1)

        response = self.client.get('/accommodations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)


class NextAvailableDateTests(APITestCase):
    """Test next available date endpoint"""

    def setUp(self):
        self.apartment = Apartment.objects.create(
            name="Test Apt",
            price=Decimal("100.00"),
            location="City",
            bedrooms=2
        )
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            price=Decimal("150.00"),
            location="City",
            room_count=50
        )

    def test_available_immediately_no_bookings(self):
        """Returns from_date when no bookings"""
        response = self.client.get(
            f'/accommodations/{self.apartment.id}/next-available/',
            {'from_date': '2024-03-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['next_available_date'], '2024-03-01')

    def test_returns_date_after_booking(self):
        """Returns end_date when from_date is during booking"""
        Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Guest"
        )

        response = self.client.get(
            f'/accommodations/{self.apartment.id}/next-available/',
            {'from_date': '2024-03-12'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['next_available_date'], '2024-03-15')

    def test_hotel_always_available(self):
        """Hotels always return from_date"""
        Booking.objects.create(
            accommodation=self.hotel,
            start_date=date(2024, 3, 10),
            end_date=date(2024, 3, 15),
            guest_name="Guest"
        )

        response = self.client.get(
            f'/accommodations/{self.hotel.id}/next-available/',
            {'from_date': '2024-03-12'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['next_available_date'], '2024-03-12')
        self.assertIn('concurrent', response.data.get('message', '').lower())

    def test_finds_gap_between_bookings(self):
        """Finds availability gap between bookings"""
        Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 10),
            guest_name="First"
        )
        Booking.objects.create(
            accommodation=self.apartment,
            start_date=date(2024, 3, 20),
            end_date=date(2024, 3, 25),
            guest_name="Second"
        )

        response = self.client.get(
            f'/accommodations/{self.apartment.id}/next-available/',
            {'from_date': '2024-03-05'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['next_available_date'], '2024-03-10')
        self.assertEqual(response.data['available_until'], '2024-03-20')

    def test_404_for_invalid_id(self):
        """Returns 404 for non-existent accommodation"""
        response = self.client.get('/accommodations/99999/next-available/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_uses_today_as_default(self):
        """Uses today when from_date not provided"""
        response = self.client.get(f'/accommodations/{self.apartment.id}/next-available/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['search_from'], str(date.today()))
