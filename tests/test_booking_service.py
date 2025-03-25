from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.schemas import BookingCreate, BookingUpdate
from app.services.booking_service import BookingService


@pytest.fixture
def mock_booking_repository():
    repository = Mock()
    return repository


@pytest.fixture
def mock_guest_repository():
    repository = Mock()
    return repository


@pytest.fixture
def mock_communication_service():
    service = Mock()
    return service


@pytest.fixture
def booking_service(
    mock_booking_repository, mock_guest_repository, mock_communication_service
):
    return BookingService(
        booking_repository=mock_booking_repository,
        guest_repository=mock_guest_repository,
        communication_service=mock_communication_service,
    )


@pytest.fixture
def sample_booking_data():
    return BookingCreate(
        guest_id=1,
        check_in=datetime.now().date(),
        check_out=(datetime.now() + timedelta(days=5)).date(),
    )


@pytest.fixture
def sample_booking():
    booking = Mock()
    booking.guest_id = 1
    check_in = (datetime.now().date(),)
    check_out = (datetime.now() + timedelta(days=5)).date()
    return booking


@pytest.fixture
def sample_guest():
    guest = Mock()
    guest.id = 1
    guest.first_name = "John"
    guest.last_name = "Doe"
    guest.email = "john.doe@wxample.com"
    guest.pays_dayrate = True
    return guest


class TestBookingService:
    def test_create_booking(
        self,
        booking_service,
        mock_booking_repository,
        sample_booking_data,
        sample_booking,
    ):
        mock_booking_repository.create.return_value = sample_booking
        result = booking_service.create_booking(sample_booking_data)
        mock_booking_repository.create.assert_called_once_with(
            sample_booking_data.dict()
        )
        assert result == sample_booking

    def test_get_all_bookings(
        self, booking_service, mock_booking_repository, sample_booking
    ):
        # Configure mock to return a list of sample bookings
        mock_booking_repository.get_all.return_value = [sample_booking]

        # Call the method
        result = booking_service.get_all_bookings()

        # Verify the repository was called
        mock_booking_repository.get_all.assert_called_once()

        # Verify the result is what we expect
        assert result == [sample_booking]

    def test_get_booking_by_id_existing(
        self, booking_service, mock_booking_repository, sample_booking
    ):
        # Configure mock to return a sample booking when get_by_id is called
        mock_booking_repository.get_by_id.return_value = sample_booking

        # Call the method
        result = booking_service.get_booking_by_id(1)

        # Verify the repository was called with the right arguments
        mock_booking_repository.get_by_id.assert_called_once_with(1)

        # Verify the result is what we expect
        assert result == sample_booking

    def test_get_booking_by_id_not_found(
        self, booking_service, mock_booking_repository
    ):
        # Configure mock to return None when get_by_id is called
        mock_booking_repository.get_by_id.return_value = None

        # Call the method and expect a ValueError
        with pytest.raises(ValueError) as excinfo:
            booking_service.get_booking_by_id(999)

        # Verify the error message
        assert "Booking with ID 999 not found" in str(excinfo.value)

        # Verify the repository was called with the right arguments
        mock_booking_repository.get_by_id.assert_called_once_with(999)

    def test_update_booking(
        self, booking_service, mock_booking_repository, sample_booking
    ):
        # Create a booking update data
        booking_update = BookingUpdate(confirmed=True)

        # Configure repository mock
        mock_booking_repository.get_by_id.return_value = sample_booking
        mock_booking_repository.update.return_value = sample_booking

        # Call the method
        result = booking_service.update_booking(1, booking_update)

        # Verify get_by_id was called
        mock_booking_repository.get_by_id.assert_called_once_with(1)

        # Verify the fields were updated
        assert sample_booking.confirmed == True
        assert isinstance(sample_booking.modified_at, datetime)

        # Verify update was called
        mock_booking_repository.update.assert_called_once_with(sample_booking)

        # Verify the result
        assert result == sample_booking

    def test_confirm_booking(
        self,
        booking_service,
        mock_booking_repository,
        mock_guest_repository,
        sample_booking,
        sample_guest,
    ):
        # Configure mocks
        mock_booking_repository.get_by_id.return_value = sample_booking
        mock_booking_repository.update.return_value = sample_booking
        mock_guest_repository.get_by_id.return_value = sample_guest

        # Set up a spy for the _send_booking_confirmation method
        with patch.object(booking_service, "_send_booking_confirmation") as mock_send:
            # Call the method
            result = booking_service.confirm_booking(1)

            # Verify the booking was updated with confirmed=True
            assert sample_booking.confirmed is True

            # Verify the guest repository was called to get the guest
            mock_guest_repository.get_by_id.assert_called_once_with(
                guest_id=sample_booking.guest_id
            )

            # Verify the email notification was sent
            mock_send.assert_called_once_with(sample_booking, sample_guest)

            # Verify the result
            assert result == sample_booking

    def test_send_booking_confirmation(
        self, booking_service, mock_communication_service, sample_booking, sample_guest
    ):
        # Call the method
        booking_service._send_booking_confirmation(sample_booking, sample_guest)

        # Verify communication service was called with the right parameters
        mock_communication_service.send_email.assert_called_once()
        call_args = mock_communication_service.send_email.call_args

        # Check the arguments
        assert call_args[1]["recipient"] == sample_guest.email
        assert call_args[1]["subject"] == "Booking confirmation"
        assert call_args[1]["template_name"] == "bkg_confirmation_template"

        # Check the context dictionary
        context = call_args[1]["context"]
        assert context["guest_name"] == "John Doe"
        assert "check_in" in context
        assert "check_out" in context
        assert context["booking_id"] == sample_booking.id
