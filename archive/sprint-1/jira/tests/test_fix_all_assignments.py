"""Tests for fix_all_assignments.py"""

from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fix_all_assignments import get_user_account_id, assign_ticket, verify_assignment


class TestGetUserAccountId:
    """Tests for get_user_account_id function."""

    @patch("fix_all_assignments.requests.get")
    def test_get_user_account_id_success(self, mock_get: Mock) -> None:
        """Test successful user account ID lookup."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"accountId": "test-account-id-123"}]
        mock_get.return_value = mock_response

        # Act
        result = get_user_account_id(config, "user@example.com")

        # Assert
        assert result == "test-account-id-123"
        mock_get.assert_called_once()

    @patch("fix_all_assignments.requests.get")
    def test_get_user_account_id_not_found(self, mock_get: Mock) -> None:
        """Test user account ID lookup when user not found."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Act
        result = get_user_account_id(config, "notfound@example.com")

        # Assert
        assert result is None

    @patch("fix_all_assignments.requests.get")
    def test_get_user_account_id_api_error(self, mock_get: Mock) -> None:
        """Test user account ID lookup when API returns error."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        # Act
        result = get_user_account_id(config, "user@example.com")

        # Assert
        assert result is None


class TestAssignTicket:
    """Tests for assign_ticket function."""

    @patch("fix_all_assignments.requests.put")
    def test_assign_ticket_success(self, mock_put: Mock) -> None:
        """Test successful ticket assignment."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        # Act
        result = assign_ticket(config, "BH-123", "account-id-123", "Test User")

        # Assert
        assert result is True
        mock_put.assert_called_once()

    @patch("fix_all_assignments.requests.put")
    def test_assign_ticket_failure(self, mock_put: Mock) -> None:
        """Test failed ticket assignment."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_put.return_value = mock_response

        # Act
        result = assign_ticket(config, "BH-123", "invalid-id", "Test User")

        # Assert
        assert result is False


class TestVerifyAssignment:
    """Tests for verify_assignment function."""

    @patch("fix_all_assignments.requests.get")
    def test_verify_assignment_success(self, mock_get: Mock) -> None:
        """Test successful assignment verification."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fields": {"assignee": {"displayName": "Marwan Samih"}}
        }
        mock_get.return_value = mock_response

        # Act
        result = verify_assignment(config, "BH-123", "Marwan")

        # Assert
        assert result is True

    @patch("fix_all_assignments.requests.get")
    def test_verify_assignment_wrong_assignee(self, mock_get: Mock) -> None:
        """Test verification when wrong person assigned."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fields": {"assignee": {"displayName": "Ahmed Sherbiny"}}
        }
        mock_get.return_value = mock_response

        # Act
        result = verify_assignment(config, "BH-123", "Marwan")

        # Assert
        assert result is False

    @patch("fix_all_assignments.requests.get")
    def test_verify_assignment_unassigned(self, mock_get: Mock) -> None:
        """Test verification when ticket unassigned."""
        # Arrange
        config = {
            "base_url": "https://test.atlassian.net",
            "username": "test@test.com",
            "token": "test-token",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"fields": {"assignee": None}}
        mock_get.return_value = mock_response

        # Act
        result = verify_assignment(config, "BH-123", "Marwan")

        # Assert
        assert result is False
