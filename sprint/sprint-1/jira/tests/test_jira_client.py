"""Tests for jira_client module.

Tests for HTTP client with mocked requests.
"""

from unittest.mock import Mock

import pytest
import requests

from jira_lib.jira_client import delete, get, post, put, search_jql
from jira_lib.jira_config import JiraConfig
from jira_lib.jira_models import JiraError


@pytest.fixture
def config() -> JiraConfig:
    """Create test configuration."""
    return JiraConfig(
        base_url="https://test.atlassian.net",
        username="test@example.com",
        token="secret-token",
    )


class TestGet:
    """Tests for GET requests."""

    def test_get_success(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "BH-123", "summary": "Test"}

        mocker.patch("requests.request", return_value=mock_response)

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert error is None
        assert data is not None
        assert data["key"] == "BH-123"
        assert data["summary"] == "Test"

    def test_get_with_params(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"accountId": "123"}]

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        params = {"query": "test@example.com"}
        data, error = get(config, "/rest/api/3/user/search", params=params)

        assert error is None
        assert data is not None
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["params"] == params

    def test_get_404_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Issue not found"
        mock_response.json.side_effect = ValueError("No JSON")

        mocker.patch("requests.request", return_value=mock_response)

        data, error = get(config, "/rest/api/3/issue/BH-999")

        assert data is None
        assert error is not None
        assert isinstance(error, JiraError)
        assert error.status_code == 404
        assert "not found" in error.message.lower()

    def test_get_401_error_with_json(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with 401 and JSON error details."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {"errorMessages": ["Invalid credentials"]}

        mocker.patch("requests.request", return_value=mock_response)

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert data is None
        assert error is not None
        assert error.status_code == 401
        assert error.errors is not None
        assert "errorMessages" in error.errors

    def test_get_network_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with network/connection error."""
        mocker.patch(
            "requests.request",
            side_effect=requests.ConnectionError("Connection refused"),
        )

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert data is None
        assert error is not None
        assert isinstance(error, JiraError)
        assert error.status_code == 0
        assert "Connection refused" in error.message

    def test_get_timeout_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with timeout."""
        mocker.patch(
            "requests.request",
            side_effect=requests.Timeout("Request timeout"),
        )

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert data is None
        assert error is not None
        assert error.status_code == 0
        assert "timeout" in error.message.lower()

    def test_get_custom_timeout(self, config: JiraConfig, mocker: Mock) -> None:
        """Test GET request with custom timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        get(config, "/rest/api/3/issue/BH-123", timeout=30)

        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["timeout"] == 30


class TestPost:
    """Tests for POST requests."""

    def test_post_success_201(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful POST request with 201 Created."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "12345", "key": "BH-200"}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        payload = {"summary": "New task", "project": {"key": "BH"}}
        data, error = post(config, "/rest/api/3/issue", payload)

        assert error is None
        assert data is not None
        assert data["key"] == "BH-200"
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["json"] == payload
        assert call_kwargs["method"] == "POST"

    def test_post_success_200(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful POST request with 200 OK."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": []}

        mocker.patch("requests.request", return_value=mock_response)

        payload = {"jql": "project = BH"}
        data, error = post(config, "/rest/api/3/search", payload)

        assert error is None
        assert data is not None

    def test_post_400_validation_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test POST request with 400 validation error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Validation failed"
        mock_response.json.return_value = {
            "errors": {"summary": "Summary is required"},
        }

        mocker.patch("requests.request", return_value=mock_response)

        payload = {"project": {"key": "BH"}}
        data, error = post(config, "/rest/api/3/issue", payload)

        assert data is None
        assert error is not None
        assert error.status_code == 400
        assert error.errors is not None
        assert "summary" in error.errors["errors"]


class TestPut:
    """Tests for PUT requests."""

    def test_put_success_204(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful PUT request with 204 No Content."""
        mock_response = Mock()
        mock_response.status_code = 204

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        payload = {"accountId": "5b10ac8d82e05b22cc7d4ef5"}
        data, error = put(config, "/rest/api/3/issue/BH-150/assignee", payload)

        assert error is None
        assert data == {}  # 204 returns empty dict
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["json"] == payload

    def test_put_success_200(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful PUT request with 200 OK."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "updated": True}

        mocker.patch("requests.request", return_value=mock_response)

        payload = {"name": "Updated Sprint"}
        data, error = put(config, "/rest/agile/1.0/sprint/123", payload)

        assert error is None
        assert data is not None
        assert data["updated"] is True

    def test_put_403_forbidden(self, config: JiraConfig, mocker: Mock) -> None:
        """Test PUT request with 403 Forbidden."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden: You don't have permission"
        mock_response.json.side_effect = ValueError("No JSON")

        mocker.patch("requests.request", return_value=mock_response)

        payload = {"accountId": "123"}
        data, error = put(config, "/rest/api/3/issue/BH-150/assignee", payload)

        assert data is None
        assert error is not None
        assert error.status_code == 403
        assert "permission" in error.message.lower()


class TestDelete:
    """Tests for DELETE requests."""

    def test_delete_success_204(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        data, error = delete(config, "/rest/api/3/issue/BH-999")

        assert error is None
        assert data == {}
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["method"] == "DELETE"

    def test_delete_404_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test DELETE request with 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Issue not found"
        mock_response.json.side_effect = ValueError("No JSON")

        mocker.patch("requests.request", return_value=mock_response)

        data, error = delete(config, "/rest/api/3/issue/BH-999")

        assert data is None
        assert error is not None
        assert error.status_code == 404


class TestSearchJql:
    """Tests for JQL search."""

    def test_search_jql_success(self, config: JiraConfig, mocker: Mock) -> None:
        """Test successful JQL search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {"key": "BH-150", "fields": {"summary": "Task 1"}},
                {"key": "BH-151", "fields": {"summary": "Task 2"}},
            ],
        }

        mocker.patch("requests.request", return_value=mock_response)

        issues, error = search_jql(config, "project = BH AND status = 'To Do'")

        assert error is None
        assert issues is not None
        assert len(issues) == 2
        assert issues[0]["key"] == "BH-150"
        assert issues[1]["key"] == "BH-151"

    def test_search_jql_custom_fields(self, config: JiraConfig, mocker: Mock) -> None:
        """Test JQL search with custom fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": []}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        custom_fields = ["summary", "assignee"]
        search_jql(config, "project = BH", fields=custom_fields)

        call_kwargs = mock_request.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["fields"] == custom_fields

    def test_search_jql_pagination(self, config: JiraConfig, mocker: Mock) -> None:
        """Test JQL search with pagination parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": []}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        search_jql(config, "project = BH", max_results=50, start_at=100)

        call_kwargs = mock_request.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["maxResults"] == 50
        assert payload["startAt"] == 100

    def test_search_jql_no_results(self, config: JiraConfig, mocker: Mock) -> None:
        """Test JQL search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": []}

        mocker.patch("requests.request", return_value=mock_response)

        issues, error = search_jql(config, "project = NONEXISTENT")

        assert error is None
        assert issues == []

    def test_search_jql_error(self, config: JiraConfig, mocker: Mock) -> None:
        """Test JQL search with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid JQL"
        mock_response.json.return_value = {"errorMessages": ["Invalid JQL syntax"]}

        mocker.patch("requests.request", return_value=mock_response)

        issues, error = search_jql(config, "invalid jql syntax")

        assert issues is None
        assert error is not None
        assert error.status_code == 400


class TestRequestAuthentication:
    """Tests for authentication in requests."""

    def test_request_uses_config_auth(self, config: JiraConfig, mocker: Mock) -> None:
        """Test that requests use config authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        get(config, "/rest/api/3/issue/BH-123")

        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["auth"] == ("test@example.com", "secret-token")

    def test_request_has_correct_headers(self, config: JiraConfig, mocker: Mock) -> None:
        """Test that requests have correct headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_request = mocker.patch("requests.request", return_value=mock_response)

        get(config, "/rest/api/3/issue/BH-123")

        call_kwargs = mock_request.call_args.kwargs
        headers = call_kwargs["headers"]
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_long_error_message_truncated(self, config: JiraConfig, mocker: Mock) -> None:
        """Test that long error messages are truncated."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "A" * 300  # Long error message
        mock_response.json.side_effect = ValueError("No JSON")

        mocker.patch("requests.request", return_value=mock_response)

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert error is not None
        assert len(error.message) <= 200

    def test_json_decode_error_handled(self, config: JiraConfig, mocker: Mock) -> None:
        """Test that JSON decode errors are handled gracefully."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid response"
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mocker.patch("requests.request", return_value=mock_response)

        data, error = get(config, "/rest/api/3/issue/BH-123")

        assert data is None
        assert error is not None
        assert error.errors is None  # Should be None when JSON parsing fails
