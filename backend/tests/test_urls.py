"""
Tests for core URL configuration.
"""
from django.test import TestCase
from django.urls import resolve, reverse
from django.conf import settings


class TestCoreURLs(TestCase):
    """Test cases for core URL configuration."""

    def test_admin_url_resolves(self):
        """Test that admin URL resolves correctly."""
        resolver = resolve('/admin/')
        self.assertEqual(resolver.url_name, 'index')
        self.assertEqual(resolver.namespace, 'admin')

    def test_users_api_url_included(self):
        """Test that users API URLs are included."""
        # This would require the users.urls to be implemented
        # For now, just test that the pattern exists
        from django.urls import path, include
        from core.urls import urlpatterns

        # Check that users URL pattern exists
        users_pattern = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'pattern') and str(pattern.pattern) == 'api/users/':
                users_pattern = pattern
                break

        self.assertIsNotNone(users_pattern)
        self.assertEqual(str(users_pattern.pattern), 'api/users/')

    def test_evidence_api_url_included(self):
        """Test that evidence API URLs are included."""
        from core.urls import urlpatterns

        evidence_pattern = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'pattern') and str(pattern.pattern) == 'api/evidence/':
                evidence_pattern = pattern
                break

        self.assertIsNotNone(evidence_pattern)
        self.assertEqual(str(evidence_pattern.pattern), 'api/evidence/')

    def test_search_api_url_included(self):
        """Test that search API URLs are included."""
        from core.urls import urlpatterns

        search_pattern = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'pattern') and str(pattern.pattern) == 'api/search/':
                search_pattern = pattern
                break

        self.assertIsNotNone(search_pattern)
        self.assertEqual(str(search_pattern.pattern), 'api/search/')

    def test_static_files_served_in_debug(self):
        """Test that static files are served in debug mode."""
        from django.conf.urls.static import static
        from core.urls import urlpatterns

        # Check if DEBUG is True
        if settings.DEBUG:
            # Should have static URL patterns
            static_patterns = [p for p in urlpatterns if 'static' in str(p.pattern)]
            self.assertTrue(len(static_patterns) > 0)

    def test_no_static_files_in_production(self):
        """Test that static files are not served in production."""
        from core.urls import urlpatterns

        # Temporarily set DEBUG to False
        original_debug = settings.DEBUG
        settings.DEBUG = False

        try:
            # Reload URLs to test production configuration
            from importlib import reload
            import core.urls
            reload(core.urls)

            # In production, static files should not be in urlpatterns
            # (they would be served by web server)
            static_patterns = [p for p in core.urls.urlpatterns if 'static' in str(p.pattern)]
            self.assertEqual(len(static_patterns), 0)
        finally:
            settings.DEBUG = original_debug

    def test_urlpatterns_structure(self):
        """Test the overall structure of URL patterns."""
        from core.urls import urlpatterns

        # Should have at least admin and API patterns
        self.assertGreaterEqual(len(urlpatterns), 4)  # admin + 3 API includes

        # Check that all patterns are valid Django URL patterns
        for pattern in urlpatterns:
            self.assertTrue(hasattr(pattern, 'pattern') or hasattr(pattern, 'regex'))

    def test_url_pattern_names(self):
        """Test that URL patterns have appropriate names where applicable."""
        from core.urls import urlpatterns

        # Admin pattern should be resolvable
        try:
            reverse('admin:index')
        except Exception as e:
            self.fail(f"Admin URL reversal failed: {e}")

    def test_include_patterns_use_correct_app_names(self):
        """Test that include patterns reference correct app names."""
        from core.urls import urlpatterns

        expected_apps = ['apps.users.urls', 'apps.evidence.urls', 'apps.search.urls']

        for pattern in urlpatterns:
            if hasattr(pattern, 'urlconf_module'):
                # This is an include pattern
                if pattern.urlconf_module in expected_apps:
                    expected_apps.remove(pattern.urlconf_module)

        # All expected apps should have been found
        self.assertEqual(len(expected_apps), 0, f"Missing URL includes for: {expected_apps}")