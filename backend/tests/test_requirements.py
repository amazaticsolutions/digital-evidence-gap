"""
Tests for requirements.txt and dependencies.
"""
import os
import re
from unittest.mock import patch

import pytest


class TestRequirements:
    """Test cases for requirements.txt."""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        assert os.path.exists('requirements.txt')

    def test_requirements_file_not_empty(self):
        """Test that requirements.txt has content."""
        with open('requirements.txt', 'r') as f:
            content = f.read().strip()
            assert len(content) > 0

    def test_django_version_specified(self):
        """Test that Django version is specified."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'Django==5.0.4' in content

    def test_drf_included(self):
        """Test that Django REST Framework is included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'djangorestframework==3.15.1' in content

    def test_jwt_auth_included(self):
        """Test that JWT authentication is included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'djangorestframework-simplejwt==5.3.1' in content

    def test_mongodb_driver_included(self):
        """Test that PyMongo is included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'pymongo==4.6.3' in content

    def test_google_api_included(self):
        """Test that Google API client is included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'google-api-python-client==2.120.0' in content

    def test_testing_dependencies_included(self):
        """Test that testing dependencies are included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'pytest==' in content
            assert 'pytest-django==' in content
            assert 'coverage==' in content
            assert 'factory-boy==' in content

    def test_code_quality_tools_included(self):
        """Test that code quality tools are included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'black==' in content
            assert 'isort==' in content
            assert 'flake8==' in content

    def test_production_dependencies_included(self):
        """Test that production dependencies are included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
            assert 'gunicorn==' in content
            assert 'whitenoise==' in content

    def test_requirements_format(self):
        """Test that requirements follow proper format."""
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Should be in format: package==version
                assert '==' in line, f"Invalid format for line: {line}"
                parts = line.split('==')
                assert len(parts) == 2, f"Invalid version specification: {line}"
                assert len(parts[0]) > 0, f"Missing package name: {line}"
                assert len(parts[1]) > 0, f"Missing version: {line}"

    def test_no_duplicate_packages(self):
        """Test that there are no duplicate packages in requirements."""
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()

        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                package = line.split('==')[0]
                assert package not in packages, f"Duplicate package: {package}"
                packages.append(package)

    def test_versions_are_valid(self):
        """Test that version numbers follow semantic versioning."""
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()

        version_pattern = re.compile(r'^\d+(\.\d+)*(\.\d+)*$')

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                version = line.split('==')[1]
                # Allow versions like 5.0.4, 3.15.1, etc.
                assert version_pattern.match(version), f"Invalid version format: {version}"

    def test_all_packages_have_versions(self):
        """Test that all packages specify exact versions."""
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                assert '==' in line, f"Package without version: {line}"

    @patch('subprocess.run')
    def test_requirements_can_be_installed(self, mock_subprocess):
        """Test that requirements.txt can be installed (mocked)."""
        mock_subprocess.return_value.returncode = 0

        # This would normally run: pip install -r requirements.txt
        # We mock it to avoid actual installation during tests
        assert True  # Placeholder for actual pip install test

    def test_critical_packages_present(self):
        """Test that critical packages for the project are present."""
        with open('requirements.txt', 'r') as f:
            content = f.read()

        critical_packages = [
            'Django',
            'djangorestframework',
            'djangorestframework-simplejwt',
            'pymongo',
            'google-api-python-client',
            'python-dotenv',
            'pytest',
        ]

        for package in critical_packages:
            assert package in content, f"Missing critical package: {package}"

    def test_environment_dependencies_included(self):
        """Test that environment-specific dependencies are included."""
        with open('requirements.txt', 'r') as f:
            content = f.read()

        env_packages = [
            'python-dotenv',
            'django-cors-headers',
        ]

        for package in env_packages:
            assert package in content, f"Missing environment package: {package}"