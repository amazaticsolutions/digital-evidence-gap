"""
Tests for core middleware.
"""
import json
import logging
import time
from unittest.mock import Mock, patch

import pytest
from django.http import JsonResponse
from django.test import RequestFactory
from rest_framework import status

from core.middleware import ExceptionHandlingMiddleware, RequestLoggingMiddleware


class TestRequestLoggingMiddleware:
    """Test cases for RequestLoggingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return RequestLoggingMiddleware()

    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()

    @patch('core.middleware.logger')
    def test_process_request_logs_request(self, mock_logger, middleware, request_factory):
        """Test that process_request logs the incoming request."""
        request = request_factory.get('/api/test/')

        result = middleware.process_request(request)

        # Should return None
        assert result is None

        # Should log the request
        mock_logger.info.assert_called_once_with("Request: GET /api/test/")

        # Should set start_time on request
        assert hasattr(request, 'start_time')
        assert isinstance(request.start_time, float)

    @patch('core.middleware.logger')
    @patch('core.middleware.time.time')
    def test_process_response_logs_response_with_duration(self, mock_time, mock_logger, middleware, request_factory):
        """Test that process_response logs response with duration."""
        # Mock time values
        mock_time.return_value = 100.5
        request = request_factory.get('/api/test/')
        request.start_time = 100.0  # Set start time

        response = JsonResponse({'test': 'data'})
        response.status_code = 200

        result = middleware.process_response(request, response)

        # Should return the response
        assert result == response

        # Should log with duration
        expected_log = "Response: GET /api/test/ [200] 0.500s"
        mock_logger.info.assert_called_once_with(expected_log)

    @patch('core.middleware.logger')
    def test_process_response_without_start_time(self, mock_logger, middleware, request_factory):
        """Test that process_response handles requests without start_time."""
        request = request_factory.get('/api/test/')
        # Don't set start_time

        response = JsonResponse({'test': 'data'})

        result = middleware.process_response(request, response)

        # Should return the response
        assert result == response

        # Should not log anything
        mock_logger.info.assert_not_called()

    @patch('core.middleware.logger')
    @patch('core.middleware.time.time')
    def test_process_response_with_different_methods_and_paths(self, mock_time, mock_logger, middleware, request_factory):
        """Test logging with different HTTP methods and paths."""
        mock_time.return_value = 200.0

        test_cases = [
            ('GET', '/api/users/', 'Request: GET /api/users/'),
            ('POST', '/api/evidence/upload/', 'Request: POST /api/evidence/upload/'),
            ('PUT', '/api/search/123/', 'Request: PUT /api/search/123/'),
            ('DELETE', '/api/users/456/', 'Request: DELETE /api/users/456/'),
        ]

        for method, path, expected_log in test_cases:
            mock_logger.reset_mock()

            if method == 'GET':
                request = request_factory.get(path)
            elif method == 'POST':
                request = request_factory.post(path)
            elif method == 'PUT':
                request = request_factory.put(path)
            elif method == 'DELETE':
                request = request_factory.delete(path)

            middleware.process_request(request)

            mock_logger.info.assert_called_with(expected_log)


class TestExceptionHandlingMiddleware:
    """Test cases for ExceptionHandlingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return ExceptionHandlingMiddleware()

    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()

    @patch('core.middleware.logger')
    def test_process_exception_returns_json_response(self, mock_logger, middleware, request_factory):
        """Test that process_exception returns proper JSON response."""
        request = request_factory.get('/api/test/')
        exception = ValueError("Test error")

        response = middleware.process_exception(request, exception)

        # Should return JsonResponse
        assert isinstance(response, JsonResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Check response content
        content = json.loads(response.content.decode('utf-8'))
        assert content['error'] == 'Internal server error'
        assert content['message'] == 'Something went wrong. Please try again later.'
        assert content['status_code'] == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('core.middleware.logger')
    def test_process_exception_logs_error(self, mock_logger, middleware, request_factory):
        """Test that process_exception logs the exception."""
        request = request_factory.get('/api/test/')
        exception = RuntimeError("Database connection failed")

        middleware.process_exception(request, exception)

        # Should log the error with exception info
        mock_logger.error.assert_called_once_with(
            "Unhandled exception: Database connection failed",
            exc_info=True
        )

    @patch('core.middleware.logger')
    def test_process_exception_handles_different_exception_types(self, mock_logger, middleware, request_factory):
        """Test that middleware handles different types of exceptions."""
        request = request_factory.get('/api/test/')

        test_exceptions = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            TypeError("Wrong type"),
            AttributeError("Missing attribute"),
            ImportError("Import failed"),
        ]

        for exception in test_exceptions:
            mock_logger.reset_mock()

            response = middleware.process_exception(request, exception)

            # Should always return 500 status
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            # Should log the exception
            mock_logger.error.assert_called_with(
                f"Unhandled exception: {str(exception)}",
                exc_info=True
            )

    @patch('core.middleware.logger')
    def test_process_exception_with_custom_exception_messages(self, mock_logger, middleware, request_factory):
        """Test exception handling with various error messages."""
        request = request_factory.get('/api/test/')

        test_cases = [
            ("Network timeout", "Network timeout"),
            ("Permission denied", "Permission denied"),
            ("File not found: /path/to/file", "File not found: /path/to/file"),
            ("", ""),  # Empty message
        ]

        for exception_msg, expected_log_msg in test_cases:
            mock_logger.reset_mock()

            exception = Exception(exception_msg)
            response = middleware.process_exception(request, exception)

            # Should return proper response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            # Should log with correct message
            mock_logger.error.assert_called_with(
                f"Unhandled exception: {expected_log_msg}",
                exc_info=True
            )

    def test_process_exception_response_content_type(self, middleware, request_factory):
        """Test that response has correct content type."""
        request = request_factory.get('/api/test/')
        exception = Exception("Test")

        response = middleware.process_exception(request, exception)

        # Should have JSON content type
        assert response['Content-Type'] == 'application/json'

    @patch('core.middleware.logger')
    def test_process_exception_preserves_request_path_in_logging(self, mock_logger, middleware):
        """Test that exception logging works regardless of request path."""
        test_paths = [
            '/api/users/',
            '/api/evidence/upload/',
            '/admin/',
            '/api/search/history/',
        ]

        for path in test_paths:
            request = RequestFactory().get(path)
            exception = Exception("Test error")

            middleware.process_exception(request, exception)

            # Should log the exception
            assert mock_logger.error.called
            mock_logger.reset_mock()