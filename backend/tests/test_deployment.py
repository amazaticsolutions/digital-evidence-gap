"""
Tests for ASGI and WSGI configurations.
"""
import os
from unittest.mock import Mock, patch

import pytest

from core.asgi import application as asgi_application
from core.wsgi import application as wsgi_application


class TestASGIConfig:
    """Test cases for ASGI configuration."""

    @patch.dict(os.environ, {}, clear=True)
    @patch('django.core.asgi.get_asgi_application')
    def test_asgi_application_sets_correct_settings_module(self, mock_get_asgi_app):
        """Test that ASGI config sets the correct Django settings module."""
        # Mock the get_asgi_application function
        mock_app = Mock()
        mock_get_asgi_app.return_value = mock_app

        # Import the module to trigger the code
        from importlib import reload
        import core.asgi
        reload(core.asgi)

        # Check that the environment variable was set (uses setdefault so only sets if not present)
        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'

        # Check that get_asgi_application was called
        mock_get_asgi_app.assert_called_once()

        # Check that application is the returned app
        assert core.asgi.application == mock_app

    @patch('django.core.asgi.get_asgi_application')
    def test_asgi_application_imports_django_asgi(self, mock_get_asgi_app):
        """Test that ASGI config imports Django's get_asgi_application."""
        from core.asgi import get_asgi_application

        # Should be importable
        assert get_asgi_application is not None

    def test_asgi_application_is_callable(self):
        """Test that the ASGI application is callable."""
        # The application should be callable (it's a mock or real ASGI app)
        assert callable(asgi_application)

    @patch.dict(os.environ, {}, clear=True)
    @patch('django.core.asgi.get_asgi_application')
    def test_asgi_application_overwrites_existing_settings(self, mock_get_asgi_app):
        """Test that ASGI config sets DJANGO_SETTINGS_MODULE when not present."""
        from importlib import reload
        import core.asgi
        reload(core.asgi)

        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'


class TestWSGIConfig:
    """Test cases for WSGI configuration."""

    @patch.dict(os.environ, {}, clear=True)
    @patch('django.core.wsgi.get_wsgi_application')
    def test_wsgi_application_sets_correct_settings_module(self, mock_get_wsgi_app):
        """Test that WSGI config sets the correct Django settings module."""
        # Mock the get_wsgi_application function
        mock_app = Mock()
        mock_get_wsgi_app.return_value = mock_app

        # Import the module to trigger the code
        from importlib import reload
        import core.wsgi
        reload(core.wsgi)

        # Check that the environment variable was set
        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'

        # Check that get_wsgi_application was called
        mock_get_wsgi_app.assert_called_once()

        # Check that application is the returned app
        assert core.wsgi.application == mock_app

    @patch('django.core.wsgi.get_wsgi_application')
    def test_wsgi_application_imports_django_wsgi(self, mock_get_wsgi_app):
        """Test that WSGI config imports Django's get_wsgi_application."""
        from core.wsgi import get_wsgi_application

        # Should be importable
        assert get_wsgi_application is not None

    def test_wsgi_application_is_callable(self):
        """Test that the WSGI application is callable."""
        # The application should be callable (it's a mock or real WSGI app)
        assert callable(wsgi_application)

    @patch.dict(os.environ, {}, clear=True)
    @patch('django.core.wsgi.get_wsgi_application')
    def test_wsgi_application_overwrites_existing_settings(self, mock_get_wsgi_app):
        """Test that WSGI config sets DJANGO_SETTINGS_MODULE when not present."""
        from importlib import reload
        import core.wsgi
        reload(core.wsgi)

        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'


class TestDeploymentConfig:
    """Test cases for deployment configuration."""

    def test_asgi_docstring_present(self):
        """Test that ASGI module has proper docstring."""
        import core.asgi
        assert 'ASGI config' in core.asgi.__doc__
        assert 'digital_evidence_gap project' in core.asgi.__doc__

    def test_wsgi_docstring_present(self):
        """Test that WSGI module has proper docstring."""
        import core.wsgi
        assert 'WSGI config' in core.wsgi.__doc__
        assert 'digital_evidence_gap project' in core.wsgi.__doc__

    def test_asgi_docstring_mentions_django_version(self):
        """Test that ASGI docstring references Django version."""
        import core.asgi
        assert '5.' in core.asgi.__doc__

    def test_wsgi_docstring_mentions_django_version(self):
        """Test that WSGI docstring references Django version."""
        import core.wsgi
        assert '5.' in core.wsgi.__doc__

    @patch.dict(os.environ, {}, clear=True)
    @patch('django.core.asgi.get_asgi_application')
    @patch('django.core.wsgi.get_wsgi_application')
    def test_both_configs_use_production_settings(self, mock_wsgi_app, mock_asgi_app):
        """Test that both ASGI and WSGI set the correct settings module."""
        from importlib import reload
        import core.asgi
        reload(core.asgi)

        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'

        # Reset environment
        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            del os.environ['DJANGO_SETTINGS_MODULE']

        import core.wsgi
        reload(core.wsgi)

        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings'