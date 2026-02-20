"""Low-level Jira REST API client.

Pure functional HTTP client with explicit error handling.
"""

from typing import Any

import requests

from .jira_config import JiraConfig
from .jira_models import JiraError

# Type aliases for clarity
Result = tuple[dict[str, Any] | None, JiraError | None]
ListResult = tuple[list[dict[str, Any]] | None, JiraError | None]


def _make_request(
    method: str,
    url: str,
    config: JiraConfig,
    json_payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = 10,
) -> Result:
    """Make HTTP request to Jira API with error handling.

    Pure function that returns result tuple instead of raising exceptions.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Full URL to request
        config: Jira configuration
        json_payload: JSON payload for request body
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_data, error). One will be None.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            auth=config.auth,
            headers=headers,
            json=json_payload,
            params=params,
            timeout=timeout,
        )

        if response.status_code in (200, 201, 204):
            if response.status_code == 204:
                return ({}, None)
            return (response.json(), None)

        error_data = None
        try:
            error_data = response.json()
        except Exception:
            pass

        error = JiraError(
            status_code=response.status_code,
            message=response.text[:200],
            errors=error_data,
        )
        return (None, error)

    except requests.RequestException as e:
        error = JiraError(
            status_code=0,
            message=f"Request failed: {str(e)[:200]}",
        )
        return (None, error)


def get(
    config: JiraConfig,
    endpoint: str,
    params: dict[str, Any] | None = None,
    timeout: int = 10,
) -> Result:
    """Execute GET request to Jira API.

    Args:
        config: Jira configuration
        endpoint: API endpoint (e.g., /rest/api/3/issue/BH-123)
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_data, error)
    """
    url = f"{config.base_url}{endpoint}"
    return _make_request("GET", url, config, params=params, timeout=timeout)


def post(
    config: JiraConfig,
    endpoint: str,
    payload: dict[str, Any],
    timeout: int = 10,
) -> Result:
    """Execute POST request to Jira API.

    Args:
        config: Jira configuration
        endpoint: API endpoint
        payload: JSON payload
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_data, error)
    """
    url = f"{config.base_url}{endpoint}"
    return _make_request("POST", url, config, json_payload=payload, timeout=timeout)


def put(
    config: JiraConfig,
    endpoint: str,
    payload: dict[str, Any],
    timeout: int = 10,
) -> Result:
    """Execute PUT request to Jira API.

    Args:
        config: Jira configuration
        endpoint: API endpoint
        payload: JSON payload
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_data, error)
    """
    url = f"{config.base_url}{endpoint}"
    return _make_request("PUT", url, config, json_payload=payload, timeout=timeout)


def delete(
    config: JiraConfig,
    endpoint: str,
    timeout: int = 10,
) -> Result:
    """Execute DELETE request to Jira API.

    Args:
        config: Jira configuration
        endpoint: API endpoint
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_data, error)
    """
    url = f"{config.base_url}{endpoint}"
    return _make_request("DELETE", url, config, timeout=timeout)


def search_jql(
    config: JiraConfig,
    jql: str,
    fields: list[str] | None = None,
    max_results: int = 100,
    start_at: int = 0,
) -> ListResult:
    """Search issues using JQL.

    Args:
        config: Jira configuration
        jql: JQL query string
        fields: List of fields to return (None for default)
        max_results: Maximum number of results
        start_at: Pagination offset

    Returns:
        Tuple of (list of issues, error)
    """
    default_fields = [
        "summary",
        "status",
        "description",
        "created",
        "updated",
        "priority",
        "assignee",
        "issuetype",
        "labels",
        "parent",
    ]

    payload = {
        "jql": jql,
        "fields": fields or default_fields,
        "maxResults": max_results,
        "startAt": start_at,
    }

    data, error = post(config, "/rest/api/3/search/jql", payload)

    if error:
        return (None, error)

    if data and "issues" in data:
        return (data["issues"], None)

    return ([], None)
