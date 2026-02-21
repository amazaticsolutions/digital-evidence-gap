"""Search app configuration."""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'search'
    verbose_name = 'Search'