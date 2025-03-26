from unittest.mock import Mock

import pytest

from app.schemas import GuestCreate
from app.services.guest_service import GuestService


@pytest.fixture
def mock_guest_repository():
    repository = Mock()
    return repository


@pytest.fixture
def guest_service(mock_guest_repository):
    return GuestService(guest_repository=mock_guest_repository)


@pytest.fixture
def sample_guest_data():
    return GuestCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="strongPassword123",
    )


@pytest.fixture
def sample_guest():
    guest = Mock()
    guest.id = 1
    guest.first_name = "John"
    guest.last_name = "Doe"
    guest.email = "john.doe@example.com"
    guest.hashed_password = "hashed_password_value"
    return guest


class TestGuestService:
    def test_hash_password(self, guest_service):
        """Test that password hashing works correctly."""
        password = "testPassword123"
        hashed = guest_service.hash_password(password)

        # Check that result is a non-empty string
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Check that result is different from original
        assert hashed != password

    def test_create_guest_success(
        self, guest_service, mock_guest_repository, sample_guest_data, sample_guest
    ):
        """Test creating a guest when email doesn't exist."""
        # Setup mocks
        mock_guest_repository.get_by_email.return_value = None
        mock_guest_repository.create.return_value = sample_guest

        # Mock the hash_password method to return a predictable value
        guest_service.hash_password = Mock(return_value="hashed_password_value")

        # Call the method
        result = guest_service.create_guest(sample_guest_data)

        # Verify behavior
        mock_guest_repository.get_by_email.assert_called_once_with(
            sample_guest_data.email
        )

        # Check that create was called with the correct type of argument
        mock_guest_repository.create.assert_called_once()

        # Extract the actual dictionary passed to create
        actual_dict = mock_guest_repository.create.call_args[0][0]

        # Verify the dictionary has the expected structure
        assert "first_name" in actual_dict
        assert "last_name" in actual_dict
        assert "email" in actual_dict
        assert "hashed_password" in actual_dict
        assert "password" not in actual_dict

        assert actual_dict["first_name"] == sample_guest_data.first_name
        assert actual_dict["last_name"] == sample_guest_data.last_name
        assert actual_dict["email"] == sample_guest_data.email
        assert actual_dict["hashed_password"] == "hashed_password_value"

        # Verify return value
        assert result == sample_guest

    def test_create_guest_duplicate_email(
        self, guest_service, mock_guest_repository, sample_guest_data, sample_guest
    ):
        """Test creating a guest when email already exists."""
        # Setup mock to return an existing guest
        mock_guest_repository.get_by_email.return_value = sample_guest

        # Expect ValueError to be raised
        with pytest.raises(ValueError) as excinfo:
            guest_service.create_guest(sample_guest_data)

        # Verify error message
        assert f"Guest with email {sample_guest_data.email} already exists" in str(
            excinfo.value
        )

        # Verify get_by_email was called but create was not
        mock_guest_repository.get_by_email.assert_called_once_with(
            sample_guest_data.email
        )
        mock_guest_repository.create.assert_not_called()

    def test_get_all_guests(self, guest_service, mock_guest_repository):
        """Test retrieving all guests."""
        # Setup mock
        expected_guests = [Mock(), Mock()]
        mock_guest_repository.get_all.return_value = expected_guests

        # Call the method
        result = guest_service.get_all_guests()

        # Verify behavior
        mock_guest_repository.get_all.assert_called_once()
        assert result == expected_guests

    def test_get_guest_by_id_success(
        self, guest_service, mock_guest_repository, sample_guest
    ):
        """Test retrieving a guest by ID when the guest exists."""
        # Setup mock
        guest_id = 1
        mock_guest_repository.get_by_id.return_value = sample_guest

        # Call the method
        result = guest_service.get_guest_by_id(guest_id)

        # Verify behavior
        mock_guest_repository.get_by_id.assert_called_once_with(guest_id)
        assert result == sample_guest

    def test_get_guest_by_id_not_found(self, guest_service, mock_guest_repository):
        """Test retrieving a guest by ID when the guest doesn't exist."""
        # Setup mock
        guest_id = 999
        mock_guest_repository.get_by_id.return_value = None

        # Expect ValueError to be raised
        with pytest.raises(ValueError) as excinfo:
            guest_service.get_guest_by_id(guest_id)

        # Verify error message
        assert f"Guest with ID {guest_id} not found" in str(excinfo.value)

        # Verify get_by_id was called
        mock_guest_repository.get_by_id.assert_called_once_with(guest_id)
